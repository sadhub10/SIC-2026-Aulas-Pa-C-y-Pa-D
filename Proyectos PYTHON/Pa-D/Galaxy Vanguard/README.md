# Salario mínimo y costo de la alimentación en Panamá

Este proyecto compara el costo de la canasta básica de alimentos con el salario mínimo en la provincia de Panamá, en tres momentos: **2019** (antes de la pandemia), **2022** (después) y **2026** (el año en curso). La pregunta que guía el análisis es cuánto del salario mínimo se va en comida.

Cada número sale de una fuente oficial (INEC, ACODECO, MEF o Gaceta Oficial).

## Qué se analiza

1. **Inflación, canasta y salario.** Con el IPC del INEC se calcula la inflación de 2019, 2022 y 2026, y se muestra en una gráfica de tiempo (línea mensual) de la variación interanual, tanto del índice general como del grupo de alimentos. Se complementa con gráficas del aumento del costo de la canasta de ACODECO (en B/.) y del salario mínimo de la Región 1: una comparación del incremento porcentual 2019→2022→2026 y una gráfica que pone la canasta frente al salario. El costo mensual de la canasta del MEF se reporta en paralelo, sin mezclarlo con el de ACODECO.
2. **Salario mínimo.** Tasas de la Región 1 y de la Región 2 (comercio al por menor y trabajo doméstico) según los decretos vigentes en cada año.
3. **Poder adquisitivo.** Qué parte del salario de la Región 1 alcanza para pagar la canasta, y si la comida subió más que el salario.
4. **Supermercados.** Precio de los 59 productos por establecimiento.

## Consideraciones

- **ACODECO y MEF no se mezclan.** ACODECO es el costo de su canasta de 59 productos a precios de supermercado. El MEF es un costo calórico familiar (cantidades INCAP, precios del INEC). Van en paralelo.
- **El IPC de 2026 no se enlaza con 2019 y 2022.** Hasta agosto de 2025 la serie usa base 2013 = 100; desde septiembre de 2025 el INEC publica base 2024 = 100. La serie anterior se publica para el área urbana de la provincia (distritos que forman parte de la provincia de Panamá) y, en este proyecto, se trata como provincia de Panamá. No hay un factor oficial de enlace para esta geografía ni para el grupo de alimentos. Por eso la gráfica de tiempo usa la variación interanual en % (general y alimentos), que sí se puede comparar entre 2019, 2022 y 2026; los niveles del índice solo se grafican dentro de la misma base. El costo de la canasta, en balboas, sí se puede comparar en los tres años.
- **La canasta solo se cruza con la Región 1.** La Región 2 aparece únicamente en el bloque del salario, para mostrar la brecha entre regiones. El equivalente mensual de una tasa horaria es hora × 208 (48 h × 52 / 12). El doméstico usa el mensual que trae el decreto. En 2019 no existe la categoría “supermercados de 5 o más sucursales”.

## Estructura

```text
canasta-basica-salario/
├── README.md
├── requirements.txt
├── references/
│   ├── plan_datos.md          # fuentes, cifras de control y reglas de limpieza
│   └── guia_analisis.md       # cómo analizar las tablas de data/processed/
├── data/
│   ├── raw/                   # archivos tal cual salen de la fuente; no se editan
│   │   ├── acodeco/           # CSV 2019 y 2022, histórico y PDF de septiembre 2026
│   │   ├── inec/              # cuadros del IPC
│   │   ├── mef/               # informes mensuales 2019, 2022 y 2026
│   │   └── mitradel/          # gacetas de los tres decretos de salario
│   ├── interim/               # limpiezas a medias, todavía no para el análisis
│   └── processed/             # tablas tidy: ipc, costo_canasta_mensual, salario_minimo, precios_supermercados
├── notebooks/                 # 00 limpieza; 01 inflación; 02 salario mínimo; 03 poder adquisitivo; 04 supermercados
├── streamlit_app/             # reporte ejecutivo; se abre con Streamlit
├── src/                       # lectura y limpieza; los notebooks no parsean crudos
└── outputs/
    └── figures/
        ├── inflacion_interanual.png          # variación interanual del IPC, general y alimentos (línea mensual)
        ├── aumento_canasta_salario.png       # incremento % 2019→2022→2026 de la canasta (ACODECO) y del salario (Región 1)
        └── canasta_vs_salario.png            # costo de la canasta (B/.) frente al salario mínimo de la Región 1
```

## Configuración

Hace falta Python 3.12 o superior.

```bash
cd canasta-basica-salario
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

En Windows, el activate es `.venv\Scripts\activate`.

Para abrir los notebooks con este entorno:

```bash
python -m ipykernel install --user --name canasta-vs-salario --display-name "Canasta vs salario"
jupyter lab
```

Para abrir el reporte, desde la raíz y con el entorno activado:

```bash
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/app.py
```

Streamlit abre http://localhost:8501. El reporte lee `data/processed/` y las tablas de `outputs/tablas/` que escriben los notebooks `03` y `04`.

Dependencias: `pandas`, `openpyxl` y `xlrd` (Excel del INEC), `pdfplumber` (PDF de ACODECO y del MEF), `matplotlib`, `jupyter`, `requests` y `lxml`.

Las gacetas del salario están escaneadas. `pdfplumber` no extrae el texto. Hay que transcribir las tasas ya verificadas en `references/plan_datos.md` (o usar OCR con `tesseract -l spa`, que no forma parte de `requirements.txt`) y dejarlas en `src/`, sin recalcularlas desde un OCR sucio.

## Cómo trabajar

1. No editar nada dentro de `data/raw/`.
2. La lectura de cada fuente vive en `src/` (`io_inec.py`, `io_acodeco.py`, `io_mef.py`, `io_salarios.py`, más `limpieza.py`).
3. El notebook `00` llama a ese código, corre los controles de calidad y escribe `data/processed/`.
4. Los notebooks `01` a `04` solo leen `data/processed/` y guardan figuras en `outputs/figures/`. El notebook `01` (inflación) produce las tres figuras de la gráfica de tiempo, del incremento porcentual y de la canasta frente al salario.

Controles mínimos antes de graficar: 59 productos por mes en los CSV, precios faltantes en `NaN` (nunca en 0), series de costo con los meses que realmente trae cada fuente, ningún gráfico de niveles del IPC que mezcle base 2013 = 100 con base 2024 = 100, y la gráfica de tiempo de inflación construida con la variación interanual, no con niveles encadenados de bases distintas.

Los CSV de ACODECO vienen en **latin-1**, no en UTF-8. El separador cambia entre coma y punto y coma, y algunos meses traen filas de cabecera vacías, columnas de índice o un pie (`Costo Total`, `FUENTE:`).

## Fuentes

| Bloque | Institución | Qué aporta |
|---|---|---|
| IPC e inflación | [INEC](https://www.inec.gob.pa/) | Índices de la provincia de Panamá (base 2013 hasta agosto de 2025; base 2024 desde septiembre de 2025) y la variación interanual que ya publica el INEC |
| Canasta en supermercados | [ACODECO](https://www.acodeco.gob.pa/) y [datos abiertos](https://www.datosabiertos.gob.pa/) | Costo total histórico y precios por establecimiento |
| Costo calórico | [MEF, canasta básica](https://www.mef.gob.pa/canasta-basica/) | Costo familiar en la provincia de Panamá |
| Salario mínimo | [Gaceta Oficial](https://www.gacetaoficial.gob.pa/) | Decreto Ejecutivo 75 de 2017, 74 de 2021 y 13 de 2025 |