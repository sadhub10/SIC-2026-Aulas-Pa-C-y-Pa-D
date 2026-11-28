
import pandas as pd
import json
import os

# Carpeta donde se encuentran los archivos
DATA = os.path.join(os.path.dirname(__file__), "data")


# ==========================================
# 1. CARGAR DATASET DE CANADÁ 2026
# ==========================================

def cargar_dataset():
    ruta = os.path.join(
        DATA, "my2026-fuel-consumption-ratings.csv"
    )

    return pd.read_csv(ruta, encoding="utf-8-sig")


# ==========================================
# 2. LIMPIAR LOS DATOS
# ==========================================

def limpiar(df):
    df = df.copy()

    # Eliminar espacios de los encabezados
    df.columns = df.columns.str.strip()

    # Eliminar espacios de los textos
    for columna in df.select_dtypes(
        include=["object", "string"]
    ).columns:
        df[columna] = df[columna].str.strip()

    # Convertir columnas a números
    columnas = [
        "Model year",
        "Engine size (L)",
        "Combined (L/100 km)",
        "CO2 emissions (g/km)"
    ]

    for columna in columnas:
        df[columna] = pd.to_numeric(
            df[columna], errors="coerce"
        )

    # Eliminar registros incompletos
    df = df.dropna(subset=columnas)

    # Eliminar vehículos que utilizan etanol E85
    df = df[df["Fuel type"] != "E"].copy()

    # Verificar coherencia de las emisiones
    co2_esperado = df["Combined (L/100 km)"] * 23

    diferencia = abs(
        df["CO2 emissions (g/km)"] - co2_esperado
    )

    # Aceptar una diferencia máxima del 8 %
    df = df[diferencia <= co2_esperado * 0.08]

    return df.reset_index(drop=True)


# ==========================================
# 3. CREAR CATÁLOGO DE PANAMÁ
# ==========================================

def crear_catalogo(df_limpio):

    from modelos import Vehiculo

    # Marca, modelo original, motor, transmisión,
    # tipo y nombre simplificado
    modelos_panama = [
        ("Toyota", "Corolla (1-mode)", 2.0,
         "AV", "Sedán", "Corolla"),

        ("Toyota", "Corolla Cross", 2.0,
         "AV10", "SUV", "Corolla Cross"),

        ("Hyundai", "Elantra", 2.0,
         "AV1", "Sedán", "Elantra"),

        ("Hyundai", "Kona", 2.0,
         "AV1", "SUV", "Kona"),

        ("Hyundai", "Venue", 1.6,
         "AV1", "SUV", "Venue"),

        ("Hyundai", "Tucson AWD", 2.5,
         "AS8", "SUV", "Tucson AWD"),

        ("Kia", "Seltos", 2.0,
         "AV8", "SUV", "Seltos"),

        ("Kia", "Sportage", 2.5,
         "AS8", "SUV", "Sportage"),

        ("Nissan", "Sentra S", 2.0,
         "AV", "Sedán", "Sentra"),

        ("Nissan", "Kicks", 2.0,
         "AV", "SUV", "Kicks"),

        ("Honda", "CR-V", 1.5,
         "AV", "SUV", "CR-V"),

        ("Honda", "HR-V", 2.0,
         "AV", "SUV", "HR-V")
    ]

    # Equivalencias de combustibles
    combustibles = {
        "X": "gasolina_91",
        "Z": "gasolina_95",
        "D": "diesel"
    }

    catalogo = []
    faltantes = []

    for marca, modelo, motor, transmision, tipo, nombre in modelos_panama:

        # Buscar coincidencias exactas
        coincidencias = df_limpio[
            (df_limpio["Make"] == marca) &
            (df_limpio["Model"] == modelo) &
            (df_limpio["Engine size (L)"] == motor) &
            (df_limpio["Transmission"] == transmision) &
            (df_limpio["Fuel type"] == "X")
        ]

        if coincidencias.empty:
            faltantes.append(marca + " " + modelo)
            continue

        # Obtener el registro de menor consumo
        fila = coincidencias.sort_values(
            "Combined (L/100 km)"
        ).iloc[0]

        combustible = combustibles[fila["Fuel type"]]

        consumo = float(fila["Combined (L/100 km)"])

        # Crear el objeto Vehiculo
        vehiculo = Vehiculo(
            marca,
            nombre,
            tipo,
            motor,
            combustible,
            consumo
        )

        catalogo.append(vehiculo)

    # Verificar que se encontraron los 12 modelos
    if faltantes:
        raise ValueError(
            "No se encontraron los modelos: "
            + ", ".join(faltantes)
        )

    # Convertir el catálogo a una tabla
    tabla = pd.DataFrame(
        [vehiculo.a_diccionario() for vehiculo in catalogo]
    )

    # Guardar el catálogo en CSV
    tabla.to_csv(
        os.path.join(DATA, "catalogo_panama.csv"),
        index=False,
        encoding="utf-8-sig"
    )

    return catalogo


# ==========================================
# 4. LEER PRECIOS DEL COMBUSTIBLE
# ==========================================

def leer_precios():

    df = pd.read_csv(
        os.path.join(DATA, "precios.csv"),
        encoding="utf-8-sig"
    )

    precios = dict(
        zip(df["combustible"], df["precio_litro"])
    )

    vigencia = str(df["vigente_desde"].iloc[0])

    return precios, vigencia


# ==========================================
# 5. LEER FACTORES DE EMISIÓN
# ==========================================

def leer_factores():

    df = pd.read_csv(
        os.path.join(DATA, "factores.csv"),
        encoding="utf-8-sig"
    )

    factores = dict(
        zip(df["combustible"], df["kg_co2_litro"])
    )

    return factores


# ==========================================
# 6. GUARDAR HISTORIAL DE CONSULTAS
# ==========================================

def guardar_historial(consultas):

    ruta = os.path.join(DATA, "historial.json")

    with open(ruta, "w", encoding="utf-8") as archivo:

        json.dump(
            consultas,
            archivo,
            ensure_ascii=False,
            indent=2
        )


# ==========================================
# 7. CARGAR HISTORIAL DE CONSULTAS
# ==========================================

def cargar_historial():

    ruta = os.path.join(DATA, "historial.json")

    # Si no existe el historial, devolver lista vacía
    if not os.path.exists(ruta):
        return []

    with open(ruta, "r", encoding="utf-8") as archivo:

        return json.load(archivo)


# ==========================================
# 8. CARGAR DATOS HISTÓRICOS 2021-2026
# ==========================================

def cargar_historico():

    df_2015_2024 = pd.read_csv(
        os.path.join(
            DATA,
            "my2015-2024-fuel-consumption-ratings.csv"
        ),
        encoding="utf-8-sig"
    )

    df_2025 = pd.read_csv(
        os.path.join(
            DATA,
            "my2025-fuel-consumption-ratings.csv"
        ),
        encoding="latin-1"
    )

    df_2026 = cargar_dataset()

    # Unir los tres DataFrames
    df_historico = pd.concat(
        [df_2015_2024, df_2025, df_2026],
        ignore_index=True
    )

    # Limpiar los registros
    df_historico = limpiar(df_historico)

    # Seleccionar los años de 2021 a 2026
    df_historico = df_historico[
        df_historico["Model year"].between(2021, 2026)
    ]

    return df_historico.reset_index(drop=True)


# ==========================================
# 9. LEER PRECIOS HISTÓRICOS
# ==========================================

def leer_precios_historicos():

    df = pd.read_csv(
        os.path.join(DATA, "precios_historicos.csv"),
        encoding="utf-8-sig",
        parse_dates=["vigente_desde"]
    )

    return df
