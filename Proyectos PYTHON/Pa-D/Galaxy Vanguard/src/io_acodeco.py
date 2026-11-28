"""Lectura de precios y costo de canasta de ACODECO a formato largo.

Los CSV de 2019 y 2022 salen del nombre del archivo (`cba_2019_03.csv`).
El histórico y el PDF de septiembre 2026 se leen por la posición de cada
palabra: el texto corrido mezcla los dígitos de columnas vecinas. Los crudos
no se modifican.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pdfplumber

from esquemas import columnas, validar
from limpieza import (
    cadena_establecimiento,
    estandarizar_establecimiento,
    normalizar_producto,
    reparar_texto,
    zona_establecimiento,
)

_RAIZ = Path(__file__).resolve().parents[1]
DIRECTORIO_CSV = _RAIZ / "data" / "raw" / "acodeco"
_NOMBRE_ARCHIVO = re.compile(r"cba_(\d{4})_(\d{2})\.csv$", re.IGNORECASE)
_PIE = re.compile(r"^(Costo Total|FUENTE)\b", re.IGNORECASE)


def _anio_mes(path: Path) -> tuple[int, int]:
    coincidencia = _NOMBRE_ARCHIVO.search(path.name)
    if coincidencia is None:
        raise ValueError(f"El nombre no trae año y mes: {path.name}")
    return int(coincidencia.group(1)), int(coincidencia.group(2))


def _separador(texto: str) -> str:
    muestra = "\n".join(texto.splitlines()[:5])
    return ";" if muestra.count(";") > muestra.count(",") else ","


def _tabla_ancha(texto: str) -> pd.DataFrame:
    separador = _separador(texto)
    lineas = texto.splitlines()
    try:
        inicio = next(
            indice
            for indice, linea in enumerate(lineas)
            if "Producto" in linea and "Medida" in linea
        )
    except StopIteration as error:
        raise ValueError("El CSV no tiene columnas Producto y Medida") from error

    filas = [linea.split(separador) for linea in lineas[inicio:]]
    ancho = max(len(fila) for fila in filas)
    filas = [fila + [""] * (ancho - len(fila)) for fila in filas]
    tabla = pd.DataFrame(filas)
    cabecera = tabla.iloc[0].astype(str).str.strip()
    columna_producto = cabecera.tolist().index("Producto")
    tabla = tabla.iloc[:, columna_producto:]
    tabla.columns = [str(nombre).strip() for nombre in tabla.iloc[0]]
    tabla = tabla.iloc[1:].copy()
    tabla = tabla.loc[:, [nombre for nombre in tabla.columns if nombre != ""]]

    producto = tabla["Producto"].astype(str).str.strip()
    tabla = tabla.loc[producto.ne("") & ~producto.str.match(_PIE)].copy()
    tabla["Producto"] = producto.loc[tabla.index]
    tabla["Medida"] = tabla["Medida"].astype(str).str.strip()
    return tabla


def leer_cba_csv(path: Path | str, anio: int | None = None, mes: int | None = None) -> pd.DataFrame:
    """Un mes de precios, una fila por producto y establecimiento."""
    path = Path(path)
    if anio is None or mes is None:
        anio_archivo, mes_archivo = _anio_mes(path)
        anio = anio if anio is not None else anio_archivo
        mes = mes if mes is not None else mes_archivo

    texto = path.read_bytes().decode("latin-1")
    ancho = _tabla_ancha(texto)
    productos = ancho["Producto"].nunique()
    if productos != 59:
        raise ValueError(f"{path.name}: se esperaban 59 productos y hay {productos}")

    establecimientos = [columna for columna in ancho.columns if columna not in {"Producto", "Medida"}]
    largo = ancho.melt(
        id_vars=["Producto", "Medida"],
        value_vars=establecimientos,
        var_name="establecimiento",
        value_name="precio",
    )
    precio = largo["precio"].astype(str).str.strip().str.replace(",", ".", regex=False)
    precio = precio.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    largo["precio"] = pd.to_numeric(precio, errors="coerce")

    normalizado = largo["Producto"].map(normalizar_producto)
    largo["producto_estandar"] = normalizado.map(lambda par: par[0])
    largo["control_precio"] = normalizado.map(lambda par: par[1])
    largo["producto"] = largo["Producto"].astype(str).str.strip()
    largo["medida"] = largo["Medida"].map(reparar_texto)
    largo["establecimiento"] = largo["establecimiento"].astype(str).str.strip()
    largo["establecimiento_estandar"] = largo["establecimiento"].map(estandarizar_establecimiento)
    largo["cadena"] = largo["establecimiento"].map(cadena_establecimiento)
    largo["zona"] = largo["establecimiento"].map(zona_establecimiento)
    largo["anio"] = anio
    largo["mes"] = mes
    largo["fecha"] = pd.Timestamp(anio, mes, 1)
    largo["quincena"] = pd.NA
    largo["fuente"] = "acodeco_csv"

    largo = largo.loc[:, columnas("precios_supermercados")]
    return validar(largo, "precios_supermercados")


def leer_precios_csv(directorio: Path | str = DIRECTORIO_CSV) -> pd.DataFrame:
    """Concatena los CSV de 2019 (marzo–diciembre) y 2022 (enero–junio)."""
    directorio = Path(directorio)
    archivos = sorted(directorio.glob("csv_*/*.csv"))
    if not archivos:
        raise FileNotFoundError(f"No hay CSV de ACODECO en {directorio}")
    return pd.concat([leer_cba_csv(archivo) for archivo in archivos], ignore_index=True)


_PDF_HISTORICO = DIRECTORIO_CSV / "HistoricoCBFA_2015-2026.pdf"
_PDF_SEPTIEMBRE = DIRECTORIO_CSV / "CBA_PreciosSupermercadosXRutas_2daSeptiembre2026.pdf"
_ANIO_PRIMERA_PAGINA = 2015
_PRECIO = re.compile(r"^\d+\.\d+$")
_NOTA_COSTO = (
    "ACODECO: costo de la canasta de 59 productos a precios de supermercado "
    "en la provincia de Panamá. No es el costo calórico del MEF."
)

# Cifras verificadas en references/plan_datos.md, sección 1.2.
_COSTO_VERIFICADO: dict[int, list[float]] = {
    2019: [262.93, 262.51, 261.19, 262.19, 264.89, 260.64, 261.90, 263.09, 263.90, 265.44, 263.13, 263.52],
    2022: [278.87, 274.00, 275.65, 275.66, 280.71, 285.92, 292.52, 285.06, 283.91, 283.92, 286.51, 287.41],
    2026: [304.40, 303.04, 302.79, 303.53, 305.13, 303.45, 303.67, 304.85],
}


def _palabras(page) -> list[dict]:
    return page.extract_words(x_tolerance=1, y_tolerance=1, keep_blank_chars=False)


def _filas(palabras: list[dict], tolerancia: float = 3) -> list[list[dict]]:
    ordenadas = sorted(palabras, key=lambda palabra: (palabra["top"], palabra["x0"]))
    filas: list[list[dict]] = []
    for palabra in ordenadas:
        if not filas or palabra["top"] - filas[-1][0]["top"] > tolerancia:
            filas.append([palabra])
        else:
            filas[-1].append(palabra)
    return filas


def _centros(posiciones: list[float], tolerancia: float = 18) -> list[float]:
    grupos: list[list[float]] = []
    for posicion in sorted(posiciones):
        if not grupos or posicion - grupos[-1][-1] > tolerancia:
            grupos.append([posicion])
        else:
            grupos[-1].append(posicion)
    return [sum(grupo) / len(grupo) for grupo in grupos]


def _cercano(posicion: float, centros: list[float], maximo: float) -> int | None:
    if not centros:
        return None
    indice = min(range(len(centros)), key=lambda i: abs(centros[i] - posicion))
    if abs(centros[indice] - posicion) > maximo:
        return None
    return indice


def _columna_encabezado(palabra: dict, centros: list[float]) -> int | None:
    """Asigna un texto de cabecera a la columna de precios que empieza a su izquierda.

    Un token corto pegado al borde (`8` de Milla 8, `2` de Pagoda No. 2) vuelve
    a la columna anterior: el nombre es más ancho que el hueco entre precios.
    """
    if not centros:
        return None
    limites = [(centros[i] + centros[i + 1]) / 2 for i in range(len(centros) - 1)]
    indice = 0
    for limite in limites:
        if palabra["x0"] > limite:
            indice += 1
    if indice > 0:
        ancho = palabra["x1"] - palabra["x0"]
        if ancho <= 8 and palabra["x0"] - limites[indice - 1] <= 6:
            indice -= 1
    return indice


def _nombre_tienda(partes: list[str]) -> str:
    nombre = " ".join(partes).replace(",", " ")
    nombre = nombre.replace("MIINIMARKE T", "MIINIMARKET")
    return reparar_texto(nombre)


def leer_costo_historico(path: Path | str = _PDF_HISTORICO) -> pd.DataFrame:
    """COSTO TOTAL mensual de 2019, 2022 y 2026.

    El PDF trae un año por página, de 2015 a 2026. Solo se conservan los tres
    años del proyecto. 2026 llega hasta agosto.
    """
    path = Path(path)
    registros: list[dict] = []
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 12:
            raise ValueError(f"{path.name}: se esperaban 12 páginas (2015-2026) y hay {len(pdf.pages)}")
        for numero, page in enumerate(pdf.pages, start=1):
            anio = _ANIO_PRIMERA_PAGINA + numero - 1
            if anio not in _COSTO_VERIFICADO:
                continue
            palabras = _palabras(page)
            encabezado = next(palabra for palabra in palabras if palabra["text"] == "TOTAL")
            cifras = [
                palabra
                for palabra in palabras
                if abs(palabra["top"] - encabezado["top"]) < 1.2 and _PRECIO.match(palabra["text"])
            ]
            cifras.sort(key=lambda palabra: palabra["x0"])
            valores = [float(palabra["text"]) for palabra in cifras]
            esperado = _COSTO_VERIFICADO[anio]
            if len(valores) != len(esperado) or any(abs(v - e) > 0.001 for v, e in zip(valores, esperado)):
                raise ValueError(f"COSTO TOTAL {anio} no coincide con las cifras verificadas: {valores}")
            for mes, costo in enumerate(valores, start=1):
                registros.append(
                    {
                        "fecha": pd.Timestamp(anio, mes, 1),
                        "anio": anio,
                        "mes": mes,
                        "fuente": "acodeco_historico",
                        "geografia": "provincia_de_panama",
                        "n_productos": 59,
                        "costo_total": costo,
                        "notas": _NOTA_COSTO,
                    }
                )
    return validar(pd.DataFrame(registros), "costo_canasta_mensual")


def _pagina_septiembre(page) -> pd.DataFrame:
    palabras = _palabras(page)
    producto = next(palabra for palabra in palabras if palabra["text"] == "Producto")
    precios = [palabra for palabra in palabras if _PRECIO.match(palabra["text"]) and palabra["x0"] > 210]
    medidas = [palabra for palabra in palabras if palabra["text"] in {"Kilogramos", "Gramos", "Litros", "Unidades"}]
    if not precios or not medidas:
        raise ValueError("La página no tiene precios o medidas")
    y_datos = min(palabra["top"] for palabra in medidas)
    centros = _centros([palabra["x0"] for palabra in precios])

    tiendas = [
        palabra
        for palabra in palabras
        if palabra["x0"] > 210 and producto["top"] - 8 < palabra["top"] < y_datos - 2 and not _PRECIO.match(palabra["text"])
    ]
    nombres_partes: list[list[str]] = [[] for _ in centros]
    for palabra in sorted(tiendas, key=lambda item: (item["top"], item["x0"])):
        indice = _columna_encabezado(palabra, centros)
        if indice is None:
            continue
        nombres_partes[indice].append(palabra["text"])
    nombres = [_nombre_tienda(partes) for partes in nombres_partes]

    zonas_palabras = [
        palabra
        for palabra in palabras
        if 35 < palabra["top"] < producto["top"] - 8 and palabra["x0"] > 200
    ]
    frases: list[list[dict]] = []
    for palabra in sorted(zonas_palabras, key=lambda item: item["x0"]):
        if not frases or palabra["x0"] - frases[-1][-1]["x1"] > 30:
            frases.append([palabra])
        else:
            frases[-1].append(palabra)
    zonas = [" ".join(item["text"] for item in frase) for frase in frases]
    centros_zona = [sum(item["x0"] for item in frase) / len(frase) for frase in frases]
    zona_columna = []
    for centro in centros:
        if not centros_zona:
            zona_columna.append("")
            continue
        indice = min(range(len(centros_zona)), key=lambda i: abs(centros_zona[i] - centro))
        zona_columna.append(zonas[indice])

    filas = []
    for fila in _filas(palabras):
        if fila[0]["top"] < y_datos - 2:
            continue
        texto_producto = " ".join(palabra["text"] for palabra in fila if palabra["x0"] < 168)
        if not texto_producto or texto_producto.upper().startswith(("NOTA", "FUENTE", "COSTO")):
            continue
        medida = reparar_texto(" ".join(palabra["text"] for palabra in fila if 168 <= palabra["x0"] < 220))
        por_columna: dict[int, float] = {}
        for palabra in fila:
            if not _PRECIO.match(palabra["text"]):
                continue
            indice = _cercano(palabra["x0"], centros, 20)
            if indice is not None:
                por_columna[indice] = float(palabra["text"])
        if not medida and not por_columna:
            continue
        estandar, control = normalizar_producto(texto_producto)
        for indice, establecimiento in enumerate(nombres):
            if not establecimiento:
                continue
            filas.append(
                {
                    "producto": texto_producto,
                    "producto_estandar": estandar,
                    "medida": medida,
                    "establecimiento": establecimiento,
                    "establecimiento_estandar": estandarizar_establecimiento(establecimiento),
                    "cadena": cadena_establecimiento(establecimiento),
                    "zona": zona_establecimiento(establecimiento, zona_columna[indice]),
                    "precio": por_columna.get(indice, pd.NA),
                    "control_precio": control,
                }
            )
    return pd.DataFrame(filas)


def leer_precios_septiembre_2026(path: Path | str = _PDF_SEPTIEMBRE) -> pd.DataFrame:
    """Precios por establecimiento de la segunda quincena de septiembre 2026."""
    path = Path(path)
    marcos = []
    with pdfplumber.open(path) as pdf:
        if len(pdf.pages) != 5:
            raise ValueError(f"{path.name}: se esperaban 5 páginas y hay {len(pdf.pages)}")
        for page in pdf.pages:
            marcos.append(_pagina_septiembre(page))
    largo = pd.concat(marcos, ignore_index=True)
    productos = largo["producto_estandar"].nunique()
    if productos != 59:
        raise ValueError(f"Septiembre 2026: se esperaban 59 productos y hay {productos}")
    largo["anio"] = 2026
    largo["mes"] = 9
    largo["fecha"] = pd.Timestamp(2026, 9, 1)
    largo["quincena"] = 2
    largo["fuente"] = "acodeco_pdf_sep2026"
    largo["precio"] = pd.to_numeric(largo["precio"], errors="coerce")
    largo = largo.loc[:, columnas("precios_supermercados")]
    largo = validar(largo, "precios_supermercados")
    _verificar_muestra_septiembre(largo)
    return largo


def _verificar_muestra_septiembre(largo: pd.DataFrame) -> None:
    """Celdas leídas del PDF, una por zona de las primeras páginas."""
    muestra = [
        ("babilla (carne de res de primera)", "REY DE VIA ESPAÑA", 7.54),
        ("bistec de cinta", "REY DE VIA ESPAÑA", 6.63),
        ("pulpa negra", "RIBA SMITH BELLA VISTA", 12.36),
        ("sardina en salsa de tomate sin picante", "REY DE VIA ESPAÑA", 0.49),
        ("babilla (carne de res de primera)", "REY CHANIS", 7.30),
        ("bistec de cinta", "REY MILLA 8", 6.52),
    ]
    for producto, tienda, precio in muestra:
        filas = largo.loc[
            largo["producto_estandar"].eq(producto) & largo["establecimiento_estandar"].eq(tienda),
            "precio",
        ]
        if filas.empty or abs(float(filas.iloc[0]) - precio) > 0.001:
            raise ValueError(f"Muestra septiembre 2026 no coincide: {producto} / {tienda} -> {filas.tolist()}")


def leer_precios(directorio: Path | str = DIRECTORIO_CSV) -> pd.DataFrame:
    """CSV de 2019 y 2022 más el PDF de la segunda quincena de septiembre 2026."""
    return pd.concat(
        [leer_precios_csv(directorio), leer_precios_septiembre_2026()],
        ignore_index=True,
    )
