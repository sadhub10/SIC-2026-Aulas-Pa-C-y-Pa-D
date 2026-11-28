import os
import statistics

import pandas as pd

COL_MOTOR = "Engine size (L)"
COL_CONSUMO = "Combined (L/100 km)"
COL_CO2 = "CO2 emissions (g/km)"
COL_COMBUSTIBLE = "Fuel type"
COL_AÑO = "Model year"

COL_FECHA = "vigente_desde"
COL_PRECIO_91 = "gasolina_91"


def ranking(catalogo, precios, factores):
    filas = []
    for v in catalogo:
        filas.append({
            "Modelo": v.nombre(),
            "Tipo": v.tipo,
            "Costo (B/. por 100 km)": round(v.costo_100km(precios), 2),
            "CO2 (kg por 100 km)": round(v.co2_100km(factores), 2),
        })
    df = pd.DataFrame(filas)
    df = df.sort_values("Costo (B/. por 100 km)").reset_index(drop=True)
    return df


def estadisticas(df_limpio):
    df = df_limpio[df_limpio[COL_COMBUSTIBLE].isin(["X", "Z"])]
    motor = df[COL_MOTOR].tolist()
    consumo = df[COL_CONSUMO].tolist()

    regresion = statistics.linear_regression(motor, consumo)

    return {
        "promedio": df[COL_CONSUMO].mean(),
        "mediana": df[COL_CONSUMO].median(),
        "correlacion": df[COL_MOTOR].corr(df[COL_CONSUMO]),
        "pendiente": regresion.slope,
        "intercepto": regresion.intercept,
    }


def comparar_tipos(catalogo):
    df = pd.DataFrame([{"Tipo": v.tipo, "Consumo": v.consumo} for v in catalogo])
    res = df.groupby("Tipo")["Consumo"].mean().reset_index()
    res = res.rename(columns={"Consumo": "Consumo promedio (L/100 km)"})

    menor = res["Consumo promedio (L/100 km)"].min()
    res["Diferencia (%)"] = (res["Consumo promedio (L/100 km)"] - menor) / menor * 100
    res = res.round(2)
    return res


def datos_dispersion(df_limpio):
    df = df_limpio[df_limpio[COL_COMBUSTIBLE].isin(["X", "Z"])]
    df = df[[COL_MOTOR, COL_CONSUMO]].copy()
    df.columns = ["Motor (L)", "Consumo (L/100 km)"]
    return df


def exportar_reporte(df_ranking):
    os.makedirs("reportes", exist_ok=True)
    ruta = os.path.join("reportes", "reporte.csv")
    df_ranking.to_csv(ruta, index=False, encoding="utf-8-sig")
    return ruta


def tendencia_anual(df_historico):
    df = df_historico[df_historico[COL_COMBUSTIBLE].isin(["X", "Z"])]
    res = df.groupby(COL_AÑO).agg(
        consumo=(COL_CONSUMO, "mean"),
        co2=(COL_CO2, "mean"),
        modelos=(COL_CONSUMO, "count"),
    ).reset_index()
    res.columns = ["Año", "Consumo promedio (L/100 km)", "CO2 promedio (g/km)", "Modelos"]
    res = res.round(2)
    return res


def precio_por_año(precios_historicos):
    df = precios_historicos.copy()
    df["Año"] = df[COL_FECHA].dt.year
    res = df.groupby("Año")[COL_PRECIO_91].mean().reset_index()
    res.columns = ["Año", "Precio promedio (B/. por litro)"]
    return res


def evolucion_modelo(df_historico, marca, nombres, precios_año):
    df = df_historico.copy()
    marca_ok = df["Make"].str.strip().str.lower() == marca.strip().lower()
    nombres_ok = df["Model"].str.strip().str.lower().isin([n.strip().lower() for n in nombres])
    df = df[marca_ok & nombres_ok & (df[COL_COMBUSTIBLE] == "X")]

    res = df.groupby(COL_AÑO)[COL_CONSUMO].min().reset_index()
    res.columns = ["Año", "Consumo (L/100 km)"]

    res = res.merge(precios_año, on="Año", how="left")
    res["Costo (B/. por 100 km)"] = res["Consumo (L/100 km)"] * res["Precio promedio (B/. por litro)"]
    res = res[["Año", "Consumo (L/100 km)", "Costo (B/. por 100 km)"]].round(2)
    return res


precio_por_anio = precio_por_año

