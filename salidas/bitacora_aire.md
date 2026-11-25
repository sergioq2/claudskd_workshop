# Bitácora — Investigación PM2.5 Antioquia 2025

Última actualización: 2026-11-24 (corrida 2: fases 3 y 4)

## Estado de fases

| Fase | Estado |
|---|---|
| 1. Inventario y calidad del dato | ✅ TERMINADA (2026-11-19) |
| 2. Diagnóstico y tendencia | ✅ TERMINADA (2026-11-19) |
| 3. Temporada crítica (H2) | ✅ TERMINADA (2026-11-24, corrida 2) |
| 4. La pólvora (H1) | ✅ TERMINADA (2026-11-24, corrida 2) |
| 5. Ciclo diario y geografía (H3) | ⏳ PENDIENTE — siguiente |
| 6. Entregables finales | ⏳ PENDIENTE |

## Archivos generados

- `salidas/aire_estaciones_2025.csv` (fase 1): 43 filas, todas las estaciones de Antioquia con PM2.5 en 2025 (filas de 24 h), con columna `calidad`.
- `salidas/aire_dias_criticos_2025.csv` (fase 3): 284 filas, estación-días 2025 con promedio > 25 µg/m³ (≥ 18 h), columna `categoria` (> 37 o 25–37).
- `salidas/aire_polvora_2025.csv` (fase 4): 92 filas (23 estaciones × 4 noches): horas con dato, promedio y pico de la noche, línea base de las mismas horas en 2025 y "veces sobre lo normal" (promedio y pico). Escrito a mano con cifras de dos consultas (ver abajo).
- `salidas/aire_tendencia_2023_2025.csv` (fase 2): 72 filas, promedio anual, representatividad y días de excedencia 2023–2025 de las 25 estaciones confiables.

## Notas sobre los datos (kekd-7v7h)

- `nombre_del_departamento` viene en MAYÚSCULAS ('ANTIOQUIA'): filtrar con `upper(nombre_del_departamento) like '%ANTIOQUIA%'`.
- `representatividad_temporal` es TEXTO: usar `representatividad_temporal::number`.
- En 2023 los nombres de estación llevan un asterisco (ej. 'CASA JUSTICIA*'): cruzar años por `id_estacion`, no por nombre.
- Dataset actualizado el 2026-10-19; 30.665 filas.
- En las filas de 24 h, `fechas_horas_del_m_ximo` trae solo la fecha (ej. '2025-01-01') y `m_ximo` es el promedio diario máximo. Para máximos HORARIOS (fase 4) hay que usar las filas de 1 h (`tiempo_de_exposici_n_horas=1`).

## Fase 1 — Hallazgos (inventario 2025)

- 43 estaciones de Antioquia reportaron PM2.5 en 2025 (filas de 24 h).
- Operadores: AMVA (25 estaciones, todas fijas, Valle de Aburrá), CORANTIOQUIA (7: 6 fijas + 1 indicativa) y CORNARE (11, todas indicativas, oriente y Magdalena Medio).
- Criterio CONFIABLE: representatividad >= 75 % **y** estación fija. Resultado: **25 estaciones confiables**, todas del AMVA (Valle de Aburrá).
- Aparte (rep >= 75 % pero indicativa): SAN ANTONIO (Rionegro, CORNARE, id 31977), rep 93 %, promedio 9,21 µg/m³, 0 días de excedencia. No entra al ranking principal.
- 17 estaciones NO CONFIABLES (rep < 75 %): las 7 de CORANTIOQUIA (rep 20–66 %) y 10 de CORNARE (rep 3–53 %).
- Casos "a revisar":
  - I.E. JORGE ELIECER G. (31792, Bello): rep 92 % pero solo 117 datos diarios; POLITÉCNICO JIC (9060): rep 75 % con 95 datos. La representatividad parece calcularse sobre el periodo de operación, no sobre el año. Se mantienen como confiables (cumplen el criterio), con advertencia.
  - Estaciones no confiables con promedios altos: FER (Amagá, CORANTIOQUIA, 31849) 22,80 µg/m³, 7 días exc., máximo diario 52 el 2025-06-25, rep 52 %; ITA-LGO (Medellín, CORANTIOQUIA, indicativa, 30855) 21,87 µg/m³, 11 días exc., rep 64 %. Reportar aparte, con advertencia.

### Lista de las 25 confiables (id): 
31367, 29509, 29511, 31340, 31343, 31360, 31362, 31364, 29493, 31369, 31373, 31375, 31379, 31628, 31855, 31856, 31946, 31994, 32036, 31366, 32034, 31371, 31854, 31792, 9060

## Fase 2 — Hallazgos (diagnóstico y tendencia)

- **Ninguna estación confiable superó el límite anual de 25 µg/m³ en 2025.** La más alta: TRÁFICO CENTRO 23,76 µg/m³ (95 % del límite).
- En 2024 TRÁFICO CENTRO sí lo superó (28,48 µg/m³).
- Promedio simple de las estaciones confiables: 2023 = 16,96 (22 est.), 2024 = 18,02 (25 est.), 2025 = 14,91 (25 est.).
- Días de excedencia (> 37 µg/m³ en 24 h), suma de las 25 estaciones: 2023 = 58 (22 est.), 2024 = 197, **2025 = 11**. En 2025 solo 5 estaciones tuvieron algún día de excedencia: TRÁFICO CENTRO 7, CASA JUSTICIA 1, I.E. CIRO MENDIA 1, VILLAHERMOSA 1, LICEO FERNANDO VÉLEZ 1.
- 24 de 25 estaciones mejoraron frente a 2024; la única que empeoró: I.E. CONCEJO MUNICIPAL (Itagüí) +0,50 µg/m³ (+3,1 %).
- Frente a 2023, solo TRÁFICO CENTRO quedó por encima (23,76 vs 23,4; +1,5 %).
- 2025 fue el mejor de los tres años en casi todas las estaciones. (No se analiza la causa; posible influencia meteorológica — no comprobable con estos datos.)

### Ranking 2025 (promedio anual µg/m³ | 2024 | 2023 | días exc. 2025 (2024) | cambio vs 2024)

| # | Estación (id) | Municipio | 2025 | 2024 | 2023 | Exc 2025 (2024) | Δ vs 2024 |
|---|---|---|---|---|---|---|---|
| 1 | TRÁFICO CENTRO (29509) | Medellín | 23,76 | 28,48 | 23,4 | 7 (30) | −16,6 % |
| 2 | ALTAVISTA (31371) | Medellín | 19,27 | 23,10 | 19,5 | 0 (15) | −16,6 % |
| 3 | CASA JUSTICIA (29493) | Itagüí | 18,52 | 22,52 | 19,1 | 1 (18) | −17,8 % |
| 4 | I.E. PEDRO JUSTO B. (31369) | Medellín | 18,27 | 21,29 | 19,4 | 0 (9) | −14,2 % |
| 5 | LA TABLAZA I.E JOSE ANTONIO GALAN (32036) | La Estrella | 17,95 | 18,76* | — | 0 (0) | −4,3 % |
| 6 | POLITÉCNICO JIC (S) (9060) | Medellín | 17,53 | 20,18 | 18,6* | 0 (3) | −13,1 % |
| 7 | ALMACÉN GENERAL DE EPM (31994) | Medellín | 16,85 | 17,73 | — | 0 (5) | −4,9 % |
| 8 | I.E. CONCEJO MUNICIPAL (29511) | Itagüí | 16,64 | 16,13 | 18,3 | 0 (3) | +3,1 % |
| 9 | FISCALÍA SECTOR CARIBE (31854) | Medellín | 16,55 | 20,01 | 20,1 | 0 (6) | −17,3 % |
| 10 | I.E. CIRO MENDIA (31364) | Medellín | 16,31 | 19,31 | 17,7 | 1 (11) | −15,6 % |
| 11 | P. BIBLIOTECA TOMÁS CARRASQUILLA - LA QUINTANA (31946) | Medellín | 15,35 | 17,38 | 16,2 | 0 (7) | −11,7 % |
| 12 | BIBLIOTECA FERNANDO B. (31366) | Medellín | 14,48 | 16,37 | 16,9 | 0 (3) | −11,6 % |
| 13 | ESCUELA JOAQUÍN A. (31340) | Caldas | 14,42 | 19,24 | 16,3 | 0 (12) | −25,0 % |
| 14 | VILLAHERMOSA (31367) | Medellín | 13,88 | 16,87 | 16,1 | 1 (5) | −17,7 % |
| 15 | HOSPITAL (31379) | La Estrella | 13,87 | 20,16 | 19,2 | 0 (15) | −31,2 % |
| 16 | I.E. JOSÉ FÉLIX (31373) | Medellín | 13,63 | 16,97 | 17,1 | 0 (7) | −19,7 % |
| 17 | I.E. RAFAEL J. MEJÍA (31628) | Sabaneta | 13,55 | 18,32 | 18,1 | 0 (12) | −26,0 % |
| 18 | HOSPITAL MANUEL URIBE (31375) | Envigado | 13,47 | 16,45 | 15,1 | 0 (6) | −18,1 % |
| 19 | TANQUES EPM (31856) | Girardota | 12,97 | 16,91 | 13,7 | 0 (9) | −23,3 % |
| 20 | I.E. JORGE ELIECER G. (31792) | Bello | 12,77 | 16,70 | 15,1* | 0 (2) | −23,5 % |
| 21 | LICEO FERNANDO VÉLEZ (31362) | Bello | 12,30 | 15,95 | 15,6 | 1 (4) | −22,9 % |
| 22 | TORRE SOCIAL (31343) | Barbosa | 11,38 | 14,34 | 12,5 | 0 (6) | −20,7 % |
| 23 | CIUDADELA EDUCATIVA (31360) | Copacabana | 11,27 | 15,12 | 14,7 | 0 (6) | −25,4 % |
| 24 | UNIVERSIDAD CES (32034) | Medellín | 10,52 | 10,79* | — | 0 (0) | −2,5 % |
| 25 | SANTA ELENA (31855) | Medellín (rural) | 7,32 | 11,54 | 10,4 | 0 (3) | −36,6 % |

(*) año comparativo con representatividad < 75 %: La Tablaza 2024 57 %, CES 2024 58 %, Politécnico 2023 52 %, Jorge Eliécer 2023 63 %. Comparación con cautela.

Todas las estaciones confiables son del AMVA (tipo Fija). Coordenadas en `aire_estaciones_2025.csv`.

## Cruce de estaciones kekd-7v7h ↔ g4t8-zkc3 (corrida 2)

- En la práctica `estacion_id` (g4t8) = `id_estacion` (kekd) para las 43 estaciones de Antioquia 2025. Verificado además por nombre, municipio y coordenadas idénticas (ej. 29509 TRÁFICO CENTRO 6.252709/-75.569656 en ambas) y porque el promedio de las horas 2025 reproduce el promedio anual de kekd (TRÁFICO CENTRO 23,79 vs 23,76; CASA JUSTICIA 18,51 vs 18,52; PEDRO JUSTO 18,27 vs 18,27; ALTAVISTA 19,28 vs 19,27; LA TABLAZA 18,01 vs 17,95; SANTA ELENA 7,50 vs 7,32). Cruce: SEGURO para las 23 AMVA horarias.
- DUDOSO / NO SIRVE PARA ANÁLISIS HORARIO: I.E. JORGE ELIECER G. (31792) y POLITÉCNICO JIC (9060) tienen `duraci_n`=1440 en g4t8 (muestreadores de 24 h, 117 y 95 registros). No tienen datos horarios → quedan fuera de fases 4 y 5.
- g4t8: `med_fecha_inicio` es TEXTO ('2025-01-01 00:00:00'); `codigo_departamento`=5 para Antioquia; `msfl_code`='PM2.5'; sin nulos en las 5 estaciones top; mínimo 0,5 (posible límite de detección).

## Fase 3 — Hallazgos (temporada crítica, H2)

Estaciones: TRÁFICO CENTRO (29509), ALTAVISTA (31371), CASA JUSTICIA (29493), PEDRO JUSTO B. (31369), LA TABLAZA (32036). Promedio diario = media de horas del día; día evaluable si ≥ 18 horas. Conteo en "estación-días".

| Mes 2025 | Estación-días evaluables | Días > 25 | % > 25 | Días > 37 | % > 37 |
|---|---|---|---|---|---|
| Ene | 147 | 41 | 27,9 % | 0 | 0 % |
| Feb | 130 | 47 | 36,2 % | 2 | 1,5 % |
| Mar | 155 | 83 | 53,5 % | 5 | 3,2 % |
| Abr | 138 | 22 | 15,9 % | 0 | 0 % |
| May | 134 | 7 | 5,2 % | 0 | 0 % |
| Jun | 132 | 6 | 4,5 % | 0 | 0 % |
| Jul | 155 | 1 | 0,6 % | 0 | 0 % |
| Ago | 152 | 3 | 2,0 % | 0 | 0 % |
| Sep | 148 | 11 | 7,4 % | 0 | 0 % |
| Oct | 148 | 17 | 11,5 % | 0 | 0 % |
| Nov | 136 | 21 | 15,4 % | 0 | 0 % |
| Dic | 136 | 25 | 18,4 % | 0 | 0 % |
| **Total** | **1.711** | **284** | **16,6 %** | **7** | **0,41 %** |

- Ene–Mar concentran 171 de 284 días > 25 (60,2 %) y los 7 de 7 días > 37. Marzo solo: 83 (29,2 % del total). Julio–agosto casi limpios (4 días).
- Días > 37 (con ≥ 18 h): TRÁFICO CENTRO 2025-02-05 (41,4), 03-11 (37,5), 03-12 (37,2), 03-15 (40,0), 03-25 (41,8), 03-28 (38,6); CASA JUSTICIA 02-07 (37,9). (03-29 TRÁFICO CENTRO = 37,00 exacto, no cuenta.) kekd reporta 7 días para TRÁFICO CENTRO: diferencia de 1 día probablemente por redondeo/criterio de completitud — anotar.
- **Episodios simultáneos (≥ 2 estaciones > 37 el mismo día): NINGUNO en 2025.** Indicador alternativo: 13 días con las 5 estaciones > 25 a la vez (01-21, 01-22, 01-23, 01-24, 02-05, 03-04, 03-11, 03-13, 03-15, 03-25, 03-26, 03-27, 03-28), todos en ene–mar. Con ≥ 4 estaciones > 25: 25 días, 24 en ene–mar + 2025-11-27.
- Días > 25 por estación: TRÁFICO CENTRO 130 (de 345 evaluables), CASA JUSTICIA 46 (342), ALTAVISTA 45 (344), PEDRO JUSTO 38 (347), LA TABLAZA 25 (333).
- Evaluables por estación: CJ 342, TC 345, PJB 347, ALT 344, TAB 333.
- H2: RESPALDADA (pocos meses: feb–mar para > 37; ene–mar para > 25). Segundo repunte menor oct–dic.
- Ojo para fase 4: el 2025-12-07 las 5 estaciones tienen solo 7–8 horas medidas (hueco de datos el día de Velitas). Revisar si la noche 7→8 dic tiene datos.
- No se hizo comparación mensual con 2024 (pendiente opcional; kekd no trae datos mensuales).

## Fase 4 — Hallazgos (pólvora, H1)

Método: 23 estaciones AMVA horarias (elegibles menos Jorge Eliécer y Politécnico, que son de 24 h). Ventanas tomadas por hora de INICIO: Año Nuevo 2024-12-31 22:00 → 2025-01-01 03:00 (6 h), Alborada 2025-11-30 22:00 → 12-01 03:00 (6 h), Velitas 12-07 22:00 → 12-08 05:00 (8 h), Nochebuena 12-24 22:00 → 12-25 02:00 (5 h). Línea base = promedio 2025 de las mismas horas de reloj, excluyendo las 4 ventanas. "Veces sobre lo normal" = promedio de la noche / línea base (y pico horario de la noche / línea base). Para Año Nuevo, las 22–23 h son de 2024 pero se comparan con la base 2025.

| Noche | Estaciones con dato | Sobre lo normal (>1×) | Mediana de veces | Rango | Máximo |
|---|---|---|---|---|---|
| Año Nuevo | 23 | 23 | 3,26× | 1,49× (Almacén EPM) – 7,67× (Villahermosa) | 22 de 23 ≥ 2× |
| Alborada | 23 | 9 | 0,87× | 0,59× – 1,62× (Liceo F. Vélez) | ninguna ≥ 2× |
| Velitas | 23 | 20 | 1,61× | 0,28× – 5,26× (Liceo F. Vélez) | 10 ≥ 2× |
| Nochebuena | 21 (sin dato: Hospital La Estrella, Liceo F. Vélez) | 21 | 2,34× | 1,40× – 4,47× (Villahermosa) | |

- Picos horarios más altos en noches de fiesta: CIRO MENDÍA 194,8 µg/m³ (1 ene 01:00; 12,7× su base) y 129,3 (Velitas); VILLAHERMOSA 170,2 (1 ene 02:00; 13,0×); ALTAVISTA 117,8 (1 ene); LA QUINTANA 106 (1 ene).
- **Máximos horarios del año (kekd, filas de 1 h, 23 estaciones AMVA): 13 de 23 caen en noches de fiesta**: 9 en Año Nuevo (1 ene 01:00–02:00: La Quintana, Tráfico Centro, Concejo Municipal, Joaquín A., Torre Social, Ciro Mendía, Biblioteca F. B., Altavista, Villahermosa), 3 en Velitas (8 dic 01:00–05:00: Casa Justicia, Liceo F. Vélez, Ciudadela Educativa), 1 en Nochebuena (24 dic 23:00: La Tablaza), 0 en Alborada. Los otros 10 caen de día en feb–mar (6) y nov–dic (4: Almacén EPM 28 nov 10:00; Pedro Justo 178,85 el 5 dic 11:00; Fiscalía 123 el 22 dic 14:00; Santa Elena 93,49 el 27 dic 21:00).
- A REVISAR: Pedro Justo 178,85 (5 dic 11:00), Fiscalía 123 (22 dic 14:00), Santa Elena 93,49 (27 dic 21:00; estación rural con promedio 7,3) — picos aislados diurnos, posible evento local o error. Almacén EPM en Velitas 4,7 µg/m³ (0,28×, 7 h) y CES/Santa Elena en Velitas con solo 4 h: valores bajos y huecos sospechosos (el 7 dic hay pocas horas en todas las estaciones).
- H1: RESPALDADA PARCIALMENTE / mayormente — Año Nuevo, Velitas y Nochebuena muestran noches muy por encima de lo normal y concentran 13 de 23 máximos anuales; la Alborada 2025 NO (mediana 0,87×). Es coincidencia temporal; los datos no identifican la fuente (no hay composición química ni meteorología).

## Consultas SoQL que funcionaron

Noches de fiesta (g4t8-zkc3):
```
select = estacion_id, case(med_fecha_inicio < '2025-01-02 00:00:00','1_AnoNuevo', med_fecha_inicio < '2025-12-02 00:00:00','2_Alborada', med_fecha_inicio < '2025-12-09 00:00:00','3_Velitas', true,'4_Nochebuena') AS noche, count(*) AS h, avg(med_concentracion_estandar) AS prom, max(med_concentracion_estandar) AS mx
where  = msfl_code='PM2.5' AND codigo_departamento=5 AND duraci_n=60 AND nombre_fgda='AMVA' AND ((med_fecha_inicio >= '2024-12-31 22:00:00' AND med_fecha_inicio <= '2025-01-01 03:00:00') OR (... las otras 3 ventanas ...))
group  = estacion_id, noche
```
Línea base (funciona `avg(case(cond, valor))` sin rama true → null):
```
select = estacion_id, avg(case(date_extract_hh(med_fecha_inicio::floating_timestamp) in (22,23,0,1,2,3), med_concentracion_estandar)) AS base_22a03, ... (22..5), ... (22..2)
where  = ... año 2025 AND hora in (22,23,0..5) AND NOT (ventanas de fiesta)
group  = estacion_id
```
Máximos horarios: kekd-7v7h con `tiempo_de_exposici_n_horas=1 AND autoridad_ambiental='AMVA' AND a_o=2025 AND variable='PM2.5'`.

Inventario 2025 (kekd-7v7h):
```
select = id_estacion, estaci_n, autoridad_ambiental, nombre_del_municipio, tipo_de_estaci_n, representatividad_temporal, promedio, d_as_de_excedencias, m_ximo, fechas_horas_del_m_ximo, latitud, longitud, no_de_datos
where  = upper(nombre_del_departamento) like '%ANTIOQUIA%' AND variable='PM2.5' AND a_o=2025 AND tiempo_de_exposici_n_horas=24
order  = representatividad_temporal::number DESC
```
Columna calculada que funcionó en select:
```
case(representatividad_temporal::number >= 75 AND tipo_de_estaci_n='Fija', 'CONFIABLE', representatividad_temporal::number >= 75, 'REP>=75 PERO INDICATIVA (aparte)', true, 'NO CONFIABLE (rep<75)') AS calidad
```
Tendencia agregada:
```
select = a_o, count(*) AS n, avg(promedio) AS prom, sum(d_as_de_excedencias) AS dias_exc, max(promedio) AS maxprom
where  = variable='PM2.5' AND a_o in (2023,2024,2025) AND tiempo_de_exposici_n_horas=24 AND id_estacion in (<25 ids>)
group  = a_o
```

Días > 25 con ≥ 18 h (g4t8-zkc3):
```
select = date_trunc_ymd(med_fecha_inicio::floating_timestamp) AS dia, estacion_id, count(*) AS h, avg(med_concentracion_estandar) AS prom
where  = estacion_id in ('29509','31371','29493','31369','32036') AND msfl_code='PM2.5' AND med_fecha_inicio >= '2025-01-01 00:00:00' AND med_fecha_inicio < '2026-01-01 00:00:00'
group  = dia, estacion_id
having = count(*) >= 18 AND avg(med_concentracion_estandar) > 25
```
Días incompletos: mismo query con `having count(*) < 18`. Días con dato por mes: `count(distinct date_trunc_ymd(med_fecha_inicio::floating_timestamp))` agrupando por `date_extract_m(...)` (funciona).

## Estaciones descartadas de los rankings y por qué

- Indicativa con rep >= 75 %: SAN ANTONIO (31977, Rionegro) — reportar aparte.
- Rep < 75 %: MED-ALTA2 (66), ITA-LGO (64, indicativa), ENV-COLS (55), LA DANTA 2024 (53, ind.), FER (52), GIR-TOT (48), GIR-SCLA (42), PARQ Yondó (20), DORADAL 2025 (13, ind.), GUATAPE2025 (13, ind.), JERUSALÉN 2024 (12, ind.), MARINILLA 2025 (12, ind.), GUARNE 2025 (11, ind.), ALCALDIA DE GUARNE 2024 (7, ind.), GUATAPÉ 2024 (7, ind.), HOSPITAL MARINILLA 2024 (4, ind.), LA CEJA (3, ind.).

## Próximos pasos (corrida 3: fases 5 y 6)

1. Fase 5 (H3): perfil horario 2025 (avg por `date_extract_hh(med_fecha_inicio::floating_timestamp)`, 24 filas por estación) de: TRÁFICO CENTRO (29509, tráfico centro de Medellín); una residencial del Valle de Aburrá — propuesta: CASA JUSTICIA (29493, Itagüí) o VILLAHERMOSA (31367, Medellín) (confirmar que el tipo/contexto no está en los datos y justificar la elección por nombre/ubicación); y SANTA ELENA (31855, menor promedio, 7,32). NO usar Jorge Eliécer ni Politécnico (sin datos horarios). Considerar excluir las ventanas de pólvora o al menos verificar que no cambian el perfil. Hora de pico y de mínimo; amplitud pico/mínimo.
2. Fase 6: informe `salidas/informe_aire_antioquia.md` (titular, resumen, H1–H3 con veredicto y cifras, ranking de fase 2, limitaciones, metodología, enlaces a los 4 CSV) y mapa `salidas/mapa_aire_antioquia.html` (Leaflet 1.9.4 de unpkg, OSM con atribución; 43 estaciones de `aire_estaciones_2025.csv`: color por promedio frente a 25, excluidas con borde punteado/gris; popup con datos; leyenda).
3. Opcional: comparación mensual con 2024 para H2 (días > 37 por mes en 2024 en las 5 top) si el presupuesto lo permite.
