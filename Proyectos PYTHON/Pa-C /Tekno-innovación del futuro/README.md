# CanastaData 🇵🇦

## Sistema de Análisis de la Evolución de la Canasta Básica y el Poder Adquisitivo en Panamá (2020-2025)

## Introducción

CanastaData es un proyecto desarrollado en Python que tiene como
finalidad analizar la evolución del costo de la Canasta Básica Familiar
de Alimentos en Panamá durante el periodo 2020-2025, considerando los
cambios económicos ocurridos antes, durante y después de la pandemia de
COVID-19.

El sistema permitirá procesar y comparar datos históricos relacionados
con los precios de los productos que conforman la canasta básica y los
salarios de los trabajadores panameños, con el propósito de identificar
variaciones en los costos de los alimentos y evaluar cómo estos cambios
se relacionan con la capacidad adquisitiva de la población.

Mediante herramientas de análisis y visualización de datos, se busca
generar información que facilite la comprensión de la situación
económica de los hogares panameños y permita evaluar la actualidad de la
composición de la canasta básica.

## Nombre del equipo

[Tekno - innovación del futuro](#nombre-del-equipo)

## Integrantes del equipo

-   \[Solin Rodriguez\]
-   \[Katherine Guevara\]
-   \[Jose De Bello\]
-   \[Arquimedes Moran\]
-   \[Jhan Sanchez\]

## Objetivo general

Desarrollar un sistema de análisis de datos en Python que permita
estudiar la evolución del costo de la canasta básica en Panamá entre
2020 y 2025, relacionándolo con los cambios salariales para evaluar su
impacto en la capacidad adquisitiva de la población.

## Estructura del proyecto

``` text
Proyecto_Canasta_Basica/
│
├── README.md
│
├── datos/
│   ├── originales/
│   │   ├── canasta_basica.csv
│   │   ├── salario_2019_2023.csv
│   │   └── salario_2021_2025.csv
│   │
│   └── procesados/
│       ├── categorias.csv
│       ├── productos.csv
│       ├── total.csv
│       └── salarios.csv
│
├── notebooks/
│   ├── 01_limpieza/
│   │   ├── 01_canasta_basica/
│   │   │   └── canasta_limpieza.ipynb
│   │   │
│   │   └── 02_salarios/
│   │       └── salarios_limpieza.ipynb
│   │
│   └── 02_analisis/
|
│
├── resultados/
|
│
├── dashboard/
│
├── material_adicional/
│
└── requirements.txt
```

## Tecnologías y herramientas

-   **Python:** lenguaje de programación.
-   **Pandas:** procesamiento y análisis de datos.
-   **NumPy:** operaciones numéricas.
-   **Matplotlib:** creación de gráficos y visualizaciones.

## Fuentes de datos

-   **Ministerio de Economía y Finanzas (MEF):** información histórica
    de la Canasta Básica Familiar de Alimentos.
    https://www.mef.gob.pa/canasta-basica/
-   **Instituto Nacional de Estadística y Censo (INEC):** información
    estadística sobre ingresos y salarios.
    https://www.inec.gob.pa/Publicaciones/Default3.aspx?ID_PUBLICACION=1279&ID_CATEGORIA=5&ID_SUBCATEGORIA=39
    https://www.inec.gob.pa/Publicaciones/Default3.aspx?ID_PUBLICACION=1417&ID_CATEGORIA=5&ID_SUBCATEGORIA=39
    

## Resultados esperados

-   Identificación de las variaciones en el costo de la canasta básica.
-   Comparación de precios de los productos a través del tiempo.
-   Análisis de la evolución de los salarios.
-   Evaluación de la relación entre el costo de la canasta y los
    ingresos.
-   Visualización de los resultados mediante gráficos y tablas.

## Estado del proyecto

En desarrollo.
