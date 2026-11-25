# Agente de datos abiertos de Colombia

Un agente construido con el **Claude Agent SDK (Python)** que recibe una misión, consulta
[datos.gov.co](https://www.datos.gov.co) a través de un servidor MCP, analiza los datos y
**entrega archivos**: un informe en Markdown y los datos de soporte en CSV.

En el taller cada quien construye **su propio agente para su propio caso**: empresas,
contratación, medio ambiente, movilidad, educación… Casi siempre basta con escribir una
misión en un archivo Markdown; no hace falta tocar el código.

## Cómo está armado

Un agente es **modelo + herramientas + misión + límites**, y cada parte vive en su lugar:

| Capa | Archivo | Qué contiene |
|---|---|---|
| **Cómo se consulta** | `datos_colombia.py` | El servidor MCP: herramientas que sirven para CUALQUIER dataset de datos.gov.co. Sus descripciones le enseñan a Claude SoQL, tipos de datos y límites |
| **Cómo trabaja un analista** | `agente.py` | Modelo, método (no inventar cifras, revisar cobertura…), permisos, límites y formato de los entregables |
| **Qué se investiga** | `mision_*.md` | Tu caso: pregunta, fuentes, pasos, entregables. Es lo único que cambia de un caso a otro |

```
datos_colombia.py          → las herramientas (se pueden probar solas, sin agente)
agente.py                  → el agente
mision_plantilla.md        → la plantilla para escribir TU misión
mision_ejemplo.md          → una misión corta, lista para correr
mision_aire_antioquia.md   → el ejemplo grande: una investigación de varias corridas
salidas/                   → aquí el agente deja informes y CSV (se crea sola)

correr_managed.py          → opcional: el agente corriendo en Claude Managed Agents
```

Herramientas del servidor MCP `datos`:

| Herramienta | Qué hace |
|---|---|
| `buscar_datasets` | Busca datasets por palabra clave en el catálogo |
| `describir_dataset` | Columnas, tipos, fecha de actualización, total de filas y filas de ejemplo |
| `consultar_dataset` | Ejecuta una consulta SoQL y devuelve JSON (hasta 1.000 filas) |
| `exportar_csv` | Guarda el resultado completo de una consulta en `salidas/*.csv` |
| `enviar_telegram` | Opcional: manda un mensaje a tu Telegram |

Además, el agente tiene `Read`, `Write` y `Edit` (herramientas integradas del SDK) para
escribir sus entregables.

## 1. Prepara tu computador

Necesitas:

- **Python 3.10 o superior** y **git**.
- **uv**, que instala Python, las dependencias y corre los scripts. No necesitas instalar
  Python aparte: si no lo tienes, uv lo descarga solo la primera vez.
  ```bash
  # Linux, macOS o WSL
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  Después de instalarlo, cierra y vuelve a abrir la terminal.
- **git**, para clonar el repositorio:
  ```bash
  # Ubuntu o WSL
  sudo apt install git
  # macOS
  xcode-select --install
  # Windows (PowerShell)
  winget install --id Git.Git -e
  ```

Clona el repositorio:

```bash
git clone https://github.com/<usuario>/<repositorio>.git
cd <repositorio>
uv sync          # instala las dependencias, sin correr nada
```

## 2. Configura tu API key

Tienes dos formas. Usa una de las dos.

**Opción A, archivo `.env` (recomendada, queda guardada):**

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Abre `.env` y completa:

```
ANTHROPIC_API_KEY=sk-ant-...
```

**Opción B, variable de entorno (dura mientras esté abierta esa terminal):**

```bash
# Linux, macOS o WSL
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-..."

# Windows CMD
set ANTHROPIC_API_KEY=sk-ant-...
```

Si usas las dos, gana la variable de entorno.

> **Nunca subas tu `.env` a GitHub ni pegues tu API key en el código.** El `.gitignore`
> ya excluye `.env`. No abras ese archivo mientras proyectas la pantalla.

## 3. Prueba las herramientas, sin agente y sin gastar

Correr `datos_colombia.py` directamente te pone en el papel del cliente MCP: el mismo papel
que cumple el agente cuando Claude decide usar una herramienta. No usa la API key.

```bash
uv run datos_colombia.py                              # qué herramientas hay
uv run datos_colombia.py ver consultar_dataset        # lo que Claude "ve" de una herramienta
uv run datos_colombia.py buscar_datasets termino="calidad del aire"
uv run datos_colombia.py describir_dataset dataset_id=jbjy-vk9h
uv run datos_colombia.py consultar_dataset dataset_id=32sa-8pi3 limit=5 order="vigenciadesde DESC"
uv run datos_colombia.py exportar_csv dataset_id=32sa-8pi3 nombre_archivo=trm limit=100
```

## 4. Corre el agente de ejemplo

```bash
uv run agente.py mision_ejemplo.md
```

Verás cada herramienta que usa el agente mientras trabaja. Al final quedan los archivos en
`salidas/` y te ofrece seguir conversando sobre el resultado: escríbele otra pregunta o
pulsa Enter para salir (con `--sin-chat` no pregunta).

En nuestras pruebas, una misión de una sola corrida tomó unos minutos y costó entre
US$0,30 y US$1. El tope por corrida es `PRESUPUESTO_USD` en `.env` (US$2 por defecto).

## 5. Tu caso: crea tu propia misión (el reto del taller)

### a) Escoge tema y dataset

| Tema | Por dónde empezar | ID |
|---|---|---|
| Contratación pública | SECOP II, contratos firmados | `jbjy-vk9h` |
| Licitaciones abiertas | SECOP II, procesos de contratación | `p6dx-8zbt` |
| Empresas | Registro mercantil (RUES) | `c82u-588k` |
| Finanzas | TRM diaria (precio oficial del dólar) | `32sa-8pi3` |
| Medio ambiente | Calidad del aire IDEAM: resumen anual / mediciones horarias | `kekd-7v7h` / `g4t8-zkc3` |
| Educación | Saber 11 por estudiante, 2010 a 2022 | `kgxf-xxbe` |
| Movilidad y otros | Búscalo: `buscar_datasets termino="siniestros viales"` (o "accidentalidad", "comparendos"…) | — |

También puedes explorar en [datos.gov.co](https://www.datos.gov.co): el ID es la parte
`xxxx-xxxx` de la URL del dataset. Antes de escoger uno, mira su fecha de actualización con
`describir_dataset`: muchos datasets dejaron de actualizarse hace años.

### b) Escribe tu misión

Una buena misión no es una pregunta: es un trabajo con un entregable. Copia la plantilla:

```bash
cp mision_plantilla.md mision_mi_tema.md       # Windows: copy mision_plantilla.md mision_mi_tema.md
```

y llena sus seis partes:

| Parte | Qué va | Ejemplo |
|---|---|---|
| **ROL** | Para quién trabaja el agente | "Eres analista de una veeduría ciudadana de Envigado" |
| **PREGUNTA** | Una sola pregunta, con lugar y periodo | "¿A quién le contrató más plata la Alcaldía este año?" |
| **FUENTE** | El dataset y su ID (o "búscala") | "SECOP II, contratos (jbjy-vk9h)" |
| **PASOS** | 3 a 5 pasos concretos | "Suma el valor por contratista y por modalidad" |
| **ENTREGABLE** | Archivos concretos en `salidas/` | "Un informe con 3 hallazgos y un CSV con el top 20" |
| **REGLAS** | 1 a 3 reglas propias | "Escribe para alguien que no es experto" |

Mira `mision_ejemplo.md` para ver una misión completa.

**¿No sabes cómo plantearla? Pídele ayuda a Claude.** Pega esto en
[claude.ai](https://claude.ai):

```
Quiero construir un agente con el Claude Agent SDK que use datos abiertos de Colombia
(datos.gov.co). Sus herramientas: buscar_datasets, describir_dataset, consultar_dataset
(consultas SoQL), exportar_csv y escribir archivos.
Mi idea: [2 líneas: para quién trabaja y qué problema resuelve].
Hazme máximo 3 preguntas para aterrizarla. Luego escribe la misión en Markdown con estas
partes: ROL, PREGUNTA, FUENTE, PASOS (3 a 5), ENTREGABLE (archivos en salidas/) y REGLAS.
Que quepa en menos de 20 líneas y se pueda hacer en una sola corrida.
```

### c) Córrela

```bash
uv run agente.py mision_mi_tema.md
```

### d) Mejórala leyendo lo que hizo el agente

La primera versión casi nunca sale perfecta. Lee los pasos que imprime el agente, cambia
la misión y vuelve a correrla:

| Si ves esto… | Cambia esto en tu misión |
|---|---|
| Usó un dataset que no era | Pon el ID exacto en **FUENTE** |
| Consultas con 0 filas | Agrega en **PASOS** cómo se escribe el filtro (mayúsculas, nombre exacto) |
| Se acabó el presupuesto o los turnos | Reduce el alcance: menos años, menos municipios, menos pasos |
| Un informe genérico | Pide cifras y comparaciones concretas en **ENTREGABLE** |
| Cifras raras (ceros, duplicados) | Agrega una **REGLA**: "excluye valores 0", "quita duplicados" |

## 6. Qué puedes modificar

| Archivo | ¿Lo tocas? | Para qué |
|---|---|---|
| `mision_*.md` | **Sí, es tu trabajo** | Tu caso de uso |
| `.env` | Sí | Tu API key, el presupuesto (`PRESUPUESTO_USD`), los turnos (`MAX_TURNOS`) y el modelo (`MODELO_CLAUDE`) |
| `agente.py` → `SYSTEM_PROMPT` | Si quieres | Reglas de método que aplican a todas tus misiones: tono, público, formato del informe |
| `datos_colombia.py` | Si quieres | Agregar una herramienta propia (ver abajo) |
| El resto | No hace falta | — |

Pon cada cosa en su capa: lo que es de **tu caso** (columnas de tu dataset, umbrales, fechas,
hipótesis) va en tu misión; lo que sirve **para cualquier caso** va en `agente.py`; y cómo
se usa una herramienta va en su descripción, en `datos_colombia.py`.

### Agrega tu propia herramienta

Si tu caso necesita algo más que consultar datos (llamar otra API, enviar un mensaje,
guardar en una base de datos), define una función con `@tool` en `datos_colombia.py` y
agrégala a la lista de `crear_servidor_datos()`:

```python
@tool("mi_herramienta", "Qué hace y cuándo usarla (Claude lee esto).", {"parametro": str})
async def mi_herramienta(args):
    resultado = ...  # llama una API, escribe un archivo, envía un mensaje...
    return {"content": [{"type": "text", "text": str(resultado)}]}
```

Como `allowed_tools` usa el comodín `mcp__datos__*`, tu herramienta queda autorizada sin
tocar nada más. La descripción importa: es lo único que Claude sabe de tu herramienta.

## 7. Ejemplo avanzado: una investigación de varias corridas

`mision_aire_antioquia.md` investiga cuándo, dónde y por qué se ensucia el aire de
Antioquia (PM2.5, 2025) con dos datasets del IDEAM y pone a prueba tres hipótesis: la
pólvora de las noches de fiesta, una temporada crítica y un ciclo diario. Usa el mismo
formato que tu misión, con más secciones: hipótesis, umbrales, memoria y fases. Son 6 fases
y el agente hace máximo dos por corrida, así que la investigación completa toma 3 corridas:

```bash
uv run agente.py mision_aire_antioquia.md      # repítelo 3 veces
```

| Corrida | Fases | Qué deja en `salidas/` |
|---|---|---|
| 1 | Inventario y diagnóstico | `bitacora_aire.md`, `aire_estaciones_2025.csv` |
| 2 | Temporada crítica y pólvora | `aire_dias_criticos_2025.csv`, bitácora actualizada |
| 3 | Ciclo diario y entregables | `informe_aire_antioquia.md`, `mapa_aire_antioquia.html` |

La memoria entre corridas es `salidas/bitacora_aire.md`: el agente la lee al empezar y la
reescribe al terminar cada fase. Si una corrida se corta por turnos o presupuesto, vuelve a
lanzarla y retoma desde la última fase guardada. Para empezar de cero, borra la bitácora.

## 8. Opcional: el agente en la nube (Claude Managed Agents)

`correr_managed.py` corre un agente equivalente en la nube de Anthropic, sin servidor MCP:
el agente consulta datos.gov.co directamente con `curl` desde un sandbox que solo puede
salir a internet hacia datos.gov.co.

```bash
uv run correr_managed.py mision_mi_tema.md     # o una pregunta entre comillas
```

- La primera vez crea el agente y el entorno, y guarda sus IDs en `.managed.json`.
- Lo que el agente deja en `/mnt/session/outputs/` se descarga en `salidas/managed/<sesión>/`.
- Cada corrida aparece en la Consola, en [platform.claude.com](https://platform.claude.com) →
  Sessions, con la traza completa y su costo.
- Cada sesión empieza en blanco: las misiones de varias corridas, como `aire_antioquia`, no
  conservan su bitácora.

## Problemas comunes

- **`uv: command not found`:** cierra y vuelve a abrir la terminal después de instalar uv.
- **`Falta ANTHROPIC_API_KEY`, `Not logged in` o `Invalid API key`:** revisa el paso 2. Si
  usaste `export`, se pierde al abrir otra terminal.
- **`credit balance is too low`:** tu cuenta de Anthropic no tiene créditos.
- **Error 429:** el portal está limitando las consultas; agrega tu `SOCRATA_APP_TOKEN`.
- **0 filas:** casi siempre son mayúsculas o tildes en el filtro. El agente suele darse
  cuenta y corregir solo.
- **Presupuesto alcanzado:** sube `PRESUPUESTO_USD` en `.env`, o reduce el alcance de la misión.
- **Los datos de SECOP cambian a diario:** dos corridas pueden dar cifras distintas; es normal.

Los datos de datos.gov.co se publican bajo licencias abiertas (generalmente CC BY-SA 4.0):
cita la entidad fuente cuando compartas tus resultados.
