"""Normalización de nombres de producto, establecimiento, cadena y zona.

Parte de los CSV de ACODECO trae las tildes en Latin-1 (`ESPAÑA`, `Maíz`).
Otra parte guardó esos mismos bytes en CP850 y, leídos como Latin-1, salen
`ESPA¥A`, `VÖA`, `Ma¡z`. `reparar_texto` deshace solo ese segundo caso.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

_MAPA_PATH = Path(__file__).resolve().parents[1] / "references" / "mapa_productos.csv"

# Caracteres que en estos archivos son CP850 leído como Latin-1, no español.
_MARCAS_CP850 = set("¥Öµà¡¢£¤\x82\x90\xa0")
_ACENTO_ENTRE_MAYUSCULAS = re.compile(r"[A-ZÁÉÍÓÚÑ][áéíóúñ][A-ZÁÉÍÓÚÑ]")
_ASTERISCO_FINAL = re.compile(r"\s*\*\s*$")
_ESPACIOS = re.compile(r"\s+")

_CADENAS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"S[UÚ]PER\s*99"), "Super 99"),
    (re.compile(r"RIBA\s+SMITH"), "Riba Smith"),
    (re.compile(r"MACHETAZO"), "Machetazo"),
    (re.compile(r"\bEL FUERTE\b"), "El Fuerte"),
    (re.compile(r"\bXTRA\b"), "Xtra"),
    (re.compile(r"\bREY\b"), "Rey"),
    (
        re.compile(r"MINI\s*SUPER|MINISUPER|MINI\s*MARKET|MIINIMARKET|\bM/S\b|(?:^|[\s-])MS(?:[\s-]|$)"),
        "minisúper",
    ),
    (re.compile(r"ABARROTER[IÍ]A|\bABT\b|\bABA\b"), "abarrotería"),
    (re.compile(r"FRUTER[IÍ]A"), "frutería"),
)


def _cargar_mapa(path: Path = _MAPA_PATH) -> dict[str, str]:
    mapa: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            mapa[fila["nombre"].strip()] = fila["producto_estandar"].strip()
    return mapa


MAPA_PRODUCTOS = _cargar_mapa()


def reparar_texto(texto: str) -> str:
    """Devuelve el texto con tildes unificadas y espacios simples."""
    if any(caracter in _MARCAS_CP850 for caracter in texto) or _ACENTO_ENTRE_MAYUSCULAS.search(texto):
        texto = texto.encode("latin-1").decode("cp850")
    return _ESPACIOS.sub(" ", texto).strip()


def separar_control(nombre: str) -> tuple[str, bool]:
    """Quita el asterisco final. Ese asterisco marca control de precios."""
    control = _ASTERISCO_FINAL.search(nombre) is not None
    return _ASTERISCO_FINAL.sub("", nombre).strip(), control


def clave_producto(nombre: str) -> str:
    sin_asterisco, _ = separar_control(nombre)
    return reparar_texto(sin_asterisco).lower()


def producto_estandar(nombre: str) -> str:
    clave = clave_producto(nombre)
    if clave in MAPA_PRODUCTOS:
        return MAPA_PRODUCTOS[clave]
    if clave in MAPA_PRODUCTOS.values():
        return clave
    return clave


def normalizar_producto(nombre: str) -> tuple[str, bool]:
    """Nombre estándar en minúsculas y si el original traía control de precios."""
    _, control = separar_control(nombre)
    return producto_estandar(nombre), control


def estandarizar_establecimiento(nombre: str) -> str:
    texto = reparar_texto(nombre).upper()
    texto = re.sub(r"\s*/\s*", "/", texto)
    texto = re.sub(r"\bVÍA\b", "VIA", texto)
    return _ESPACIOS.sub(" ", texto).strip()


def cadena_establecimiento(nombre: str) -> str:
    """Cadena explícita en el nombre. Vacío si el nombre no la dice."""
    estandar = estandarizar_establecimiento(nombre)
    for patron, cadena in _CADENAS:
        if patron.search(estandar):
            return cadena
    return ""


def zona_establecimiento(nombre: str, zona_pdf: str | None = None) -> str:
    """San Miguelito solo si el nombre o el recuadro del PDF lo dicen.

    Bella Vista, Tocumen y el resto quedan `sin_clasificar`: no se asigna
    corregimiento por el texto de la sucursal.
    """
    estandar = estandarizar_establecimiento(nombre)
    if "SAN MIGUELITO" in estandar:
        return "san_miguelito"
    if zona_pdf and "SAN MIGUELITO" in reparar_texto(zona_pdf).upper():
        return "san_miguelito"
    return "sin_clasificar"
