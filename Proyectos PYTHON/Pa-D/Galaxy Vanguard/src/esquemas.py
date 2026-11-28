"""Columnas canónicas de las tablas tidy y validaciones simples.

Las cuatro tablas salen de la sección 3.1 de references/plan_datos.md.
`ipc.notas` guarda la variación interanual oficial cuando el INEC la publica
(octubre 2026). `precios_supermercados.quincena` solo aplica al PDF de 2026.
"""

from __future__ import annotations

import pandas as pd

COLUMNAS: dict[str, list[str]] = {
    "ipc": [
        "fecha",
        "anio",
        "mes",
        "geografia",
        "grupo",
        "indice",
        "base",
        "fuente",
        "notas",
    ],
    "costo_canasta_mensual": [
        "fecha",
        "anio",
        "mes",
        "fuente",
        "geografia",
        "n_productos",
        "costo_total",
        "notas",
    ],
    "salario_minimo": [
        "fecha_inicio",
        "anio_analisis",
        "decreto",
        "region",
        "actividad",
        "categoria",
        "salario_hora",
        "salario_mensual",
        "es_oficial_mensual",
        "categoria_existia",
    ],
    "precios_supermercados": [
        "fecha",
        "anio",
        "mes",
        "quincena",
        "producto",
        "producto_estandar",
        "medida",
        "establecimiento",
        "establecimiento_estandar",
        "cadena",
        "zona",
        "precio",
        "control_precio",
        "fuente",
    ],
}

# precio puede ser NaN. indice y costo_total no.
COLUMNAS_NUMERICAS: dict[str, list[str]] = {
    "ipc": ["indice"],
    "costo_canasta_mensual": ["n_productos", "costo_total"],
    "salario_minimo": ["salario_hora", "salario_mensual"],
    "precios_supermercados": ["precio"],
}

COLUMNAS_SIN_NULO: dict[str, list[str]] = {
    "ipc": ["fecha", "anio", "mes", "geografia", "grupo", "indice", "base", "fuente"],
    "costo_canasta_mensual": [
        "fecha",
        "anio",
        "mes",
        "fuente",
        "geografia",
        "n_productos",
        "costo_total",
    ],
    "salario_minimo": [
        "fecha_inicio",
        "anio_analisis",
        "decreto",
        "region",
        "actividad",
        "categoria",
        "salario_mensual",
        "es_oficial_mensual",
        "categoria_existia",
    ],
    "precios_supermercados": [
        "fecha",
        "anio",
        "mes",
        "producto",
        "producto_estandar",
        "establecimiento",
        "zona",
        "control_precio",
        "fuente",
    ],
}

VALORES: dict[str, dict[str, set[str]]] = {
    "ipc": {
        "geografia": {"panama_y_san_miguelito", "provincia_de_panama"},
        "grupo": {"total", "alimentos_y_bebidas_no_alcoholicas"},
        "base": {"2013=100", "2024=100"},
    },
    "costo_canasta_mensual": {
        "fuente": {"acodeco_historico", "mef_cbfa"},
        "geografia": {"provincia_de_panama", "panama_y_san_miguelito"},
    },
    "salario_minimo": {
        "region": {"1", "2"},
        "actividad": {"comercio_al_por_menor", "trabajo_domestico"},
        "categoria": {"pequena", "gran_empresa", "supermercados_5_plus", "domestico"},
        "decreto": {"DE 75/2017", "DE 74/2021", "DE 13/2025"},
    },
    "precios_supermercados": {
        "zona": {"capital", "san_miguelito", "sin_clasificar"},
        "fuente": {"acodeco_csv", "acodeco_pdf_sep2026"},
    },
}


def columnas(tabla: str) -> list[str]:
    if tabla not in COLUMNAS:
        raise KeyError(f"Tabla desconocida: {tabla}")
    return list(COLUMNAS[tabla])


def validar(df: pd.DataFrame, tabla: str) -> pd.DataFrame:
    """Falla si falta una columna canónica o si un monto no es numérico.

    `precio` y `salario_hora` aceptan NaN. Un índice o un costo total vacío
    sí es un error. No reordena ni rellena: solo revisa.
    """
    esperadas = columnas(tabla)
    faltan = [col for col in esperadas if col not in df.columns]
    if faltan:
        raise ValueError(f"{tabla}: faltan columnas {faltan}")

    for col in COLUMNAS_NUMERICAS[tabla]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"{tabla}.{col} no es numérica (dtype={df[col].dtype})")

    for col in COLUMNAS_SIN_NULO[tabla]:
        if df[col].isna().any():
            raise ValueError(f"{tabla}.{col} tiene valores vacíos")

    for col, permitidos in VALORES[tabla].items():
        encontrados = set(df[col].dropna().astype(str))
        ajenos = encontrados - permitidos
        if ajenos:
            raise ValueError(f"{tabla}.{col} tiene valores fuera del esquema: {sorted(ajenos)}")

    return df
