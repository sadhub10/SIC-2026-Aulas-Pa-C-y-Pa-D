"""Salario mínimo de comercio al por menor y de trabajo doméstico.

Las gacetas están escaneadas, así que esta tabla no se lee del PDF. Las tasas
son las ya verificadas en references/plan_datos.md, sección 1.4. El mensual del
comercio es hora × 208; el del doméstico es el monto oficial del decreto.
En 2019 el decreto no trae supermercados de 5 o más sucursales, y esa fila no
se inventa.
"""

from __future__ import annotations

import pandas as pd

from esquemas import validar

_HORAS_MES = 208

# anio, decreto, fecha_inicio, region, categoria, salario_hora
_COMERCIO = [
    (2019, "DE 75/2017", "2018-01-01", "1", "pequena", 2.20),
    (2019, "DE 75/2017", "2018-01-01", "1", "gran_empresa", 2.72),
    (2019, "DE 75/2017", "2018-01-01", "2", "pequena", 1.84),
    (2019, "DE 75/2017", "2018-01-01", "2", "gran_empresa", 2.23),
    (2022, "DE 74/2021", "2022-01-16", "1", "pequena", 2.27),
    (2022, "DE 74/2021", "2022-01-16", "1", "gran_empresa", 2.81),
    (2022, "DE 74/2021", "2022-01-16", "1", "supermercados_5_plus", 2.88),
    (2022, "DE 74/2021", "2022-01-16", "2", "pequena", 1.90),
    (2022, "DE 74/2021", "2022-01-16", "2", "gran_empresa", 2.30),
    (2022, "DE 74/2021", "2022-01-16", "2", "supermercados_5_plus", 2.36),
    (2026, "DE 13/2025", "2026-01-16", "1", "pequena", 2.37),
    (2026, "DE 13/2025", "2026-01-16", "1", "gran_empresa", 3.02),
    (2026, "DE 13/2025", "2026-01-16", "1", "supermercados_5_plus", 3.09),
    (2026, "DE 13/2025", "2026-01-16", "2", "pequena", 1.99),
    (2026, "DE 13/2025", "2026-01-16", "2", "gran_empresa", 2.48),
    (2026, "DE 13/2025", "2026-01-16", "2", "supermercados_5_plus", 2.54),
]

# anio, decreto, fecha_inicio, region, salario_mensual oficial
_DOMESTICO = [
    (2019, "DE 75/2017", "2018-01-01", "1", 275),
    (2019, "DE 75/2017", "2018-01-01", "2", 250),
    (2022, "DE 74/2021", "2022-01-16", "1", 315),
    (2022, "DE 74/2021", "2022-01-16", "2", 290),
    (2026, "DE 13/2025", "2026-01-16", "1", 350),
    (2026, "DE 13/2025", "2026-01-16", "2", 320),
]


def leer_salarios() -> pd.DataFrame:
    """Una fila por decreto, región y categoría que sí existía."""
    filas = []
    for anio, decreto, fecha, region, categoria, hora in _COMERCIO:
        filas.append(
            {
                "fecha_inicio": pd.Timestamp(fecha),
                "anio_analisis": anio,
                "decreto": decreto,
                "region": region,
                "actividad": "comercio_al_por_menor",
                "categoria": categoria,
                "salario_hora": hora,
                "salario_mensual": round(hora * _HORAS_MES, 2),
                "es_oficial_mensual": False,
                "categoria_existia": True,
            }
        )
    for anio, decreto, fecha, region, mensual in _DOMESTICO:
        filas.append(
            {
                "fecha_inicio": pd.Timestamp(fecha),
                "anio_analisis": anio,
                "decreto": decreto,
                "region": region,
                "actividad": "trabajo_domestico",
                "categoria": "domestico",
                "salario_hora": pd.NA,
                "salario_mensual": float(mensual),
                "es_oficial_mensual": True,
                "categoria_existia": True,
            }
        )
    salario = pd.DataFrame(filas)
    salario["salario_hora"] = pd.to_numeric(salario["salario_hora"])
    if salario.duplicated(["anio_analisis", "region", "actividad", "categoria"]).any():
        raise ValueError("Hay dos tasas para la misma categoría y año")
    if ((salario["anio_analisis"] == 2019) & (salario["categoria"] == "supermercados_5_plus")).any():
        raise ValueError("El decreto de 2017 no trae supermercados de 5 o más sucursales")
    muestra = salario.loc[
        (salario["anio_analisis"] == 2022)
        & (salario["region"] == "1")
        & (salario["categoria"] == "gran_empresa"),
        "salario_mensual",
    ]
    if muestra.empty or abs(float(muestra.iloc[0]) - 584.48) > 0.001:
        raise ValueError(f"2022 R1 gran empresa debía ser 584.48 y es {muestra.tolist()}")
    if len(salario) != 22:
        raise ValueError(f"Se esperaban 22 filas y hay {len(salario)}")
    return validar(salario, "salario_minimo")
