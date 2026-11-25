"""Análisis reproducible de la encuesta de Samsung Innovation Campus 2026.

Solo Python: pandas, matplotlib y openpyxl (lector de Excel de pandas).

Ejecución:
    python dataframe_encuesta_mejorado.py
    python dataframe_encuesta_mejorado.py --archivo "ruta/al/Excel.xlsx"
    python dataframe_encuesta_mejorado.py --archivo "ruta/al/dataset.csv"

El Excel debe incluir la hoja 'Datos_limpios' y las columnas originales
normalizadas. Si no se proporciona --archivo, se buscan los Excel disponibles
junto al script, en el directorio actual y en Descargas.
Los resultados se guardan como archivos CSV, PNG y TXT en resultados_encuesta/.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import unicodedata
import warnings

import matplotlib
matplotlib.use("Agg")  # Generar imágenes sin depender de una ventana gráfica.
import matplotlib.pyplot as plt
import pandas as pd


HOJA = "Datos_limpios"
NOMBRES_ARCHIVO = (
    "analisis_cruces_SIC_2026.xlsx",
    "analisis_encuesta_SIC_2026.xlsx",
    "Analisis_encuesta.xlsx",
    "samsung_encuesta_dataframe.csv",
)
TRANSPORTE = (
    "Menos de 30 minutos.",
    "Entre 30 minutos y 1 hora.",
    "Entre 1 y 2 horas.",
    "Más de 2 horas.",
)
ORDINALES = {
    "capacidad_ahorro_mensual": (
        "Nada por ahora", "Menos de $10", "Entre $10 y $25",
        "Entre $26 y $50", "Más de $50",
    ),
    "impacto_habitos_academico": (
        "Nunca", "Rara vez", "A veces", "Frecuentemente", "Siempre",
    ),
    "rango_edad": (
        "18 a 20 años", "21 a 23 años", "24 a 26 años", "27 años o más",
    ),
}
NOMINALES = (
    "dificultad_finanzas", "obstaculo_ahorro_inversion", "habito_dificil",
    "causa_malos_habitos", "situacion_actual", "zona_residencia",
    "recursos_tecnologicos", "verificacion_informacion", "discapacidad_apoyo",
    "tipo_discapacidad", "accesibilidad_universitaria",
)
REQUERIDAS = (
    "dificultad_finanzas", "capacidad_ahorro_mensual",
    "obstaculo_ahorro_inversion", "habito_dificil",
    "impacto_habitos_academico", "causa_malos_habitos",
    "rango_edad", "situacion_actual", "zona_residencia",
    "recursos_tecnologicos", "tiempo_transporte", "verificacion_informacion",
    "discapacidad_apoyo", "tipo_discapacidad", "accesibilidad_universitaria",
)
INDICADORES = (
    "barrera_informacion_financiera", "afectacion_habitos_alta",
    "traslado_1h_o_mas", "inconsistencia_salto_discapacidad",
)


def normalizar_texto(valor: object) -> object:
    """Normaliza espacios/Unicode, manteniendo nulos y tildes."""
    if pd.isna(valor):
        return pd.NA
    texto = unicodedata.normalize("NFC", str(valor))
    return " ".join(texto.strip().split()) or pd.NA


def buscar_archivo(ruta: str | None) -> Path:
    if ruta:
        archivo = Path(ruta).expanduser().resolve()
        if not archivo.is_file():
            raise FileNotFoundError(f"No se encontró el archivo: {archivo}")
        return archivo
    carpetas = (Path(__file__).resolve().parent, Path.cwd(), Path.home() / "Downloads")
    for carpeta in carpetas:
        for nombre in NOMBRES_ARCHIVO:
            candidato = carpeta / nombre
            if candidato.is_file():
                return candidato
    raise FileNotFoundError(
        "No encontré el archivo de datos. Coloca el Excel junto al .py o usa "
        "--archivo \"C:\\ruta\\archivo.xlsx\". "
        f"Nombres buscados: {', '.join(NOMBRES_ARCHIVO)}"
    )


def cargar_datos(archivo: Path) -> pd.DataFrame:
    try:
        if archivo.suffix.lower() == ".csv":
            df = pd.read_csv(archivo, encoding="utf-8-sig")
        elif archivo.suffix.lower() in (".xlsx", ".xlsm"):
            df = pd.read_excel(archivo, sheet_name=HOJA)
        else:
            raise ValueError("Formato no compatible: utiliza .xlsx, .xlsm o .csv")
    except ValueError as exc:
        raise ValueError(f"No se pudo leer {archivo.name} (hoja '{HOJA}'): {exc}") from exc

    df.columns = [str(col).strip() for col in df.columns]
    faltan = sorted(set(REQUERIDAS) - set(df.columns))
    if faltan:
        raise ValueError(
            "Faltan columnas normalizadas: " + ", ".join(faltan) + ". "
            "Se necesita el Excel 'Datos_limpios' o el CSV ya procesado; "
            "el Excel original del Forms usa otros encabezados."
        )
    if df.empty:
        raise ValueError("El archivo no tiene respuestas")
    if "id_respuesta" not in df:
        df.insert(0, "id_respuesta", range(1, len(df) + 1))
    if "fecha_respuesta" in df:
        df["fecha_respuesta"] = pd.to_datetime(df["fecha_respuesta"], errors="coerce")

    for col in REQUERIDAS:
        df[col] = df[col].map(normalizar_texto).astype("string")
    return df


def preparar_datos(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df = df.copy()
    alertas: list[str] = []
    for col, categorias in ORDINALES.items():
        desconocidos = sorted(set(df[col].dropna()) - set(categorias))
        if desconocidos:
            alertas.append(f"Categorías no reconocidas en '{col}': {desconocidos}")
        # No se pierden datos inesperados en el DataFrame: si aparecen, detener.
    valores_transporte = set(TRANSPORTE) | {"No aplica, estudio a distancia."}
    desconocidos = sorted(set(df["tiempo_transporte"].dropna()) - valores_transporte)
    if desconocidos:
        alertas.append(f"Categorías no reconocidas en 'tiempo_transporte': {desconocidos}")
    if alertas:
        raise ValueError("\n".join(alertas) + "\nCorrige el origen antes de analizar.")

    for col, categorias in ORDINALES.items():
        df[col] = pd.Categorical(df[col], categories=list(categorias), ordered=True)
    df["estudio_distancia"] = df["tiempo_transporte"].eq("No aplica, estudio a distancia.").astype("Int64")
    # Los alumnos a distancia se conservan en los datos, pero no constituyen
    # un quinto nivel ordinal de duración del trayecto.
    df["tiempo_transporte"] = pd.Categorical(
        df["tiempo_transporte"], categories=list(TRANSPORTE) + ["No aplica, estudio a distancia."],
        ordered=False,
    )
    df["duracion_transporte_ordinal"] = pd.Categorical(
        df["tiempo_transporte"].astype("string").where(df["estudio_distancia"].eq(0)),
        categories=list(TRANSPORTE), ordered=True,
    )
    for col in NOMINALES:
        df[col] = df[col].astype("category")

    original = {col: pd.to_numeric(df[col], errors="coerce") for col in INDICADORES if col in df}
    respuesta = df["obstaculo_ahorro_inversion"].astype("string")
    df["barrera_informacion_financiera"] = respuesta.isin([
        "Falta de conocimientos financieros", "No saber qué opciones existen",
    ]).astype("Int64")
    df["afectacion_habitos_alta"] = df["impacto_habitos_academico"].isin([
        "Frecuentemente", "Siempre",
    ]).astype("Int64")
    df["traslado_1h_o_mas"] = df["tiempo_transporte"].isin([
        "Entre 1 y 2 horas.", "Más de 2 horas.",
    ]).astype("Int64")
    contesto_pregunta_condicionada = (
        df["tipo_discapacidad"].notna() | df["accesibilidad_universitaria"].notna()
    )
    df["inconsistencia_salto_discapacidad"] = (
        df["discapacidad_apoyo"].astype("string").ne("Sí.") & contesto_pregunta_condicionada
    ).astype("Int64")

    for col, antes in original.items():
        diferencia = antes.notna() & antes.ne(df[col]).fillna(False)
        if diferencia.any():
            alertas.append(f"'{col}': {int(diferencia.sum())} diferencias con el Excel; se recalculó.")

    if df["id_respuesta"].duplicated().any():
        alertas.append("Hay identificadores de respuesta duplicados.")
    nulos = df[list(REQUERIDAS)].isna().sum()
    for col, cantidad in nulos.items():
        if cantidad and col not in ("tipo_discapacidad", "accesibilidad_universitaria"):
            alertas.append(f"'{col}': {cantidad} respuestas faltantes.")
    return df, alertas


def cruce_indicador(df: pd.DataFrame, grupo: str, indicador: str) -> pd.DataFrame:
    resultado = df.groupby(grupo, observed=True, dropna=False)[indicador].agg(
        estudiantes="count", casos="sum", porcentaje="mean"
    )
    resultado["porcentaje"] = (resultado["porcentaje"] * 100).round(1)
    return resultado.reset_index()


def analizar(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    resultados: dict[str, pd.DataFrame] = {}
    resultados["frecuencia_obstaculos"] = df["obstaculo_ahorro_inversion"].value_counts(dropna=False).rename_axis("respuesta").reset_index(name="cantidad")
    resultados["frecuencia_ahorro"] = df["capacidad_ahorro_mensual"].value_counts(sort=False, dropna=False).rename_axis("respuesta").reset_index(name="cantidad")
    resultados["frecuencia_habitos"] = df["habito_dificil"].value_counts(dropna=False).rename_axis("respuesta").reset_index(name="cantidad")
    resultados["cruce_situacion_finanzas"] = cruce_indicador(df, "situacion_actual", "barrera_informacion_financiera")
    resultados["cruce_habitos_rendimiento"] = cruce_indicador(df, "habito_dificil", "afectacion_habitos_alta")

    grupos = {
        "Estudian y trabajan": df["situacion_actual"] == "Estudio y trabajo.",
        "Solamente estudian": df["situacion_actual"] == "Solamente estudio.",
    }
    indicadores = {
        "Barrera de información financiera": df["barrera_informacion_financiera"].eq(1),
        "Falta de dinero disponible": df["obstaculo_ahorro_inversion"].eq("Falta de dinero disponible"),
        "Dificultad para organizar gastos": df["dificultad_finanzas"].eq("Organizar mis gastos"),
        "Ya ahorra/invierte regularmente": df["obstaculo_ahorro_inversion"].eq("Ya ahorro o invierto regularmente"),
        "Alta afectación académica": df["afectacion_habitos_alta"].eq(1),
        "Dificultad con horarios de sueño": df["habito_dificil"].eq("Mantener horarios de sueño adecuados"),
    }
    filas = []
    for nombre, serie in indicadores.items():
        fila = {"indicador": nombre}
        for grupo, mascara in grupos.items():
            n = int(mascara.sum())
            casos = int((serie & mascara).sum())
            fila[f"n_{grupo}"] = n
            fila[f"casos_{grupo}"] = casos
            fila[f"pct_{grupo}"] = round(casos / n * 100, 1) if n else float("nan")
        fila["diferencia_pp"] = round(fila["pct_Estudian y trabajan"] - fila["pct_Solamente estudian"], 1)
        filas.append(fila)
    resultados["cruce_trabajo_finanzas"] = pd.DataFrame(filas)

    # Incluir explícitamente grupos con cero casos y a distancia por separado.
    transporte = df.groupby("tiempo_transporte", observed=True).agg(
        n_grupo=("id_respuesta", "count"),
        n_afectacion_alta=("afectacion_habitos_alta", "sum"),
        pct_afectacion_alta=("afectacion_habitos_alta", lambda s: round(s.mean() * 100, 1)),
        n_sueno=("habito_dificil", lambda s: int((s == "Mantener horarios de sueño adecuados").sum())),
        n_falta_tiempo=("causa_malos_habitos", lambda s: int((s == "Falta de tiempo").sum())),
    ).reset_index()
    resultados["cruce_transporte_habitos"] = transporte

    inter = df.groupby(list(INDICADORES[:3]), dropna=False).size().reset_index(name="n_estudiantes")
    inter["porcentaje_muestra"] = (inter["n_estudiantes"] / len(df) * 100).round(1)
    resultados["interseccion_problemas"] = inter.sort_values("n_estudiantes", ascending=False)
    resultados["calidad_datos"] = pd.DataFrame({
        "columna": df.columns,
        "faltantes": [int(df[col].isna().sum()) for col in df.columns],
        "porcentaje_faltantes": [round(df[col].isna().mean() * 100, 1) for col in df.columns],
        "valores_distintos": [int(df[col].nunique(dropna=True)) for col in df.columns],
    })
    return resultados


def guardar_grafico(series: pd.Series, titulo: str, xlabel: str, ruta: Path, porcentaje: bool = False) -> None:
    valores = series.astype(float)
    fig, ax = plt.subplots(figsize=(10, max(4.6, len(valores) * 0.55 + 1.5)))
    barras = ax.barh(range(len(valores)), valores.values)
    ax.set_yticks(range(len(valores)), [str(x) for x in valores.index])
    ax.invert_yaxis()
    ax.set_xlabel(xlabel)
    ax.set_title(titulo)
    ax.set_xlim(0, max(1, valores.max() * 1.24))
    for barra, valor in zip(barras, valores):
        etiqueta = f"{valor:.1f}%" if porcentaje else str(int(valor))
        ax.text(barra.get_width() + max(valores.max() * .02, .1),
                barra.get_y() + barra.get_height() / 2, etiqueta, va="center")
    fig.tight_layout()
    fig.savefig(ruta, dpi=160, bbox_inches="tight")
    plt.close(fig)


def exportar(df: pd.DataFrame, resultados: dict[str, pd.DataFrame], alertas: list[str], salida: Path, archivo: Path) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    df.to_csv(salida / "dataset_preparado.csv", index=False, encoding="utf-8-sig")
    for nombre, tabla in resultados.items():
        tabla.to_csv(salida / f"{nombre}.csv", index=False, encoding="utf-8-sig")

    guardar_grafico(
        df["obstaculo_ahorro_inversion"].value_counts(),
        "Obstáculos para ahorrar o invertir", "Estudiantes",
        salida / "01_obstaculos_financieros.png",
    )
    guardar_grafico(
        df["habito_dificil"].value_counts(),
        "Hábitos más difíciles de mantener", "Estudiantes",
        salida / "02_habitos_dificiles.png",
    )
    trabajo = resultados["cruce_trabajo_finanzas"].set_index("indicador")
    fig, ax = plt.subplots(figsize=(11, 6))
    y = list(range(len(trabajo)))
    ax.barh([k - .19 for k in y], trabajo["pct_Estudian y trabajan"], height=.36, label="Estudian y trabajan")
    ax.barh([k + .19 for k in y], trabajo["pct_Solamente estudian"], height=.36, label="Solamente estudian")
    ax.set_yticks(y, trabajo.index)
    ax.invert_yaxis()
    ax.set_xlabel("Porcentaje dentro del grupo (%)")
    ax.set_title("Comparación de indicadores por situación laboral")
    ax.legend()
    ax.set_xlim(0, 75)
    fig.tight_layout()
    fig.savefig(salida / "03_trabajo_vs_estudio.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    tabla_transporte = resultados["cruce_transporte_habitos"].set_index("tiempo_transporte")
    guardar_grafico(
        tabla_transporte.reindex(list(TRANSPORTE))["pct_afectacion_alta"],
        "Afectación académica según duración del traslado",
        "Afectación alta (%) · alumnos presenciales",
        salida / "04_transporte_y_habitos.png", porcentaje=True,
    )

    resumen = [
        "ENCUESTA SAMSUNG INNOVATION CAMPUS 2026",
        "Análisis exploratorio descriptivo. No implica causalidad ni representatividad nacional.",
        f"Fuente: {archivo}",
        f"Total de respuestas: {len(df)}",
        f"Barreras informativas financieras: {int(df['barrera_informacion_financiera'].sum())}/{len(df)}",
        f"Afectación académica frecuente/siempre: {int(df['afectacion_habitos_alta'].sum())}/{len(df)}",
        f"Traslado de una hora o más: {int(df['traslado_1h_o_mas'].sum())}/{len(df)}",
        f"Inconsistencias en preguntas condicionadas de discapacidad: {int(df['inconsistencia_salto_discapacidad'].sum())}",
        "Nota: los estudiantes a distancia se excluyen del orden de duraciones de transporte.",
        "Nota: los cruces reflejan asociaciones descriptivas, no efectos causales.",
        "Nota: las preguntas de discapacidad son sensibles y las respuestas inconsistentes se conservan marcadas.",
        "",
        "ALERTAS DE CALIDAD:",
        *(alertas or ["Sin alertas adicionales."]),
    ]
    (salida / "resumen_y_calidad.txt").write_text("\n".join(resumen) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Análisis de encuesta universitaria - SIC 2026")
    parser.add_argument("--archivo", help="Ruta al Excel de datos limpios o CSV preparado")
    parser.add_argument("--salida", help="Carpeta de resultados (por defecto, junto al script)")
    args = parser.parse_args()
    try:
        archivo = buscar_archivo(args.archivo)
        df, alertas = preparar_datos(cargar_datos(archivo))
        resultados = analizar(df)
        salida = Path(args.salida).expanduser().resolve() if args.salida else Path(__file__).resolve().parent / "resultados_encuesta"
        exportar(df, resultados, alertas, salida, archivo)
    except (FileNotFoundError, ValueError, ImportError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"\nArchivo leído: {archivo.name}")
    print(f"Dimensiones del DataFrame: {df.shape[0]} filas x {df.shape[1]} columnas")
    print("\nPrimeras respuestas:\n", df.head(3).to_string(index=False))
    print("\nTIPOS DE VARIABLES:\n", df.dtypes.to_string())
    for nombre, tabla in resultados.items():
        if nombre != "calidad_datos":
            print(f"\n=== {nombre.upper()} ===\n{tabla.to_string(index=False)}")
    print("\nAlertas:", *(alertas or ["Sin alertas adicionales"]), sep="\n- ")
    print(f"\nCSV, 4 gráficas PNG y resumen TXT guardados en: {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
