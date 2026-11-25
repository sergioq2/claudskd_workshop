# /// script
# requires-python = ">=3.10"
# dependencies = ["anthropic>=2.13", "python-dotenv>=1.0"]
# ///
"""
Prueba el agente en Claude Managed Agents (beta), SIN desplegar ningún servidor MCP.

El agente corre en un sandbox en la nube de Anthropic y consulta datos.gov.co
directamente con curl, en vez de usar el MCP de datos_colombia.py. El sandbox solo
puede salir a internet hacia datos.gov.co. Los archivos que entrega el agente se
descargan al final en salidas/managed/<id de la sesión>/.

Uso:
    uv run correr_managed.py                     # misión de prueba: Saber 11 en Envigado
    uv run correr_managed.py "tu objetivo"       # misión libre
    uv run correr_managed.py mi_mision.md        # una misión escrita en un archivo Markdown
    uv run correr_managed.py aire_antioquia      # atajo: busca mision_aire_antioquia.md
    uv run correr_managed.py --recrear           # vuelve a crear el agente y el entorno

Requisito: ANTHROPIC_API_KEY en .env. uv instala solo lo que este script necesita
(con pip: pip install anthropic python-dotenv).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import anthropic

CARPETA_PROYECTO = Path(__file__).resolve().parent
ARCHIVO_IDS = CARPETA_PROYECTO / ".managed.json"  # guarda los IDs para no recrear todo cada vez
BETA = "managed-agents-2026-04-01"
MODELO = os.environ.get("MODELO_CLAUDE") or "claude-sonnet-5-5"
PRESUPUESTO_USD = float(os.environ.get("PRESUPUESTO_USD", "2"))

# --------------------------------------------------------------------------- #
# 1. El agente: modelo + instrucciones + herramientas
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """Eres un agente analista de datos abiertos de Colombia. Trabajas de forma \
autónoma hasta completar la misión y entregas resultados concretos (archivos), no solo respuestas. \
Escribe siempre en español de Colombia, tanto tus mensajes como los informes.

Cómo consultar datos.gov.co: usa bash con curl. Tu sandbox solo puede salir a internet hacia \
datos.gov.co. Usa curl -sG con --data-urlencode para que los espacios y comillas viajen bien, y \
escapa el $ de los parámetros SoQL dentro de comillas dobles.
- Buscar datasets: https://api.us.socrata.com/api/catalog/v1 con domains=www.datos.gov.co, \
search_context=www.datos.gov.co, q=<términos> y limit=10. Prefiere resultados con resource.type "dataset".
- Describir un dataset: https://www.datos.gov.co/api/views/<id>.json (en "columns" están \
fieldName y dataTypeName) y unas filas de ejemplo con https://www.datos.gov.co/resource/<id>.json?$limit=3
- Consultar con SoQL, por ejemplo:
  curl -sG "https://www.datos.gov.co/resource/<id>.json" --data-urlencode "\\$select=col, count(*) AS n" \
--data-urlencode "\\$where=upper(ciudad) like '%MEDELL%'" --data-urlencode "\\$group=col" \
--data-urlencode "\\$order=n DESC" --data-urlencode "\\$limit=100"
- Exportar a CSV: la misma consulta contra /resource/<id>.csv, guardando con -o en /mnt/session/outputs/.
- Si la misión menciona las herramientas buscar_datasets, describir_dataset, consultar_dataset o \
exportar_csv, haz lo equivalente con curl como se explica arriba.
- Guarda las respuestas grandes en /tmp y procésalas con python3; no imprimas miles de filas.

Datasets de confianza. El usuario no tiene por qué saber IDs: escoge tú el dataset. Empieza por \
esta lista; si la pregunta no encaja, busca en el catálogo y verifica que el dataset tenga datos \
recientes (rowsUpdatedAt en /api/views/<id>.json). Al empezar, di en una línea qué dataset vas a \
usar y por qué.
- TRM diaria (precio oficial del dólar): 32sa-8pi3. Columnas valor y vigenciadesde.
- SECOP II, contratos firmados: jbjy-vk9h. Procesos de contratación (licitaciones): p6dx-8zbt.
- Registro mercantil RUES (empresas, fecha de matrícula, actividad CIIU): c82u-588k.
- Saber 11 por estudiante, 2010 a 2022: kgxf-xxbe. Todas sus columnas son texto (usa \
punt_global::number), el periodo se escribe así: '20224'. Revisa duplicados (el periodo 20224 trae \
cada registro dos veces): deduplica por estu_consecutivo.
- Calidad del aire IDEAM: resumen anual por estación kekd-7v7h; mediciones horarias g4t8-zkc3 \
(es enorme: filtra siempre por estación o municipio y por fechas).

Reglas:
- Antes de consultar un dataset, descríbelo para conocer los nombres exactos de las columnas \
y sus tipos. Nunca adivines nombres de columnas.
- Agrega en el servidor (select + group con count(*), sum(), avg(), min(), max()) en lugar de \
traer miles de filas.
- Los textos distinguen mayúsculas y tildes: filtra con upper(columna) like '%TEXTO%' o explora \
primero los valores distintos con group.
- Antes de filtrar por fechas, mira su formato en las filas de ejemplo ('2026-01-01T00:00:00' si \
es fecha, '2026-01-01 00:00:00' si es texto). Un número guardado como texto se convierte con \
columna::number.
- Si una consulta falla, lee el error, corrígela y reintenta (máximo 3 intentos).
- No inventes cifras: todo número del informe debe salir de una consulta. Si algo no se puede \
calcular, dilo.
- Señala los valores atípicos como "a revisar", nunca como prueba de una irregularidad.
- Si después de reintentar no logras obtener datos, no escribas un informe vacío: explica qué \
falló y detente.

Entregables:
- Escribe todo lo que entregas en /mnt/session/outputs/: es la única carpeta que recibe el \
usuario. Donde la misión diga salidas/, usa /mnt/session/outputs/.
- El informe va en Markdown, con resumen ejecutivo (3 a 5 líneas), cifras clave, hallazgos y una \
sección "Fuente y metodología" con el nombre y el ID del dataset, el enlace \
https://www.datos.gov.co/d/<id>, la fecha de consulta y las limitaciones.
- Escribe los valores en pesos con punto como separador de miles (ej. $1.250.000.000).
- Al terminar, responde con un resumen breve de lo que encontraste y la lista de archivos creados."""

HERRAMIENTAS = [
    {
        "type": "agent_toolset_20260401",
        "default_config": {"enabled": False},  # todo apagado...
        "configs": [  # ...y prendemos solo lo necesario (sin búsqueda web)
            {"name": "bash", "enabled": True},
            {"name": "read", "enabled": True},
            {"name": "write", "enabled": True},
            {"name": "edit", "enabled": True},
        ],
    }
]

# --------------------------------------------------------------------------- #
# 2. El entorno: dónde corre (un sandbox que solo puede hablar con datos.gov.co)
# --------------------------------------------------------------------------- #

CONFIG_ENTORNO = {
    "type": "cloud",
    "networking": {
        "type": "limited",
        "allowed_hosts": ["www.datos.gov.co", "datos.gov.co", "api.us.socrata.com"],
    },
}

# --------------------------------------------------------------------------- #
# Misiones
# --------------------------------------------------------------------------- #

MISION_DE_PRUEBA = (
    "Hazme un ranking de los colegios de Envigado en las pruebas Saber 11 más recientes que haya. "
    "Quiero ver cuántos estudiantes presentó cada colegio, sin meter en el ranking principal a los "
    "que tengan menos de 10, y cómo les fue a los oficiales frente a los privados."
)


def elegir_mision(argumentos: list[str]) -> tuple[str, str]:
    if not argumentos:
        return "Saber 11 en Envigado (prueba)", MISION_DE_PRUEBA
    if len(argumentos) == 1:
        # Un archivo .md, o un atajo: "aire_antioquia" busca mision_aire_antioquia.md
        nombre = argumentos[0]
        ruta = Path(nombre) if nombre.lower().endswith(".md") else CARPETA_PROYECTO / f"mision_{nombre}.md"
        if nombre.lower().endswith(".md") and not ruta.is_file():
            print(f"No encuentro el archivo {ruta}.")
            sys.exit(1)
        if ruta.is_file():
            texto = ruta.read_text(encoding="utf-8").strip()
            titulo = next((l.lstrip("# ").strip() for l in texto.splitlines() if l.startswith("# ")), ruta.stem)
            return titulo, texto
    objetivo = " ".join(argumentos)
    return "Misión libre", (
        f"{objetivo}\n\nEncuentra los datos necesarios en datos.gov.co, analízalos y entrega un "
        "informe en /mnt/session/outputs/ con los datos de soporte en CSV."
    )


# --------------------------------------------------------------------------- #
# Crear (una sola vez) el agente y el entorno
# --------------------------------------------------------------------------- #


def huella_config() -> str:
    texto = json.dumps([MODELO, SYSTEM_PROMPT, HERRAMIENTAS, CONFIG_ENTORNO], sort_keys=True)
    return hashlib.sha256(texto.encode()).hexdigest()[:16]


def preparar_agente_y_entorno(cliente: anthropic.Anthropic, recrear: bool) -> tuple[str, str]:
    guardado = {}
    if ARCHIVO_IDS.exists() and not recrear:
        guardado = json.loads(ARCHIVO_IDS.read_text(encoding="utf-8"))
    if guardado.get("huella") == huella_config():
        return guardado["agent_id"], guardado["environment_id"]

    if guardado:
        print("Cambió la configuración: creo un agente y un entorno nuevos.")
    agente = cliente.beta.agents.create(
        name="Analista de datos abiertos de Colombia",
        model=MODELO,
        system=SYSTEM_PROMPT,
        tools=HERRAMIENTAS,
    )
    entorno = cliente.beta.environments.create(name="datos-gov-co", config=CONFIG_ENTORNO)
    ARCHIVO_IDS.write_text(
        json.dumps(
            {"agent_id": agente.id, "environment_id": entorno.id, "huella": huella_config()},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Agente creado: {agente.id}\nEntorno creado: {entorno.id}")
    return agente.id, entorno.id


# --------------------------------------------------------------------------- #
# Ver al agente trabajar
# --------------------------------------------------------------------------- #


def resumir(nombre: str, entrada: dict) -> str:
    if nombre == "bash":
        texto = str(entrada.get("command", ""))
    elif "file_path" in entrada:
        texto = str(entrada["file_path"])
    else:
        texto = json.dumps(entrada, ensure_ascii=False)
    texto = " ".join(texto.split())
    return texto if len(texto) <= 200 else texto[:200] + "…"


def seguir_sesion(cliente: anthropic.Anthropic, sesion_id: str, mision: str) -> None:
    with cliente.beta.sessions.events.stream(sesion_id) as eventos:
        # El mensaje se envía después de abrir el stream, para no perder eventos
        cliente.beta.sessions.events.send(
            sesion_id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": mision}]}],
        )
        for evento in eventos:
            if evento.type == "agent.message":
                for bloque in evento.content:
                    if getattr(bloque, "type", "") == "text" and bloque.text.strip():
                        print(f"\n[Claude] {bloque.text.strip()}", flush=True)
            elif evento.type == "agent.tool_use":
                print(f"\n  -> {evento.name}  {resumir(evento.name, evento.input)}", flush=True)
            elif evento.type == "session.error":
                error = evento.error
                print(f"\n  (error: {error.type}: {getattr(error, 'message', '')})", flush=True)
            elif evento.type == "session.status_idle":
                motivo = evento.stop_reason.type
                if motivo == "requires_action":
                    print("\nEl agente está esperando una aprobación; este script no la maneja.")
                elif motivo == "budget_reached":
                    print("\nEl agente llegó al presupuesto. Ajusta PRESUPUESTO_USD en tu .env.")
                elif motivo != "end_turn":
                    print(f"\nLa sesión se detuvo: {motivo}")
                return
            elif evento.type == "session.status_terminated":
                print("\nLa sesión terminó.")
                return


def descargar_entregables(cliente: anthropic.Anthropic, sesion_id: str) -> None:
    carpeta = CARPETA_PROYECTO / "salidas" / "managed" / sesion_id
    archivos = []
    # Los archivos pueden tardar unos segundos en aparecer después de que el agente termina
    for _ in range(6):
        archivos = list(cliente.beta.files.list(scope_id=sesion_id, betas=[BETA]))
        if archivos:
            break
        time.sleep(5)
    if not archivos:
        print("\nEl agente no dejó archivos en /mnt/session/outputs/.")
        return
    carpeta.mkdir(parents=True, exist_ok=True)
    print("\nArchivos entregados:")
    for archivo in archivos:
        destino = carpeta / Path(archivo.filename).name
        cliente.files.download(archivo.id).write_to_file(destino)
        print(f"  - {destino.relative_to(CARPETA_PROYECTO)}  ({archivo.size_bytes / 1024:.1f} KB)")


# --------------------------------------------------------------------------- #
# Programa principal
# --------------------------------------------------------------------------- #


def main() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Falta ANTHROPIC_API_KEY. Créala en https://platform.claude.com y agrégala a tu .env")
        sys.exit(1)

    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    titulo, mision = elegir_mision(argumentos)
    mision += f"\n\nFecha de hoy: {date.today().isoformat()}."

    cliente = anthropic.Anthropic()
    agente_id, entorno_id = preparar_agente_y_entorno(cliente, "--recrear" in sys.argv)

    # 3. La sesión: una corrida del agente, con un tope de gasto (en centavos de dólar)
    sesion = cliente.beta.sessions.create(
        agent=agente_id,
        environment_id=entorno_id,
        title=titulo[:200],
        budget={
            "type": "limit",
            "max_list_cost": {"amount": str(round(PRESUPUESTO_USD * 100)), "currency": "USD"},
        },
    )
    print(f"\n=== {titulo} ===")
    print(f"Sesión {sesion.id} (modelo {MODELO}, tope US${PRESUPUESTO_USD:g}).")
    print("El agente trabaja en la nube de Anthropic. Ctrl+C lo interrumpe.\n")

    inicio = time.time()
    try:
        seguir_sesion(cliente, sesion.id, mision)
    except KeyboardInterrupt:
        # La sesión vive en el servidor: si solo cerramos el script, seguiría trabajando
        cliente.beta.sessions.events.send(sesion.id, events=[{"type": "user.interrupt"}])
        print("\nInterrumpido. Le avisé a la sesión que se detenga.")
    print(f"\n=== Fin: {time.time() - inicio:.0f} s ===")
    descargar_entregables(cliente, sesion.id)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    main()
