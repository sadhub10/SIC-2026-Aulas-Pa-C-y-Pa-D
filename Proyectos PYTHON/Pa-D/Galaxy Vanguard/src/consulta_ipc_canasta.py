"""Inflación, canasta y salario."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

_RAIZ = Path(__file__).resolve().parents[1]
PROCESSED = _RAIZ / "data" / "processed"
FIGURAS = _RAIZ / "outputs" / "figures"

# Junio está en ACODECO y en el MEF en los tres años. Agosto de 2022 no existe en el MEF.
MES_CORTE = 6
ANIOS = (2019, 2022, 2026)

# Cuadro 5, variación anual ya publicada. No está como fila mensual en ipc.csv.
_CUADRO5 = {
    2019: {"total": -0.3, "alimentos": 0.3},
    2022: {"total": 2.6, "alimentos": 3.9},
}


def cargar_datos(carpeta: Path | str = PROCESSED) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """IPC, costo de la canasta y salario mínimo ya limpios."""
    carpeta = Path(carpeta)
    ipc = pd.read_csv(carpeta / "ipc.csv", parse_dates=["fecha"])
    costo = pd.read_csv(carpeta / "costo_canasta_mensual.csv", parse_dates=["fecha"])
    salario = pd.read_csv(carpeta / "salario_minimo.csv", parse_dates=["fecha_inicio"])
    return ipc, costo, salario


def inflacion_oficial(ipc: pd.DataFrame) -> pd.DataFrame:
    """Variación interanual publicada: Cuadro 5 en 2019 y 2022, Cuadro 7 en octubre 2026."""
    octubre = ipc.loc[
        ipc["anio"].eq(2026) & ipc["mes"].eq(10) & ipc["grupo"].eq("total"),
        "notas",
    ]
    if octubre.empty or not str(octubre.iloc[0]).strip():
        raise ValueError("Octubre 2026 no trae la variación interanual en notas")
    nota = str(octubre.iloc[0])
    if "+3.3" not in nota or "+2.6" not in nota:
        raise ValueError(f"La nota de octubre 2026 no trae +3.3 % y +2.6 %: {nota}")
    filas = [
        {"momento": "2019", "etiqueta": "2019\nvariación anual", "total": _CUADRO5[2019]["total"], "alimentos": _CUADRO5[2019]["alimentos"]},
        {"momento": "2022", "etiqueta": "2022\nvariación anual", "total": _CUADRO5[2022]["total"], "alimentos": _CUADRO5[2022]["alimentos"]},
        {"momento": "oct 2026", "etiqueta": "Oct 2026\nvs oct 2025", "total": 3.3, "alimentos": 2.6},
    ]
    return pd.DataFrame(filas)


def corte_junio(costo: pd.DataFrame, salario: pd.DataFrame, mes: int = MES_CORTE) -> pd.DataFrame:
    """Canasta de un mismo mes y salario de gran empresa, Región 1."""
    r1 = salario.loc[
        salario["region"].eq(1)
        & salario["actividad"].eq("comercio_al_por_menor")
        & salario["categoria"].eq("gran_empresa"),
        ["anio_analisis", "salario_mensual"],
    ].rename(columns={"anio_analisis": "anio"})
    if set(r1["anio"]) != set(ANIOS):
        raise ValueError(f"Falta el salario de gran empresa, Región 1: {sorted(r1['anio'])}")

    def costos(fuente: str) -> pd.DataFrame:
        tabla = costo.loc[
            costo["fuente"].eq(fuente) & costo["mes"].eq(mes) & costo["anio"].isin(ANIOS),
            ["anio", "costo_total"],
        ]
        if set(tabla["anio"]) != set(ANIOS):
            raise ValueError(f"{fuente} no tiene el mes {mes} en 2019, 2022 y 2026")
        return tabla.rename(columns={"costo_total": fuente})

    corte = r1.merge(costos("acodeco_historico"), on="anio").merge(costos("mef_cbfa"), on="anio")
    corte = corte.sort_values("anio").reset_index(drop=True)
    base_canasta = float(corte.loc[corte["anio"].eq(2019), "acodeco_historico"].iloc[0])
    base_salario = float(corte.loc[corte["anio"].eq(2019), "salario_mensual"].iloc[0])
    corte["var_canasta_pct"] = (corte["acodeco_historico"] / base_canasta - 1) * 100
    corte["var_salario_pct"] = (corte["salario_mensual"] / base_salario - 1) * 100
    corte["pct_salario_acodeco"] = corte["acodeco_historico"] / corte["salario_mensual"] * 100
    corte["pct_salario_mef"] = corte["mef_cbfa"] / corte["salario_mensual"] * 100
    return corte


def _guardar(figura: plt.Figure, nombre: str, directorio: Path) -> Path:
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / nombre
    figura.savefig(ruta, dpi=140, bbox_inches="tight")
    plt.close(figura)
    return ruta


def figura_inflacion(inflacion: pd.DataFrame, directorio: Path = FIGURAS) -> Path:
    """Variación interanual publicada, general y alimentos."""
    figura, eje = plt.subplots(figsize=(7.2, 4.4))
    posiciones = range(len(inflacion))
    ancho = 0.36
    eje.bar([p - ancho / 2 for p in posiciones], inflacion["total"], width=ancho, label="Total", color="#1f4e79")
    eje.bar([p + ancho / 2 for p in posiciones], inflacion["alimentos"], width=ancho, label="Alimentos", color="#d4782a")
    eje.axhline(0, color="#666666", linewidth=0.8)
    eje.set_xticks(list(posiciones), inflacion["etiqueta"])
    eje.set_ylabel("Variación interanual (%)")
    eje.set_title("Inflación publicada por el INEC")
    eje.legend(frameon=False)
    eje.spines["top"].set_visible(False)
    eje.spines["right"].set_visible(False)
    figura.text(
        0.01,
        -0.02,
        "2019 y 2022: variación anual del Cuadro 5 (base 2013=100). Octubre 2026: Cuadro 7 (base 2024=100).",
        fontsize=8,
        color="#444444",
    )
    return _guardar(figura, "inflacion_interanual.png", directorio)


def figura_aumento(corte: pd.DataFrame, directorio: Path = FIGURAS) -> Path:
    """Incremento porcentual respecto a 2019, canasta ACODECO y salario de la Región 1."""
    figura, eje = plt.subplots(figsize=(7.2, 4.4))
    posiciones = range(len(corte))
    ancho = 0.36
    eje.bar(
        [p - ancho / 2 for p in posiciones],
        corte["var_canasta_pct"],
        width=ancho,
        label="Canasta ACODECO",
        color="#1f4e79",
    )
    eje.bar(
        [p + ancho / 2 for p in posiciones],
        corte["var_salario_pct"],
        width=ancho,
        label="Salario Región 1",
        color="#2e7d4f",
    )
    eje.axhline(0, color="#666666", linewidth=0.8)
    for posicion, anio in enumerate(corte["anio"]):
        if int(anio) == 2019:
            eje.text(posicion, 0.35, "0 %", ha="center", va="bottom", fontsize=8, color="#444444")
    eje.set_xticks(list(posiciones), [str(anio) for anio in corte["anio"]])
    eje.set_ylabel("Cambio respecto a junio de 2019 (%)")
    eje.set_title("Aumento de la canasta y del salario")
    eje.legend(frameon=False)
    eje.spines["top"].set_visible(False)
    eje.spines["right"].set_visible(False)
    figura.text(
        0.01,
        -0.02,
        "Junio. Canasta ACODECO. Salario: comercio al por menor, gran empresa, Región 1.",
        fontsize=8,
        color="#444444",
    )
    return _guardar(figura, "aumento_canasta_salario.png", directorio)


def figura_canasta_salario(corte: pd.DataFrame, directorio: Path = FIGURAS) -> Path:
    """Costo de junio en balboas frente al salario mensual. ACODECO y MEF, por separado."""
    figura, eje = plt.subplots(figsize=(7.6, 4.4))
    posiciones = range(len(corte))
    ancho = 0.25
    eje.bar([p - ancho for p in posiciones], corte["acodeco_historico"], width=ancho, label="Canasta ACODECO", color="#1f4e79")
    eje.bar(list(posiciones), corte["mef_cbfa"], width=ancho, label="Canasta MEF", color="#d4782a")
    eje.bar([p + ancho for p in posiciones], corte["salario_mensual"], width=ancho, label="Salario Región 1", color="#2e7d4f")
    eje.set_xticks(list(posiciones), [str(anio) for anio in corte["anio"]])
    eje.set_ylabel("Balboas")
    eje.set_title("Canasta de junio frente al salario mínimo")
    eje.legend(frameon=False)
    eje.spines["top"].set_visible(False)
    eje.spines["right"].set_visible(False)
    figura.text(
        0.01,
        -0.02,
        "ACODECO y MEF no se promedian. Salario mensual de gran empresa, Región 1 (hora × 208).",
        fontsize=8,
        color="#444444",
    )
    return _guardar(figura, "canasta_vs_salario.png", directorio)


def guardar_figuras(
    ipc: pd.DataFrame | None = None,
    costo: pd.DataFrame | None = None,
    salario: pd.DataFrame | None = None,
    directorio: Path | str = FIGURAS,
) -> pd.DataFrame:
    """Escribe las tres figuras y devuelve el corte de junio usado en las dos últimas."""
    if ipc is None or costo is None or salario is None:
        ipc, costo, salario = cargar_datos()
    directorio = Path(directorio)
    corte = corte_junio(costo, salario)
    figura_inflacion(inflacion_oficial(ipc), directorio)
    figura_aumento(corte, directorio)
    figura_canasta_salario(corte, directorio)
    _comprobar(corte)
    return corte


def _comprobar(corte: pd.DataFrame) -> None:
    """Junio, gran empresa, Región 1: las cifras de la guía de análisis."""
    esperado = {
        2019: (260.64, 565.76),
        2022: (285.92, 584.48),
        2026: (303.45, 628.16),
    }
    for anio, (canasta, pago) in esperado.items():
        fila = corte.loc[corte["anio"].eq(anio)].iloc[0]
        if abs(fila["acodeco_historico"] - canasta) > 0.02 or abs(fila["salario_mensual"] - pago) > 0.02:
            raise ValueError(f"El corte de junio {anio} no coincide con la guía: {fila.to_dict()}")


def main() -> None:
    corte = guardar_figuras()
    print("Junio, comercio al por menor, gran empresa, Región 1")
    print(
        corte.assign(
            acodeco_historico=lambda df: df["acodeco_historico"].round(2),
            mef_cbfa=lambda df: df["mef_cbfa"].round(2),
            salario_mensual=lambda df: df["salario_mensual"].round(2),
            pct_salario_acodeco=lambda df: df["pct_salario_acodeco"].round(1),
        )[
            ["anio", "acodeco_historico", "mef_cbfa", "salario_mensual", "pct_salario_acodeco", "var_canasta_pct", "var_salario_pct"]
        ].to_string(index=False)
    )
    print(f"Figuras en {FIGURAS.relative_to(_RAIZ)}")


if __name__ == "__main__":
    main()
