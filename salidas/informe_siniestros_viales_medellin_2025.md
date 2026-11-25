# Siniestros viales en Medellín por mes (2025) y hora más peligrosa

*Fecha de consulta: 24 de noviembre de 2026*

## Resumen ejecutivo

- **No se pudo calcular el número de siniestros por mes ni la hora más peligrosa.** La base oficial de la Alcaldía de Medellín ("Incidentes viales", `9wqu-juqb`) es la única que tiene incidentes con su hora, pero en datos.gov.co está publicada como un enlace externo y la plataforma no deja consultarla (error 403, "non-tabular"). Ninguna otra fuente consultable trae la hora del hecho para Medellín.
- Como aproximación se usan las **víctimas** del último año completo, **2025**, que registran la Policía y MinDefensa: **2.705 lesionados** y **505 fallecidos** en Medellín. Son personas afectadas, no siniestros.
- Entre enero y septiembre se registraron unos 276 lesionados al mes. Julio fue el mes más alto (341). Los fallecidos más altos fueron marzo (55) y agosto (51).
- Los lesionados de **octubre a diciembre caen con fuerza (114, 80 y 28)**. La misma caída se ve al cierre de 2024 y en los últimos meses de 2026, así que lo más probable es que sean registros incompletos y no una mejora real.
- No hay datos por hora. Por día de la semana, el **sábado** concentra la mayor cantidad de lesionados (457; 16,9 %).

## Cifras clave (Medellín, 2025)

| Mes 2025 | Lesionados (MinDefensa) | Fallecidos (Policía – DIJIN) | Total víctimas |
|---|---:|---:|---:|
| Enero | 224 | 39 | 263 |
| Febrero | 238 | 36 | 274 |
| Marzo | 295 | **55** | 350 |
| Abril | 302 | 44 | 346 |
| Mayo | 300 | 38 | 338 |
| Junio | 259 | 42 | 301 |
| Julio | **341** | 37 | **378** |
| Agosto | 277 | 51 | 328 |
| Septiembre | 247 | 36 | 283 |
| Octubre ⚠ | 114 | 44 | 158 |
| Noviembre ⚠ | 80 | 44 | 124 |
| Diciembre ⚠ | 28 | 39 | 67 |
| **Total** | **2.705** | **505** | **3.210** |

⚠ = registro de lesionados probablemente incompleto (ver hallazgo 2).

Lesionados por día de la semana (2025):

| Día | Lesionados | % |
|---|---:|---:|
| Sábado | **457** | 16,9 % |
| Domingo | 396 | 14,6 % |
| Martes | 384 | 14,2 % |
| Jueves | 383 | 14,2 % |
| Miércoles | 375 | 13,9 % |
| Lunes | 365 | 13,5 % |
| Viernes | 345 | 12,8 % |

## Hallazgos

1. **No es posible responder "cuál es la hora más peligrosa" con los datos consultables.** La hora aparece en las bases de la Secretaría de Movilidad de Medellín ("Incidentes viales" `9wqu-juqb`, "Víctimas en incidentes viales" `bkec-fpy9` e "Incidentes viales con motos" `6v9g-zujz`). En datos.gov.co las tres están publicadas como enlaces o archivos externos, y la API respondió *"no row or column access to non-tabular tables"*. Además, su última actualización fue el 5 de agosto de 2025. Para obtener la hora hay que descargar esos archivos desde el portal MEData de la Alcaldía.
2. **El último trimestre de cada año aparece con muchos menos registros.** En los lesionados de MinDefensa, septiembre a diciembre de 2024 suman 154, 131, 84 y 26. Octubre a diciembre de 2025 suman 114, 80 y 28, frente a un promedio de 276 al mes entre enero y septiembre de 2025. En 2026 la caída empieza antes (junio: 181; octubre: 40). Que el patrón se repita y que 2024 siga igual de bajo un año después sugiere un problema en cómo se registran o consolidan los datos, no una baja real en la siniestralidad. Hay que revisarlo con la fuente. **Estos meses no deben leerse como una mejora.**
3. **Los fallecidos no muestran esa caída al cierre del año.** Se mantienen entre 36 y 55 al mes durante 2025, unos 42 en promedio. Los picos de marzo (55) y agosto (51) son variaciones mensuales; los datos no permiten atribuirlas a ninguna causa.
4. **El sábado es el día con más lesionados** (457, frente a 345 del viernes, el más bajo). Es un patrón descriptivo. Como en el último trimestre faltan registros, el reparto podría cambiar un poco con datos completos.
5. **La base del RUNT (vehículos involucrados) no sirve para 2025 en Medellín.** Entre enero de 2022 y octubre de 2024 registra entre 1.352 y 4.280 vehículos al mes en siniestros con heridos. Desde noviembre de 2024 cae a menos de 60 al mes (por ejemplo, 28 vehículos con heridos en enero de 2025). Eso indica que Medellín dejó de reportar o se reportó de forma parcial al RNAT. Julio de 2024 tiene un valor atípico de **22.658** vehículos con heridos, unas 9 veces lo normal, y queda **a revisar** como posible error de digitación o carga.

## Fuente y metodología

| Dataset | ID | Publica | Uso |
|---|---|---|---|
| Lesiones accidentes de tránsito | `ntej-qq7v` – https://www.datos.gov.co/d/ntej-qq7v | Ministerio de Defensa Nacional (actualizado 17/11/2026) | Lesionados por mes y día de la semana (filtro `cod_muni = '05001'`) |
| Homicidios accidente de tránsito Policía Nacional | `ha6j-pa2r` – https://www.datos.gov.co/d/ha6j-pa2r | DIJIN – Policía Nacional (actualizado 01/09/2026; datos hasta 31/07/2026) | Fallecidos por mes (filtro `codigo_dane like '05001%'`, Medellín (CT)) |
| Vehículos involucrados en un accidente de tránsito – Ley 2251 de 2022 | `6jmc-vaxk` – https://www.datos.gov.co/d/6jmc-vaxk | Ministerio de Transporte / RUNT (actualizado 04/09/2026) | Revisión de cobertura; no se usó para las cifras de 2025 |
| Incidentes viales (Medellín) | `9wqu-juqb` – https://www.datos.gov.co/d/9wqu-juqb | Secretaría de Movilidad de Medellín | No se pudo consultar (enlace externo, no tabular) |

**Método:** se tomó 2025 como el último año completo, porque 2026 va hasta octubre en MinDefensa y hasta julio en la Policía. Los lesionados se sumaron con el campo `cantidad` y se agruparon por mes y por día de la semana; los fallecidos, con `cantidad` por mes. Todas las cifras salen de consultas SoQL hechas el 24/11/2026.

**Limitaciones:**
- Las cifras cuentan **víctimas, no siniestros**. Un siniestro puede tener varias víctimas o ninguna (por ejemplo, los de solo daños, que no aparecen en ninguna de estas fuentes). No se debe leer "3.210 víctimas" como "3.210 siniestros".
- Las fuentes son registros de la Policía y MinDefensa. No coinciden necesariamente con las cifras oficiales de la Secretaría de Movilidad de Medellín ni con las de Medicina Legal, que suelen ser mayores.
- No existe la variable hora en ninguna fuente consultable, así que la hora más peligrosa **no se calculó**.
- Los lesionados de octubre a diciembre de 2025 parecen incompletos. Los totales anuales probablemente se quedan cortos.
- No se suman las dos fuentes como si fueran un solo registro: vienen de sistemas distintos y podrían solaparse.
- El análisis es exploratorio y descriptivo: no establece causas.

## Archivos de soporte (carpeta `salidas/`)

- `medellin_lesionados_transito_mensual_2024_2026.csv`: lesionados por mes, de enero de 2024 a octubre de 2026, con los días que tienen registro.
- `medellin_fallecidos_transito_mensual_2025.csv`: fallecidos por mes en 2025.
- `medellin_lesionados_transito_dia_semana_2025.csv`: lesionados por día de la semana en 2025 (0 = domingo … 6 = sábado).
- `medellin_vehiculos_runt_mensual_2022_2026.csv`: vehículos involucrados por mes y gravedad según el RUNT, que muestra el corte de reporte desde noviembre de 2024.
