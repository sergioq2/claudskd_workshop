"""
Agente de datos abiertos de Colombia, construido con el Claude Agent SDK (Python).

El agente recibe una MISIÓN (no una pregunta), consulta datos.gov.co con las
herramientas de datos_colombia.py, analiza, y ENTREGA archivos en salidas/:
informes, CSV de soporte, un mapa (y opcionalmente una alerta por Telegram).

Tres capas, cada una en su lugar:
    datos_colombia.py  → CÓMO se consulta (las descripciones de las herramientas)
    agente.py          → CÓMO trabaja un analista (este archivo: método, límites, entregables)
    mision_*.md        → QUÉ se investiga (pregunta, fuentes, fases, entregables del caso)

Uso:
    uv run agente.py mision_ejemplo.md            # una misión escrita en Markdown
    uv run agente.py mision_aire_antioquia.md     # la investigación del aire (varias corridas)
    uv run agente.py aire_antioquia               # atajo: busca mision_aire_antioquia.md
    uv run agente.py "tu objetivo"                # misión libre: el agente busca los datos solo
    uv run agente.py mi_mision.md --sin-chat      # sin preguntas de seguimiento al final
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

# Carga variables desde .env si tienes python-dotenv (el SDK no lo hace solo).
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from datos_colombia import CARPETA_SALIDAS, crear_servidor_datos, telegram_configurado

CARPETA_PROYECTO = Path(__file__).resolve().parent

# --------------------------------------------------------------------------- #
# Instrucciones del agente: CÓMO trabaja, no qué investiga (eso está en la misión)
# ni cómo se escribe una consulta (eso lo explican las herramientas del MCP).
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """Eres un agente analista de datos abiertos de Colombia. Trabajas de forma \
autónoma hasta completar la misión y entregas resultados concretos (archivos), no solo respuestas. \
Escribe siempre en español de Colombia, tanto tus mensajes como los informes.

Cómo trabajas (las herramientas explican cómo consultar; tú decides qué y por qué):
- Antes de confiar en un dataset, revisa quién lo publica, qué mide cada columna, sus \
unidades, su cobertura (fechas y lugares) y su fecha de actualización.
- Si una consulta falla, lee el error, corrígela y reintenta (máximo 3 intentos).
- No inventes cifras: todo número del informe debe salir de una consulta. Si algo no se \
puede calcular con los datos disponibles, dilo explícitamente.
- Distingue la falta de datos de un valor cero, y no presentes un periodo incompleto como \
si estuviera completo.
- Una coincidencia en el tiempo no prueba una causa: describe patrones y di lo que los \
datos no permiten afirmar.
- Los datos abiertos tienen errores de digitación: señala los valores atípicos como \
"a revisar", nunca como prueba de una irregularidad. Tu análisis es exploratorio: no \
declares incumplimientos legales.
- Si después de reintentar no logras obtener datos (por ejemplo, error de conexión), no \
escribas un informe vacío ni una plantilla: explica qué falló y detente.

Entregables:
- Escribe los informes en la carpeta salidas/, en Markdown y en español, con: resumen \
ejecutivo (3 a 5 líneas), cifras clave, hallazgos, y una sección "Fuente y metodología" con \
el nombre y el ID del dataset, el enlace https://www.datos.gov.co/d/<id>, la fecha de \
consulta y las limitaciones.
- Usa exportar_csv para entregar los datos de soporte.
- Escribe los valores en pesos con punto como separador de miles (ej. $1.250.000.000).
- Al terminar, responde con un resumen breve de lo que encontraste y la lista de archivos creados.

Fecha de hoy: {hoy}."""


# --------------------------------------------------------------------------- #
# Salida por consola: ver al agente trabajar es la mitad de la gracia
# --------------------------------------------------------------------------- #


def _resumen_argumentos(nombre: str, entrada: dict) -> str:
    if nombre in ("Write", "Read", "Edit"):
        return entrada.get("file_path", "")
    texto = json.dumps(entrada, ensure_ascii=False)
    return texto if len(texto) <= 220 else texto[:220] + "…"


def mostrar(mensaje) -> None:
    if isinstance(mensaje, AssistantMessage):
        for bloque in mensaje.content:
            if isinstance(bloque, TextBlock) and bloque.text.strip():
                print(f"\n[Claude] {bloque.text.strip()}", flush=True)
            elif isinstance(bloque, ToolUseBlock):
                nombre = bloque.name.removeprefix("mcp__datos__")
                print(f"\n  -> {nombre}  {_resumen_argumentos(nombre, bloque.input)}", flush=True)

    elif isinstance(mensaje, UserMessage) and isinstance(mensaje.content, list):
        for bloque in mensaje.content:
            if isinstance(bloque, ToolResultBlock) and bloque.is_error:
                print("     (la herramienta devolvió un error; el agente lo va a corregir)", flush=True)

    elif isinstance(mensaje, ResultMessage):
        costo = f"US${mensaje.total_cost_usd:.3f}" if mensaje.total_cost_usd is not None else "N/D"
        print(
            f"\n=== Fin: {mensaje.subtype} | {mensaje.num_turns} turnos | "
            f"{mensaje.duration_ms / 1000:.0f} s | costo aprox. {costo} ===",
            flush=True,
        )
        if mensaje.subtype == "error_max_turns":
            print("El agente llegó al máximo de turnos. Sube max_turns o simplifica la misión.")
        elif mensaje.subtype == "error_max_budget_usd":
            print("El agente llegó al presupuesto máximo. Ajusta PRESUPUESTO_USD en tu .env.")


def listar_archivos_nuevos(desde: float) -> None:
    if not CARPETA_SALIDAS.exists():
        return
    nuevos = sorted(p for p in CARPETA_SALIDAS.iterdir() if p.is_file() and p.stat().st_mtime >= desde)
    if nuevos:
        print("\nArchivos entregados:")
        for ruta in nuevos:
            print(f"  - {ruta.relative_to(CARPETA_PROYECTO)}  ({ruta.stat().st_size / 1024:.1f} KB)")


# --------------------------------------------------------------------------- #
# Programa principal
# --------------------------------------------------------------------------- #


def leer_mision_md(ruta: Path) -> tuple[str, str]:
    """Una misión escrita en un archivo Markdown (ver mision_plantilla.md)."""
    if not ruta.is_file():
        print(f"No encuentro el archivo {ruta}. Copia mision_plantilla.md y llénala con tu caso.")
        sys.exit(1)
    texto = ruta.read_text(encoding="utf-8").strip()
    titulo = next((l.lstrip("# ").strip() for l in texto.splitlines() if l.startswith("# ")), ruta.stem)
    return titulo, texto


def elegir_mision(argumentos: list[str]) -> tuple[str, str]:
    if not argumentos:
        print(__doc__)
        print("Misiones en esta carpeta:", ", ".join(sorted(p.name for p in CARPETA_PROYECTO.glob("mision_*.md"))))
        sys.exit(0)
    if len(argumentos) == 1:
        # Un archivo .md, o un atajo: "aire_antioquia" busca mision_aire_antioquia.md
        nombre = argumentos[0]
        if nombre.lower().endswith(".md"):
            return leer_mision_md(Path(nombre))
        atajo = CARPETA_PROYECTO / f"mision_{nombre}.md"
        if atajo.is_file():
            return leer_mision_md(atajo)
    objetivo_libre = " ".join(argumentos)
    return (
        "Misión libre",
        f"{objetivo_libre}\n\nEncuentra los datos necesarios en datos.gov.co, analízalos y "
        "entrega un informe en salidas/ con los datos de soporte en CSV.",
    )


def hay_credenciales() -> bool:
    proveedores = (
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "CLAUDE_CODE_USE_ANTHROPIC_AWS",
    )
    return any(os.environ.get(v) for v in proveedores)


async def main() -> None:
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    sin_chat = "--sin-chat" in sys.argv
    titulo, objetivo = elegir_mision(argumentos)

    if not hay_credenciales():
        print("Falta ANTHROPIC_API_KEY. Créala en https://platform.claude.com y agrégala a tu .env")
        sys.exit(1)

    if telegram_configurado():
        objetivo += (
            "\n\nAl terminar, envía por Telegram un resumen de máximo 6 líneas con los "
            "hallazgos más importantes y el nombre del informe."
        )

    CARPETA_SALIDAS.mkdir(exist_ok=True)

    opciones = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT.format(hoy=date.today().isoformat()),
        # Nuestras herramientas de datos, corriendo dentro de este mismo proceso
        mcp_servers={"datos": crear_servidor_datos()},
        # Usar SOLO nuestro servidor MCP, aunque el computador tenga otros configurados
        strict_mcp_config=True,
        # Herramientas integradas disponibles: solo leer, escribir y editar archivos (sin Bash)
        tools=["Read", "Write", "Edit"],
        # Herramientas que corren sin pedir permiso
        allowed_tools=["mcp__datos__*", "Read", "Write", "Edit"],
        # Si tienes Claude in Chrome activo en Claude Code, se lo ocultamos al agente
        disallowed_tools=["mcp__claude-in-chrome"],
        permission_mode="acceptEdits",
        cwd=str(CARPETA_PROYECTO),
        # No cargar configuraciones personales de ~/.claude: el agente se comporta
        # igual en el computador de todos los participantes
        setting_sources=[],
        # Con pocas herramientas es más rápido cargarlas todas desde el inicio
        env={"ENABLE_TOOL_SEARCH": "false"},
        # Límites de seguridad para que un error no se convierta en una factura
        max_turns=int(os.environ.get("MAX_TURNOS", "40")),
        max_budget_usd=float(os.environ.get("PRESUPUESTO_USD", "2")),
        model=os.environ.get("MODELO_CLAUDE") or None,
    )

    print(f"\n=== {titulo} ===")
    print("El agente va a trabajar solo. Verás cada herramienta que usa.\n")
    inicio = time.time()

    async with ClaudeSDKClient(options=opciones) as cliente:
        await cliente.query(objetivo)
        async for mensaje in cliente.receive_response():
            mostrar(mensaje)
        listar_archivos_nuevos(inicio)

        # Seguimiento: el mismo cliente conserva el contexto de la sesión
        if sin_chat or not sys.stdin.isatty():
            return
        while True:
            pregunta = await asyncio.to_thread(
                input, "\nPídele algo más al agente (Enter para salir): "
            )
            if not pregunta.strip():
                break
            inicio = time.time()
            await cliente.query(pregunta)
            async for mensaje in cliente.receive_response():
                mostrar(mensaje)
            listar_archivos_nuevos(inicio)


if __name__ == "__main__":
    # Consolas de Windows: asegurar que tildes y eñes se impriman bien
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrumpido.")
