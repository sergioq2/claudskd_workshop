"""
Servidor MCP con datos abiertos de Colombia (datos.gov.co).

datos.gov.co corre sobre Socrata: CUALQUIER dataset del portal se consulta igual,
con su ID de 8 caracteres (ej. "jbjy-vk9h") y filtros en SoQL (un SQL simplificado).
Por eso estas pocas herramientas sirven para SECOP, TRM, INVIMA, MinEducación...

Probar el servidor SIN agente y SIN API key (actúas tú como cliente MCP):
    uv run datos_colombia.py                          # tools/list: qué herramientas hay
    uv run datos_colombia.py ver consultar_dataset    # lo que Claude "ve" de una herramienta
    uv run datos_colombia.py buscar_datasets termino="calidad del aire"
    uv run datos_colombia.py describir_dataset dataset_id=jbjy-vk9h
    uv run datos_colombia.py consultar_dataset dataset_id=32sa-8pi3 limit=5 order="vigenciadesde DESC"
    uv run datos_colombia.py exportar_csv dataset_id=32sa-8pi3 nombre_archivo=trm limit=100

Usarlo desde el agente (ver agente.py):
    from datos_colombia import crear_servidor_datos
    ClaudeAgentOptions(mcp_servers={"datos": crear_servidor_datos()}, ...)

Referencia SoQL: https://dev.socrata.com/docs/queries/
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from claude_agent_sdk import ToolAnnotations, create_sdk_mcp_server, tool

# =========================================================================== #
# 1. CONFIGURACIÓN
# =========================================================================== #

DOMINIO = "www.datos.gov.co"
URL_BASE = f"https://{DOMINIO}"
URL_CATALOGO = "https://api.us.socrata.com/api/catalog/v1"  # buscador de datasets
CARPETA_SALIDAS = Path(__file__).resolve().parent / "salidas"

MAX_FILAS = 1_000  # lo máximo que el agente "lee" en una consulta
MAX_FILAS_CSV = 50_000  # lo máximo que se guarda en un CSV
MAX_CARACTERES = 40_000  # para no llenar el contexto del modelo


# =========================================================================== #
# 2. UTILIDADES: cómo responde una herramienta MCP y cómo hablamos con la API
# =========================================================================== #


def ok(datos: Any) -> dict[str, Any]:
    """Respuesta MCP exitosa: una lista de bloques de contenido (aquí, un texto)."""
    texto = datos if isinstance(datos, str) else json.dumps(datos, ensure_ascii=False, indent=1, default=str)
    if len(texto) > MAX_CARACTERES:
        texto = texto[:MAX_CARACTERES] + "\n[... recortado. Trae menos datos con select, group o un limit menor.]"
    return {"content": [{"type": "text", "text": texto}]}


def error(mensaje: str) -> dict[str, Any]:
    """Respuesta MCP de error: is_error le dice al agente que corrija y reintente."""
    return {"content": [{"type": "text", "text": mensaje}], "is_error": True}


class ErrorDatos(Exception):
    """Un problema que el agente puede leer y usar para corregir su siguiente intento."""


async def pedir(url: str, params: dict[str, Any], timeout: float = 60.0) -> httpx.Response:
    """GET a datos.gov.co. Si algo falla, lanza ErrorDatos con un mensaje útil."""
    cabeceras = {"User-Agent": "taller-agentes-datos-colombia/1.0"}
    # Sin token funciona, pero con límites de peticiones muy bajos.
    # Créalo gratis en datos.gov.co > tu perfil > Developer Settings.
    if os.environ.get("SOCRATA_APP_TOKEN"):
        cabeceras["X-App-Token"] = os.environ["SOCRATA_APP_TOKEN"]
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=cabeceras, follow_redirects=True) as cliente:
            respuesta = await cliente.get(url, params=params)
    except httpx.TimeoutException:
        raise ErrorDatos("La consulta tardó demasiado. Agrega filtros en where o agrega con group.")
    except httpx.HTTPError as e:
        raise ErrorDatos(f"No se pudo conectar a datos.gov.co ({type(e).__name__}).")

    if respuesta.status_code != 200:
        try:
            cuerpo = respuesta.json()
            detalle = cuerpo.get("message") if isinstance(cuerpo, dict) else None
        except ValueError:
            detalle = None
        pista = {
            400: "Revisa la sintaxis SoQL y que las columnas existan (usa describir_dataset).",
            404: "El dataset no existe o no es público. Verifica el ID con buscar_datasets.",
            429: "Límite de peticiones alcanzado. Configura SOCRATA_APP_TOKEN en tu .env.",
        }.get(respuesta.status_code, "")
        raise ErrorDatos(
            f"Error HTTP {respuesta.status_code} de datos.gov.co: {detalle or respuesta.text[:500]}\n{pista}".strip()
        )
    return respuesta


def validar_id(valor: Any) -> str:
    did = str(valor or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9]{4}-[a-z0-9]{4}", did):
        raise ErrorDatos("ID inválido. Debe tener la forma 'xxxx-xxxx' (ej. 'jbjy-vk9h').")
    return did


def parametros_soql(args: dict[str, Any], limite_por_defecto: int, limite_maximo: int) -> dict[str, Any]:
    """{'where': 'x > 1', 'limit': 5}  ->  {'$where': 'x > 1', '$limit': 5}"""
    params: dict[str, Any] = {
        f"${clave}": str(args[clave])
        for clave in ("select", "where", "group", "having", "order", "q")
        if args.get(clave) not in (None, "")
    }
    try:
        limite = int(args.get("limit") or limite_por_defecto)
    except (TypeError, ValueError):
        limite = limite_por_defecto
    params["$limit"] = max(1, min(limite, limite_maximo))
    return params


def recortar_textos(fila: dict[str, Any], largo: int = 200) -> dict[str, Any]:
    return {k: (v[:largo] + "…" if isinstance(v, str) and len(v) > largo else v) for k, v in fila.items()}


def nombre_archivo_seguro(nombre: Any) -> str:
    """'Alertas Medellín!' -> 'Alertas_Medellin' (sin tildes, espacios ni rutas)."""
    sin_tildes = unicodedata.normalize("NFKD", str(nombre or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", sin_tildes).strip("_")[:80] or "datos"


# =========================================================================== #
# 3. HERRAMIENTAS
#    Cada una = nombre + descripción (la lee Claude) + esquema de argumentos
#    + una función async que recibe args (dict) y devuelve ok(...) o error(...)
# =========================================================================== #

SOLO_LECTURA = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
ESCRIBE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)


@tool(
    "buscar_datasets",
    "Busca datasets en el catálogo de datos abiertos de Colombia (datos.gov.co) por "
    "palabra clave. Devuelve el ID de 8 caracteres (ej. 'jbjy-vk9h'), nombre, entidad "
    "que lo publica, categoría, fecha de actualización y descripción. Úsala cuando no "
    "sepas qué dataset tiene la información. Escribe los términos en español.",
    {
        "type": "object",
        "properties": {
            "termino": {"type": "string", "description": "Palabras clave, ej. 'accidentes de transito medellin'"},
            "limite": {"type": "integer", "minimum": 1, "maximum": 20, "description": "Máximo de resultados (por defecto 8)"},
        },
        "required": ["termino"],
    },
    annotations=SOLO_LECTURA,
)
async def buscar_datasets(args: dict[str, Any]) -> dict[str, Any]:
    termino = str(args.get("termino") or "").strip()
    if not termino:
        return error("Debes indicar un término de búsqueda.")
    try:
        limite = max(1, min(int(args.get("limite") or 8), 20))
    except (TypeError, ValueError):
        limite = 8

    try:
        respuesta = await pedir(
            URL_CATALOGO,
            {"domains": DOMINIO, "search_context": DOMINIO, "q": termino, "limit": limite * 2},
            timeout=30,
        )
    except ErrorDatos as e:
        return error(str(e))

    items = respuesta.json().get("results", [])
    # Preferimos tablas consultables sobre mapas, gráficos o enlaces externos.
    tablas = [i for i in items if i.get("resource", {}).get("type") == "dataset"] or items
    resultados = [
        {
            "id": i["resource"].get("id"),
            "nombre": i["resource"].get("name"),
            "entidad": i["resource"].get("attribution"),
            "categoria": i.get("classification", {}).get("domain_category"),
            "actualizado": str(i["resource"].get("data_updated_at") or i["resource"].get("updatedAt") or "")[:10],
            "descripcion": (i["resource"].get("description") or "")[:300],
            "url": i.get("permalink") or i.get("link"),
        }
        for i in tablas[:limite]
        if "resource" in i
    ]
    if not resultados:
        return ok(f"No encontré datasets para '{termino}'. Prueba con sinónimos, sin tildes o términos más generales.")
    return ok(resultados)


@tool(
    "describir_dataset",
    "Muestra la estructura de un dataset de datos.gov.co: nombre, entidad, fecha de "
    "última actualización, total de filas, columnas (nombre de campo para usar en SoQL, "
    "tipo y descripción) y 3 filas de ejemplo. Úsala SIEMPRE antes de consultar un "
    "dataset por primera vez, para no adivinar nombres de columnas.",
    {"dataset_id": str},
    annotations=SOLO_LECTURA,
)
async def describir_dataset(args: dict[str, Any]) -> dict[str, Any]:
    try:
        did = validar_id(args.get("dataset_id"))
        meta = (await pedir(f"{URL_BASE}/api/views/{did}.json", {}, timeout=30)).json()
    except ErrorDatos as e:
        return error(str(e))

    ejemplo, total = [], None
    try:  # opcionales: filas de ejemplo y conteo (en datasets enormes el conteo puede tardar)
        ejemplo = (await pedir(f"{URL_BASE}/resource/{did}.json", {"$limit": 3}, timeout=30)).json()
        conteo = (await pedir(f"{URL_BASE}/resource/{did}.json", {"$select": "count(*) AS total"}, timeout=20)).json()
        total = conteo[0].get("total") if conteo else None
    except ErrorDatos:
        pass

    actualizado = meta.get("rowsUpdatedAt")
    if isinstance(actualizado, (int, float)):
        actualizado = datetime.fromtimestamp(actualizado, tz=timezone.utc).date().isoformat()

    return ok(
        {
            "id": did,
            "nombre": meta.get("name"),
            "entidad": meta.get("attribution"),
            "descripcion": (meta.get("description") or "")[:600],
            "ultima_actualizacion": actualizado,
            "total_filas": total,
            "url": f"{URL_BASE}/d/{did}",
            "columnas": [
                {
                    "campo": c.get("fieldName"),
                    "tipo": c.get("dataTypeName"),
                    "nombre": c.get("name"),
                    "descripcion": (c.get("description") or "")[:150],
                }
                for c in meta.get("columns", [])
                if c.get("fieldName") and not str(c["fieldName"]).startswith(":")
            ],
            "filas_de_ejemplo": [recortar_textos(f) for f in ejemplo if isinstance(f, dict)],
        }
    )


ARGUMENTOS_SOQL = {
    "dataset_id": {"type": "string", "description": "ID de 8 caracteres, ej. 'jbjy-vk9h'"},
    "select": {"type": "string", "description": "Columnas o agregaciones, ej. 'nombre_entidad, count(*) AS n, sum(valor_del_contrato) AS total'"},
    "where": {"type": "string", "description": "Filtro, ej. \"fecha_de_firma >= '2026-01-01T00:00:00' AND upper(ciudad) like '%MEDELL%'\""},
    "group": {"type": "string", "description": "Agrupar por, ej. 'nombre_entidad'"},
    "having": {"type": "string", "description": "Filtro sobre agregados, ej. 'count(*) > 5'"},
    "order": {"type": "string", "description": "Orden, ej. 'total DESC'"},
    "q": {"type": "string", "description": "Búsqueda de texto libre en todas las columnas"},
}


@tool(
    "consultar_dataset",
    "Ejecuta una consulta SoQL (SQL simplificado de Socrata) sobre un dataset de "
    "datos.gov.co y devuelve las filas en JSON. Todos los parámetros salvo dataset_id "
    "son opcionales. Consejos: agrega en el servidor con select + group (count(*), "
    "sum(), avg(), min(), max()) en lugar de traer miles de filas; los textos distinguen "
    "mayúsculas y tildes, así que filtra con upper(columna) like '%TEXTO%'; compara fechas en el formato de la columna "
    "('2026-01-31T00:00:00' si es fecha, '2026-01-31 00:00:00' si es texto; un texto se convierte con columna::floating_timestamp "
    "para usar date_trunc_ymd() o date_extract_hh()); un número guardado como texto se castea con columna::number (si la columna ya es numérica, úsala sin ::number: falla). En datasets muy grandes filtra siempre por periodo y por estación, entidad o municipio antes de agregar; si la consulta falla por tamaño o tiempo, divídela (por mes o por estación). Máximo 1000 filas.",
    {
        "type": "object",
        "properties": {
            **ARGUMENTOS_SOQL,
            "limit": {"type": "integer", "minimum": 1, "maximum": MAX_FILAS, "description": "Máximo de filas (por defecto 100)"},
        },
        "required": ["dataset_id"],
    },
    annotations=SOLO_LECTURA,
)
async def consultar_dataset(args: dict[str, Any]) -> dict[str, Any]:
    try:
        did = validar_id(args.get("dataset_id"))
        params = parametros_soql(args, limite_por_defecto=100, limite_maximo=MAX_FILAS)
        filas = (await pedir(f"{URL_BASE}/resource/{did}.json", params)).json()
    except ErrorDatos as e:
        return error(str(e))

    if not filas:
        return ok(
            "La consulta funcionó pero devolvió 0 filas. Posibles causas: mayúsculas o tildes "
            "en el filtro (usa upper(col) like '%...%'), formato de fecha, o que no haya datos "
            "en ese rango. Explora los valores reales con select + group."
        )
    return ok(
        {
            "filas_devueltas": len(filas),
            "nota": f"Se alcanzó el límite de {params['$limit']} filas: puede haber más. Usa group/agregaciones o filtros más estrictos."
            if len(filas) == params["$limit"]
            else "Resultado completo.",
            "datos": [recortar_textos(f) for f in filas],
        }
    )


@tool(
    "exportar_csv",
    "Ejecuta una consulta SoQL y guarda el resultado COMPLETO en un archivo CSV en la "
    "carpeta salidas/ (se abre bien en Excel). Úsala para entregar los datos de soporte "
    "de un informe o una lista de casos a revisar. Mismos parámetros que "
    "consultar_dataset más nombre_archivo (sin extensión). Hasta 50.000 filas.",
    {
        "type": "object",
        "properties": {
            **ARGUMENTOS_SOQL,
            "nombre_archivo": {"type": "string", "description": "Nombre del archivo sin extensión, ej. 'alertas_contratos'"},
            "limit": {"type": "integer", "minimum": 1, "maximum": MAX_FILAS_CSV, "description": "Máximo de filas (por defecto 5000)"},
        },
        "required": ["dataset_id", "nombre_archivo"],
    },
    annotations=ESCRIBE,
)
async def exportar_csv(args: dict[str, Any]) -> dict[str, Any]:
    try:
        did = validar_id(args.get("dataset_id"))
        params = parametros_soql(args, limite_por_defecto=5000, limite_maximo=MAX_FILAS_CSV)
        texto_csv = (await pedir(f"{URL_BASE}/resource/{did}.csv", params, timeout=120)).text
    except ErrorDatos as e:
        return error(str(e))

    filas = list(csv.reader(io.StringIO(texto_csv)))
    if len(filas) <= 1:
        return ok("La consulta no devolvió filas; no se creó ningún archivo.")

    CARPETA_SALIDAS.mkdir(exist_ok=True)
    ruta = CARPETA_SALIDAS / f"{nombre_archivo_seguro(args.get('nombre_archivo'))}.csv"
    ruta.write_text(texto_csv, encoding="utf-8-sig")  # utf-8-sig: Excel muestra bien tildes y eñes

    return ok(
        {
            "archivo": f"salidas/{ruta.name}",
            "filas": len(filas) - 1,
            "columnas": filas[0],
            "nota": "Se alcanzó el límite: puede haber más filas." if len(filas) - 1 == params["$limit"] else "Exportación completa.",
        }
    )


@tool(
    "enviar_telegram",
    "Envía un mensaje de texto a tu chat de Telegram (bot configurado en .env). Úsala "
    "para alertas o resúmenes cortos: texto plano, sin Markdown, máximo ~3500 caracteres.",
    {"mensaje": str},
    annotations=ESCRIBE,
)
async def enviar_telegram(args: dict[str, Any]) -> dict[str, Any]:
    token, chat_id = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat_id):
        return error("Telegram no está configurado (faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID).")
    mensaje = str(args.get("mensaje") or "").strip()[:4000]
    if not mensaje:
        return error("El mensaje está vacío.")
    try:
        async with httpx.AsyncClient(timeout=30) as cliente:
            respuesta = await cliente.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": mensaje, "disable_web_page_preview": True},
            )
    except httpx.HTTPError as e:
        # No mostramos la excepción completa: la URL contiene el token del bot.
        return error(f"No se pudo conectar a Telegram ({type(e).__name__}).")
    if respuesta.status_code != 200:
        return error(f"Telegram respondió {respuesta.status_code}: {respuesta.text[:300]}")
    return ok("Mensaje enviado a Telegram.")


# =========================================================================== #
# 4. SERVIDOR MCP: agrupa las herramientas. Esto es lo que recibe el agente.
# =========================================================================== #


def telegram_configurado() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def crear_servidor_datos():
    """👉 TALLER: si creas una herramienta nueva, defínela arriba con @tool y agrégala aquí."""
    herramientas = [buscar_datasets, describir_dataset, consultar_dataset, exportar_csv]
    if telegram_configurado():
        herramientas.append(enviar_telegram)
    return create_sdk_mcp_server(name="datos", version="1.0.0", tools=herramientas)


# =========================================================================== #
# 5. MODO PRUEBA: tú haces de cliente MCP, el mismo papel que cumple el agente
# =========================================================================== #


def leer_argumentos(pares: list[str]) -> dict[str, Any]:
    """['dataset_id=32sa-8pi3', 'limit=5']  ->  {'dataset_id': '32sa-8pi3', 'limit': 5}"""
    argumentos: dict[str, Any] = {}
    for par in pares:
        if "=" not in par:
            raise ValueError(f"'{par}' no tiene la forma clave=valor")
        clave, valor = par.split("=", 1)
        argumentos[clave.strip()] = int(valor) if valor.strip().lstrip("-").isdigit() else valor
    return argumentos


async def probar(comando: list[str]) -> int:
    from mcp import Client

    # Conectarse al servidor (en memoria, dentro de este mismo proceso)
    async with Client(crear_servidor_datos()["instance"]) as cliente:
        # tools/list: "¿qué sabes hacer?"
        herramientas = {h.name: h for h in (await cliente.list_tools()).tools}

        if not comando:
            print(f"tools/list → el servidor 'datos' expone {len(herramientas)} herramientas:\n")
            for h in herramientas.values():
                esquema = h.input_schema or {}
                requeridos = set(esquema.get("required", []))
                parametros = ", ".join(
                    nombre if nombre in requeridos else f"{nombre}?" for nombre in esquema.get("properties", {})
                )
                print(f"  {h.name}({parametros})")
            print("\n  (? = opcional)   Detalle de una:  uv run datos_colombia.py ver <herramienta>")
            return 0

        if comando[0] == "ver":
            h = herramientas.get(comando[1] if len(comando) > 1 else "")
            if not h:
                print(f"Indica una herramienta: {', '.join(herramientas)}")
                return 1
            print(json.dumps(h.model_dump(by_alias=True, exclude_none=True), indent=2, ensure_ascii=False))
            return 0

        nombre, pares = comando[0], comando[1:]
        if nombre not in herramientas:
            print(f"No existe '{nombre}'. Disponibles: {', '.join(herramientas)}")
            return 1
        try:
            argumentos = leer_argumentos(pares)
        except ValueError as e:
            print(e)
            return 1

        # tools/call: "haz esto con estos argumentos"
        print(f"tools/call → {nombre} {json.dumps(argumentos, ensure_ascii=False)}\n")
        resultado = await cliente.call_tool(nombre, argumentos)
        print("← ERROR (isError: true)\n" if resultado.is_error else "← OK\n")
        print("\n".join(getattr(bloque, "text", str(bloque)) for bloque in resultado.content))
        return 1 if resultado.is_error else 0


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parent / ".env")
    except ImportError:
        pass
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # tildes en consolas de Windows
    except (AttributeError, ValueError):
        pass
    sys.exit(asyncio.run(probar(sys.argv[1:])))
