# AquaLytics

Evaluación descriptiva y parcial de la calidad del agua con Python. Proyecto de Ricardo Vasquez (líder y desarrollador), Mario Aranda, Juan Aranda y Keysi Martinez (desarrolladores), para Samsung Innovation Campus.

El sistema limpia los dos archivos adjuntos, reconstruye las mediciones compatibles desde el archivo original, identifica excedencias y muestra resultados mediante ocho gráficos y un panel HTML con filtros. **No aplica regresión lineal, no entrena modelos y no certifica potabilidad.** La propuesta plantea análisis descriptivo y deja la predicción para una fase posterior; no hay etiquetas independientes de potabilidad para validar un clasificador.

## Ejecución

Se recomienda Python 3.11 o 3.12. Extraer el ZIP completo y abrir una terminal en la carpeta `AquaLytics`.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux o macOS:
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

`python main.py --sin-abrir` vuelve a generar todo sin abrir el navegador. Las rutas se resuelven desde el archivo del proyecto, no desde el directorio de la terminal.

**Panel:** al ejecutar `main.py` se genera `resultados/Panel_AquaLytics.html`, que se abre en el navegador. Es autónomo, contiene sus gráficos y datos, y funciona sin conexión. Permite filtrar por organismo, estación, fechas, estado y calidad de resultados, explorar parámetros y descargar la selección en CSV. Las ocho figuras completas están en una sección desplegable.

## Datos y unidad de análisis

`resultphyschem.zip` contiene 3,911 filas y 81 columnas en formato largo. Los identificadores corresponden a USGS Georgia y NPS de Estados Unidos; no son datos de Panamá. Las fechas van del 27 de enero de 2020 al 30 de septiembre de 2024. El CSV pivoteado contiene 369 combinaciones de estación y fecha y se usa como fuente de auditoría; no se concatena con el original porque produciría doble conteo.

La unidad principal es la combinación **organismo + identificador de actividad**. Quedan 364 actividades y 102 estaciones tras separar los controles de calidad. Una actividad de campo y una muestra de laboratorio del mismo sitio y día pueden conservarse por separado; no se inventa que sean la misma muestra física. Las medianas por actividad se usan para explorar; la evaluación revisa cada resultado original y conserva cualquier excedencia.

## Limpieza aplicada

1. Se conservan los originales y se registran sus SHA-256. Se revisan duplicados exactos, cadenas vacías, números, fechas e identificadores. No se encontraron duplicados exactos en el original.
2. Se separan 496 filas de controles, réplicas y materiales de referencia. No se consideran observaciones ambientales independientes.
3. Se normalizan nombres y unidades. `mg/l` y `mg/L` se reconocen como equivalentes. El pH sin unidad explícita se admite como magnitud adimensional y se marca su inferencia. La conductividad conserva en la tabla larga la distinción de compensación a 25 °C.
4. Se emplean SDT reportados directamente en mg/L; las 62 mediciones en toneladas/acre-pie se excluyen para evitar mezclar representaciones del mismo parámetro. No se convierten ni se promedian con mg/L. La saturación de oxígeno (%) se excluye de la concentración en mg/L. La turbidez FNU y NTRU permanece en columnas separadas; no se convierte a UNT.
5. No se sustituyen resultados no detectados, detectados no cuantificados o no reportados por cero, el límite de detección o una media. Se mantienen sus metadatos y se dejan sin valor evaluable. No se imputa ningún faltante para decidir excedencias.
6. Se rechazan concentraciones negativas y pH fuera de 0–14 si aparecen. Los atípicos estadísticos se señalan con 1.5 veces el intervalo intercuartílico por organismo y parámetro, con al menos ocho observaciones, y se conservan. No se confunde un valor extremo ambiental con un error.
7. Se conservan el estado preliminar, el tipo estimado, la fracción de muestra, los métodos y calificadores del origen. Se incluye un análisis de sensibilidad con resultados aceptados/finales y no estimados.

`mediciones_auditadas.csv` conserva las 81 columnas originales más los campos de trazabilidad. `registros_no_utilizados.csv` contiene parámetros fuera del alcance, unidades incompatibles y resultados censurados; no todos son datos incorrectos. Los controles se identifican en su propio CSV y mediante `es_control`. Hay 1,900 observaciones válidas dentro del alcance y fuera de controles.

## Evaluación de referencia

Se implementan las tablas 2 y 3 de la página 2 de la Resolución 122 del 16 de julio de 2021, que modifica DGNTI-COPANIT 21-2019. Las reglas están en `limites.json`. No se aplican los valores excepcionales de emergencia.

| Parámetro | Referencia de comparación |
|---|---:|
| pH | 6.5–8.5 inclusive |
| Conductividad | ≤850 µS/cm |
| Cloruros | ≤250 mg/L |
| Fluoruros | ≤0.8 mg/L |
| Sulfatos | ≤250 mg/L |
| Dureza | ≤200 mg/L CaCO3 |
| Sólidos disueltos totales | ≤500 mg/L |

Las concentraciones de fracción disuelta sirven como comparación orientativa y no prueban cumplimiento de una medición total. `evaluacion_por_parametro.csv` detalla las fracciones y los valores mínimos y máximos por actividad. Tampoco se presenta toda conductividad como método plenamente homologado al de la norma: la compensación y el método deben comprobarse para una evaluación regulatoria.

Las guías OMS se usan para interpretar la diferencia entre criterios sanitarios y operativos o de aceptabilidad. No se inventa un límite sanitario OMS para pH, dureza, oxígeno disuelto o SDT. El perfil OMS no se usa como un segundo clasificador automático.

La turbidez normativa es ≤1 UNT y el cloro residual libre es 0.3–1.5 mg/L en la modificación de 2021. No se evalúan: falta equivalencia de método/unidad para la turbidez y no hay mediciones de cloro residual. Faltan microbiología y otros contaminantes requeridos. **No es posible determinar potabilidad con estos archivos.** Aplicar las referencias a aguas ambientales estadounidenses es una demostración educativa y no una declaración de infracción regulatoria.

## Resultados obtenidos

| Resultado por actividad | Cantidad |
|---|---:|
| Con una o más excedencias | 174 |
| Sin excedencias en los parámetros observados | 170 |
| Sin datos evaluables del perfil | 20 |
| Total | 364 |

La cobertura mediana es 28.57%, equivalente a dos de siete parámetros. Ninguna de las tres categorías equivale a “agua potable”.

| Parámetro | Actividades fuera / evaluables | Porcentaje |
|---|---:|---:|
| Cloruros | 102 / 267 | 38.20% |
| Conductividad | 122 / 341 | 35.78% |
| pH | 46 / 155 | 29.68% |
| Dureza | 2 / 72 | 2.78% |
| Fluoruros | 0 / 68 | 0.00% |
| Sulfatos | 0 / 81 | 0.00% |
| SDT | 0 / 53 | 0.00% |

Los denominadores varían por disponibilidad. Los porcentajes no se suman porque una actividad puede exceder varios parámetros. Las 174 actividades con excedencias representan el 47.80% de las 364 actividades; esto no es una tasa poblacional de agua no potable.

Hay 178 actividades que contienen resultados preliminares y 82 con resultados estimados. Al recalcular usando sólo resultados aceptados/finales y no estimados quedan 206 actividades: 79 con excedencias, 107 sin excedencias observadas y 20 sin datos evaluables. Cambian tanto la información como el universo de actividades; no se interpreta como mejora temporal de calidad.

La correlación de Spearman entre conductividad y cloruros es 0.929 con 264 pares. Es una asociación del conjunto disponible, sensible a la mezcla de sitios y organismos; no demuestra causalidad ni predice potabilidad. Se publican la matriz de coeficientes y la matriz de tamaños por par; se exige al menos 20 pares y no se calculan p-valores ni inferencias de independencia entre observaciones repetidas.

## Auditoría del CSV adjunto

La comparación por estación y fecha detecta 292 celdas distintas respecto de la reconstrucción que excluye controles y unidades incompatibles: 89 de oxígeno y 62 de SDT, entre otras. Las diferencias también reflejan separación de réplicas y política de agregación; no todas son errores de unidades. El detalle está en `diferencias_pivote_adjunto.csv`. La auditoría usa media por estación y fecha para aproximar la estructura del adjunto; el análisis principal conserva actividades y usa medianas sólo para descripción.

## Archivos entregados

| Ruta | Contenido |
|---|---|
| `analisis.py`, `panel.py`, `main.py` | Código del proceso y panel |
| `limites.json` | Configuración verificable de referencias |
| `datos/originales/` | Los dos datasets adjuntos sin alteración |
| `datos/procesados/` | Tablas limpias, trazabilidad y sensibilidad |
| `resultados/Panel_AquaLytics.html` | Panel autónomo con filtros y exportación |
| `resultados/graficos/` | Ocho visualizaciones PNG |
| `resultados/` | Estadísticas, correlaciones, tamaños de pares e indicadores |

El video y la carga en el repositorio oficial del programa deben realizarse con los medios y el destino del equipo. No se han inventado enlaces GitHub ni grabaciones.

## Validación y métricas

El tiempo registrado en `indicadores.json` mide carga, limpieza, evaluación, exportación y sensibilidad en este equipo; excluye las figuras y el panel. No se realizó una comparación manual cronometrada, por lo que no se afirma un ahorro porcentual. Sin etiquetas externas y validación de laboratorio no se informa exactitud de potabilidad.

## Referencias

- MICI (2019). DGNTI-COPANIT 21-2019. https://asep.gob.pa/wp-content/uploads/agua/legislacion/dgnti_21-2019.pdf
- MICI (2021). Resolución 122 del 16 de julio de 2021, página 2, tablas 2 y 3. https://asep.gob.pa/wp-content/uploads/agua/legislacion/dgnti_21-2019_mod.pdf
- OMS (2026). Guidelines for drinking-water quality, fourth edition incorporating the first, second and third addenda. https://www.who.int/publications/i/item/9789240121225
- OMS (2026). Capítulo 10, Acceptability aspects. https://cdn.who.int/media/docs/default-source/wash-documents/water-safety-and-quality/dwq-guidelines-4/gdwq_4ed_with_third-addenda_acceptability-aspects.pdf
- Archivos suministrados por el equipo: `resultphyschem.zip` y `tabla_calidad_agua_pivoteada.csv`. La URL y los filtros de la consulta original no están incluidos, por lo que se conservan los metadatos y hashes como trazabilidad disponible.
