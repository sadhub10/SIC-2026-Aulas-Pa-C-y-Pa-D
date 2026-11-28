# Lectura del IPC del INEC a la tabla tidy `ipc`.

from __future__ import annotations

from pathlib import Path

import pandas as pd

from esquemas import validar

_RAIZ = Path(__file__).resolve().parents[1]
DIRECTORIO_INEC = _RAIZ / "data" / "raw" / "inec"

_MESES = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}
_MESES_LARGOS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

# Muestra mensual del plan de datos, sección 1.1. El CSV publica un decimal.
_MUESTRA_CUADRO6 = {
    (2019, 1, "total"): 103.8,
    (2019, 1, "alimentos_y_bebidas_no_alcoholicas"): 102.1,
    (2019, 6, "total"): 104.3,
    (2019, 6, "alimentos_y_bebidas_no_alcoholicas"): 101.8,
    (2019, 12, "total"): 104.0,
    (2019, 12, "alimentos_y_bebidas_no_alcoholicas"): 101.6,
    (2022, 1, "total"): 105.1,
    (2022, 1, "alimentos_y_bebidas_no_alcoholicas"): 103.6,
    (2022, 6, "total"): 109.1,
    (2022, 6, "alimentos_y_bebidas_no_alcoholicas"): 106.3,
    (2022, 12, "total"): 106.8,
    (2022, 12, "alimentos_y_bebidas_no_alcoholicas"): 109.0,
}
_ANUAL_CUADRO5 = {
    (2019, "total"): 104.2,
    (2019, "alimentos_y_bebidas_no_alcoholicas"): 101.8,
    (2022, "total"): 106.9,
    (2022, "alimentos_y_bebidas_no_alcoholicas"): 106.3,
}


def _archivo(directorio: Path, patron: str) -> Path:
    encontrados = sorted(directorio.glob(patron))
    if len(encontrados) != 1:
        raise FileNotFoundError(f"Se esperaba un archivo {patron} en {directorio}, hay {len(encontrados)}")
    return encontrados[0]


def _grupo(texto: str) -> str | None:
    limpio = " ".join(str(texto).split()).casefold()
    if limpio == "total":
        return "total"
    if limpio.startswith("alimentos y bebidas no alcoh"):
        return "alimentos_y_bebidas_no_alcoholicas"
    return None


def _fila(anio: int, mes: int, grupo: str, indice: float, base: str, geografia: str, fuente: str, notas: str = "") -> dict:
    return {
        "fecha": pd.Timestamp(anio, mes, 1),
        "anio": anio,
        "mes": mes,
        "geografia": geografia,
        "grupo": grupo,
        "indice": indice,
        "base": base,
        "fuente": fuente,
        "notas": notas,
    }


def _leer_cuadro6(path: Path) -> pd.DataFrame:
    texto = path.read_bytes().decode("latin-1")
    lineas = [linea for linea in texto.splitlines() if linea.strip()]
    encabezado = lineas[0].split(";")
    columnas = []
    for indice, etiqueta in enumerate(encabezado):
        if "-" not in etiqueta:
            continue
        anio_corto, mes_texto = etiqueta.split("-", 1)
        if anio_corto not in {"19", "22"} or mes_texto not in _MESES:
            continue
        columnas.append((indice, 2000 + int(anio_corto), _MESES[mes_texto]))

    registros = []
    for linea in lineas[1:]:
        celdas = linea.split(";")
        grupo = _grupo(celdas[0])
        if grupo is None:
            continue
        for indice, anio, mes in columnas:
            registros.append(
                _fila(
                    anio,
                    mes,
                    grupo,
                    float(celdas[indice]),
                    "2013=100",
                    "panama_y_san_miguelito",
                    "INEC Cuadro 6 2017-25",
                )
            )
    return pd.DataFrame(registros)


def _verificar_cuadro5(path: Path) -> None:
    texto = path.read_bytes().decode("latin-1")
    lineas = [linea for linea in texto.splitlines() if linea.strip()]
    encabezado = lineas[0].split(";")
    anuales: dict[tuple[int, str], float] = {}
    for linea in lineas[1:]:
        celdas = linea.split(";")
        grupo = _grupo(celdas[0])
        if grupo is None:
            continue
        for indice, etiqueta in enumerate(encabezado[1:], start=1):
            if etiqueta in {"2019", "2022"}:
                anuales[(int(etiqueta), grupo)] = float(celdas[indice])
    if anuales != _ANUAL_CUADRO5:
        raise ValueError(f"El Cuadro 5 anual no coincide con las cifras verificadas: {anuales}")


def _leer_cuadro8(path: Path) -> pd.DataFrame:
    cuadro = pd.read_excel(path, header=None)
    anio = None
    registros = []
    for _, fila in cuadro.iterrows():
        etiqueta = fila.iloc[0]
        if pd.isna(etiqueta):
            continue
        texto = str(etiqueta).strip()
        if texto in {"2025", "2026"}:
            anio = int(texto)
            continue
        mes = _MESES_LARGOS.get(texto.casefold())
        if mes is None or anio is None:
            continue
        registros.append(
            _fila(anio, mes, "total", float(fila.iloc[1]), "2024=100", "provincia_de_panama", "INEC Cuadro 8 2026")
        )
        registros.append(
            _fila(
                anio,
                mes,
                "alimentos_y_bebidas_no_alcoholicas",
                float(fila.iloc[4]),
                "2024=100",
                "provincia_de_panama",
                "INEC Cuadro 8 2026",
            )
        )
    return pd.DataFrame(registros)


def _notas_octubre_2026(path: Path) -> str:
    cuadro = pd.read_excel(path, header=None)
    variaciones = {}
    for _, fila in cuadro.iterrows():
        grupo = _grupo(fila.iloc[0])
        if grupo is None:
            continue
        variaciones[grupo] = float(fila.iloc[4])
    total = variaciones["total"]
    alimentos = variaciones["alimentos_y_bebidas_no_alcoholicas"]
    if round(total, 1) != 3.3 or round(alimentos, 1) != 2.6:
        raise ValueError(f"La variación interanual del Cuadro 7 no es +3.3 % y +2.6 %: {variaciones}")
    return (
        "Variación interanual octubre 2026 / octubre 2025, INEC Cuadro 7: "
        f"total +{total:.1f} %; alimentos y bebidas no alcohólicas +{alimentos:.1f} %."
    )


def _verificar_muestra(ipc: pd.DataFrame) -> None:
    for (anio, mes, grupo), esperado in _MUESTRA_CUADRO6.items():
        valor = ipc.loc[
            ipc["anio"].eq(anio) & ipc["mes"].eq(mes) & ipc["grupo"].eq(grupo) & ipc["base"].eq("2013=100"),
            "indice",
        ]
        if valor.empty or abs(float(valor.iloc[0]) - esperado) > 0.001:
            raise ValueError(f"Cuadro 6 {anio}-{mes} {grupo} no coincide: {valor.tolist()} != {esperado}")


def leer_ipc(directorio: Path | str = DIRECTORIO_INEC) -> pd.DataFrame:
    """IPC mensual de 2019, 2022 y diciembre 2025–octubre 2026.

    Las dos bases quedan en la misma tabla y se distinguen por `base` y
    `geografia`. No hay filas empalmadas.
    """
    directorio = Path(directorio)
    _verificar_cuadro5(_archivo(directorio, "*Cuadro 5*"))
    cuadro6 = _leer_cuadro6(_archivo(directorio, "*Cuadro 6*"))
    cuadro8 = _leer_cuadro8(directorio / "Cuadro8_provincia_mensual_2026.xlsx")
    nota = _notas_octubre_2026(directorio / "Cuadro7_provincia_oct2026.xlsx")
    octubre = cuadro8["anio"].eq(2026) & cuadro8["mes"].eq(10)
    cuadro8.loc[octubre, "notas"] = nota

    ipc = pd.concat([cuadro6, cuadro8], ignore_index=True)
    ipc = ipc.sort_values(["base", "fecha", "grupo"]).reset_index(drop=True)
    _verificar_muestra(ipc)
    return validar(ipc, "ipc")
