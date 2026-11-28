"""Cifras del reporte, tomadas del corte que ya usa el análisis."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.consulta_ipc_canasta import cargar_datos, corte_junio

TABLAS = ROOT / "outputs" / "tablas"
# Los mismos seis grupos que grafica el notebook 04.
_CADENAS = {
    "Xtra": "Xtra",
    "Machetazo": "El Machetazo",
    "Super 99": "Super 99",
    "Rey": "Rey",
    "Riba Smith": "Riba Smith",
    "minisúper": "Minisúper",
}


def cargar_corte() -> pd.DataFrame:
    """Junio, ACODECO y MEF por separado, salario de gran empresa en la Región 1."""
    _ipc, costo, salario = cargar_datos(ROOT / "data" / "processed")
    corte = corte_junio(costo, salario).copy()
    horas = salario.loc[
        salario["region"].eq(1)
        & salario["actividad"].eq("comercio_al_por_menor")
        & salario["categoria"].eq("gran_empresa"),
        ["anio_analisis", "salario_hora"],
    ].rename(columns={"anio_analisis": "anio"})
    corte = corte.merge(horas, on="anio", how="left")
    if corte["salario_hora"].isna().any():
        raise ValueError("Falta la tasa horaria de gran empresa, Región 1")
    base_mef = float(corte.loc[corte["anio"].eq(2019), "mef_cbfa"].iloc[0])
    corte["var_mef_pct"] = (corte["mef_cbfa"] / base_mef - 1) * 100
    return corte.sort_values("anio").reset_index(drop=True)


def _fila(corte: pd.DataFrame, anio: int) -> pd.Series:
    return corte.loc[corte["anio"].eq(anio)].iloc[0]


def _variacion(nuevo: float, anterior: float) -> float:
    return (nuevo / anterior - 1) * 100


def horas_junio() -> pd.DataFrame:
    """Horas publicadas por el notebook 03, corte de junio."""
    tabla = pd.read_csv(TABLAS / "03_poder_adquisitivo.csv")
    junio = tabla.loc[tabla["mes"].eq(6), ["fuente", "anio", "horas_para_pagar"]].copy()
    if junio["anio"].nunique() != 3 or set(junio["fuente"]) != {"acodeco_historico", "mef_cbfa"}:
        raise ValueError("La tabla de poder adquisitivo no trae junio de 2019, 2022 y 2026")
    return junio


def cadenas() -> pd.DataFrame:
    """Índice y costo estimado que ya escribió el notebook 04."""
    indice = pd.read_csv(TABLAS / "04_supermercados_tablas" / "supermercados_indice_cadena.csv")
    costo = pd.read_csv(
        TABLAS / "04_supermercados_tablas" / "supermercados_costo_estimado.csv",
        index_col=0,
    )
    filas = []
    for grupo, nombre in _CADENAS.items():
        fila = indice.loc[indice["grupo"].eq(grupo)]
        if fila.empty or nombre not in costo.index:
            raise ValueError(f"Falta {grupo} en las tablas de supermercados")
        filas.append(
            {
                "grupo": nombre,
                "indice": float(fila["2026"].iloc[0]),
                "costo": float(costo.loc[nombre, "2026"]),
            }
        )
    return pd.DataFrame(filas).sort_values("indice").reset_index(drop=True)


def _horas(junio: pd.DataFrame, fuente: str, anio: int) -> float:
    return float(junio.loc[junio["fuente"].eq(fuente) & junio["anio"].eq(anio), "horas_para_pagar"].iloc[0])


def preparar(corte: pd.DataFrame) -> dict:
    """Textos y series listos para la página. Los porcentajes salen del corte."""
    y2019 = _fila(corte, 2019)
    y2022 = _fila(corte, 2022)
    y2026 = _fila(corte, 2026)
    junio = horas_junio()
    grupos = cadenas()

    return {
        "corte": corte,
        "canasta_2026": float(y2026["acodeco_historico"]),
        "canasta_2019": float(y2019["acodeco_historico"]),
        "mef_2026": float(y2026["mef_cbfa"]),
        "mef_2019": float(y2019["mef_cbfa"]),
        "salario_2026": float(y2026["salario_mensual"]),
        "salario_2019": float(y2019["salario_mensual"]),
        "hora_2026": float(y2026["salario_hora"]),
        "pct_2026": float(y2026["pct_salario_acodeco"]),
        "pct_2022": float(y2022["pct_salario_acodeco"]),
        "pct_2019": float(y2019["pct_salario_acodeco"]),
        "pct_mef_2026": float(y2026["pct_salario_mef"]),
        "pct_mef_2022": float(y2022["pct_salario_mef"]),
        "pct_mef_2019": float(y2019["pct_salario_mef"]),
        "var_canasta_2026": float(y2026["var_canasta_pct"]),
        "var_canasta_2022": float(y2022["var_canasta_pct"]),
        "var_salario_2026": float(y2026["var_salario_pct"]),
        "var_salario_2022": float(y2022["var_salario_pct"]),
        "var_mef_2026": float(y2026["var_mef_pct"]),
        "var_mef_2022": float(y2022["var_mef_pct"]),
        "var_canasta_22_26": _variacion(y2026["acodeco_historico"], y2022["acodeco_historico"]),
        "var_salario_22_26": _variacion(y2026["salario_mensual"], y2022["salario_mensual"]),
        "var_mef_22_26": _variacion(y2026["mef_cbfa"], y2022["mef_cbfa"]),
        "horas_acodeco": {anio: _horas(junio, "acodeco_historico", anio) for anio in (2019, 2022, 2026)},
        "horas_mef": {anio: _horas(junio, "mef_cbfa", anio) for anio in (2019, 2022, 2026)},
        "cadenas": grupos,
    }
