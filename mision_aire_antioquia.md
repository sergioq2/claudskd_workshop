# Investigación: ¿cuándo, dónde y por qué se ensucia el aire de Antioquia?

ROL: Eres el analista de datos de una investigación periodística sobre el aire que respiran los antioqueños. Tus lectores no son expertos en calidad del aire.

PREGUNTA: ¿Cuándo y dónde aumentó el material particulado fino (PM2.5) en Antioquia durante 2025, y qué patrones lo acompañan? Usa 2024 y 2023 como comparación cuando haya datos comparables.

HIPÓTESIS (respáldalas o descártalas con datos):
- H1. Los picos horarios coinciden con las noches de pólvora.
- H2. Los días más contaminados se concentran en pocos meses.
- H3. Hay un ciclo diario: el aire empeora siempre a las mismas horas.

FUENTES (IDEAM, en datos.gov.co):
- kekd-7v7h: resumen anual por estación y variable (promedio, representatividad, días de excedencia, máximo y su fecha, coordenadas). Para promedios y excedencias usa los registros de 24 horas; para máximos horarios, los de 1 hora.
- g4t8-zkc3: mediciones horarias. Es enorme: consulta una estación y un periodo a la vez.
- Las dos fuentes no comparten identificadores de estación. Empareja cada estación con evidencia (nombre, municipio y coordenadas), anota los cruces dudosos y déjalos fuera de las comparaciones que los necesiten.

UMBRALES (Resolución 2254 de 2017, para PM2.5): 37 µg/m³ como promedio de 24 horas y 25 µg/m³ como promedio anual. Usar 25 µg/m³ para días es solo un umbral de análisis. No compares una medición horaria con un límite diario.

MEMORIA ENTRE CORRIDAS: tu memoria es salidas/bitacora_aire.md.
1. Al empezar, léela. Si no existe, empieza en la fase 1; si existe, sigue en la primera fase pendiente.
2. Haz como máximo DOS fases por corrida.
3. Al terminar cada fase, reescríbela completa: fases terminadas, parciales o bloqueadas (con el motivo), hallazgos con cifras, consultas que funcionaron, cruces de estaciones, descartes y próximos pasos.
4. Después de dos fases, detente y resume qué hiciste y qué sigue.

FASES:
1. Inventario. Estaciones de Antioquia que midieron PM2.5 en 2025 (resumen anual, registros de 24 horas): operador, municipio, tipo, representatividad y coordenadas. Son ELEGIBLES las no indicativas con representatividad de al menos 75 %. Exporta el inventario a CSV 'aire_estaciones_2025'.
2. Diagnóstico. Ranking de las elegibles por promedio anual frente a 25 µg/m³, con sus días de excedencia del límite de 37 µg/m³. Compara cada una con su propio valor de 2024 y 2023, con los mismos criterios.
3. Temporada crítica (H2). Para las 5 elegibles con mayor promedio, calcula promedios diarios de 2025 contando solo días con al menos 18 horas medidas. Por mes: días evaluables, días sobre 37 y sobre 25 µg/m³, y su proporción. Los días en que varias estaciones superan 37 a la vez son episodios simultáneos. Exporta los días críticos a CSV 'aire_dias_criticos_2025'.
4. Pólvora (H1). En las estaciones elegibles, compara cada hora de estas noches con el promedio de esa misma hora en 2025, sin contar las noches de fiesta:
   - Año Nuevo: 31 dic 2024 22:00 a 1 ene 2025 04:00
   - Alborada: 30 nov 2025 22:00 a 1 dic 2025 04:00
   - Velitas: 7 dic 2025 22:00 a 8 dic 2025 06:00
   - Nochebuena: 24 dic 2025 22:00 a 25 dic 2025 03:00
   Di cuántas veces por encima de lo normal estuvo cada estación y cuántos máximos horarios del año (resumen anual, registros de 1 hora) caen en esas noches. Habla de coincidencia, no de causa.
5. Ciclo diario (H3). Perfil horario de 2025 de tres elegibles de contextos distintos: una de tráfico del centro de Medellín, una residencial del Valle de Aburrá y la de menor promedio. ¿A qué hora es el pico y a qué hora el mínimo?
6. Entregables finales (ver abajo).

ENTREGABLES:
- salidas/informe_aire_antioquia.md: un titular respaldado por los datos, el resumen ejecutivo, cada hipótesis marcada como respaldada, parcialmente respaldada, no respaldada o sin evidencia suficiente (con cifras), el ranking de estaciones, las limitaciones y la metodología. Enlaza los CSV de las fases anteriores.
- salidas/mapa_aire_antioquia.html: un mapa en un solo archivo con Leaflet 1.9.4 desde https://unpkg.com/leaflet@1.9.4/dist/ y mapa base de OpenStreetMap con su atribución. Un círculo por estación coloreado según su promedio anual frente a 25 µg/m³, las estaciones excluidas con otro estilo, una ventana con los datos de cada estación y una leyenda. Los datos van escritos dentro del HTML.
