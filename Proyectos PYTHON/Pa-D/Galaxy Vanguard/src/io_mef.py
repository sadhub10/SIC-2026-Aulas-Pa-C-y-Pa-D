"""Costo calórico familiar del MEF para Panamá y San Miguelito.

De cada informe se toma la cifra de la introducción, la de los distritos de
Panamá y San Miguelito. No se usa el costo «sin control de precios» ni el del
Resto urbano. Enero y febrero de 2026 vienen en un solo PDF y salen como dos
filas. Agosto de 2022 no está publicado.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pdfplumber

from esquemas import validar

_RAIZ = Path(__file__).resolve().parents[1]
DIRECTORIO_MEF = _RAIZ / "data" / "raw" / "mef"
_NOMBRE = re.compile(r"mef_(\d{4})_(\d{2})(?:-(\d{2}))?\.pdf$")
_MONTO = re.compile(r"B/\.(\d{3}\.\d{2})")
_EXCLUIR = re.compile(r"hubiese|no existir|sin la medida|de no existir", re.IGNORECASE)
_NOTA = "MEF: costo calórico familiar; no comparable 1:1 con ACODECO."

# Cifras ya leídas en references/plan_datos.md, sección 1.3.
_VERIFICADO = {
    (2019, 1): 306.08,
    (2019, 2): 304.59,
    (2019, 3): 304.61,
    (2019, 4): 306.76,
    (2019, 5): 308.21,
    (2019, 6): 308.99,
    (2019, 7): 310.38,
    (2019, 8): 308.25,
    (2019, 9): 310.04,
    (2019, 10): 310.06,
    (2019, 11): 306.42,
    (2019, 12): 306.68,
    (2022, 1): 318.12,
    (2022, 6): 330.40,
    (2026, 8): 369.21,
}


def _texto(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        paginas = pdf.pages[:15]
        return " ".join(" ".join((pagina.extract_text() or "").split()) for pagina in paginas)


def _montos(texto: str) -> list[float]:
    """Montos de canasta asociados a Panamá y San Miguelito, en orden de aparición."""
    frases = re.split(r"(?<=\.)\s+", texto)
    encontrados: list[float] = []
    for frase in frases:
        if _EXCLUIR.search(frase) or not re.search(r"San Miguelito", frase, re.IGNORECASE):
            continue
        corte = re.search(r"Resto urbano", frase, re.IGNORECASE)
        trozo = frase[: corte.start()] if corte else frase
        for coincidencia in _MONTO.finditer(trozo):
            antes = trozo[max(0, coincidencia.start() - 18) : coincidencia.start()]
            if re.search(r"Costo total\s*$", antes, re.IGNORECASE):
                continue
            valor = float(coincidencia.group(1))
            if valor >= 250 and valor not in encontrados:
                encontrados.append(valor)
    return encontrados


def _meses(path: Path, montos: list[float]) -> list[tuple[int, int, float]]:
    coincidencia = _NOMBRE.search(path.name)
    if coincidencia is None:
        raise ValueError(f"Nombre de informe no reconocido: {path.name}")
    anio = int(coincidencia.group(1))
    mes_inicio = int(coincidencia.group(2))
    mes_fin = coincidencia.group(3)
    if not montos:
        raise ValueError(f"{path.name}: no aparece el costo de Panamá y San Miguelito")
    if mes_fin is None:
        return [(anio, mes_inicio, montos[0])]
    if len(montos) < 2:
        raise ValueError(f"{path.name}: el informe trae dos meses y solo se leyó {montos}")
    # El informe habla primero de febrero y luego compara con enero.
    return [(anio, mes_inicio, montos[1]), (anio, int(mes_fin), montos[0])]


def leer_costo_mef(directorio: Path | str = DIRECTORIO_MEF) -> pd.DataFrame:
    """Una fila por mes disponible de 2019, 2022 y 2026."""
    directorio = Path(directorio)
    archivos = sorted(directorio.glob("*/*.pdf"))
    if not archivos:
        raise FileNotFoundError(f"No hay informes del MEF en {directorio}")
    registros = []
    for archivo in archivos:
        for anio, mes, costo in _meses(archivo, _montos(_texto(archivo))):
            registros.append(
                {
                    "fecha": pd.Timestamp(anio, mes, 1),
                    "anio": anio,
                    "mes": mes,
                    "fuente": "mef_cbfa",
                    "geografia": "panama_y_san_miguelito",
                    "n_productos": 59,
                    "costo_total": costo,
                    "notas": _NOTA,
                }
            )
    costo = pd.DataFrame(registros).sort_values("fecha").reset_index(drop=True)
    if costo.duplicated(["anio", "mes"]).any():
        raise ValueError("Hay dos costos del MEF para el mismo mes")
    if ((costo["anio"] == 2022) & (costo["mes"] == 8)).any():
        raise ValueError("Agosto de 2022 no está en el catálogo del MEF")
    for (anio, mes), esperado in _VERIFICADO.items():
        valor = costo.loc[costo["anio"].eq(anio) & costo["mes"].eq(mes), "costo_total"]
        if valor.empty or abs(float(valor.iloc[0]) - esperado) > 0.001:
            raise ValueError(f"MEF {anio}-{mes:02d} no coincide: {valor.tolist()} != {esperado}")
    conteo = costo.groupby("anio").size().to_dict()
    if conteo != {2019: 12, 2022: 11, 2026: 8}:
        raise ValueError(f"Se esperaban 12, 11 y 8 meses y hay {conteo}")
    return validar(costo, "costo_canasta_mensual")
