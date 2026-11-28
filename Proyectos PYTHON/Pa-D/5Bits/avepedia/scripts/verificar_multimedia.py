"""Comprueba que cada ave de datos/aves.csv tenga su fotografía y su canto, y que se puedan abrir.

Uso (desde la carpeta principal del proyecto):
    .venv39\\Scripts\\python scripts\\verificar_multimedia.py

Genera reporte_multimedia.csv con el estado de cada ave.
"""
import os
import sys
from pathlib import Path

import pandas as pd
from PIL import Image

BASE = Path(__file__).resolve().parent.parent
IMAGENES, AUDIOS = BASE / 'imagenes', BASE / 'audios'
FOTO_GRANDE_MB = 1.0      # la app muestra la foto a 160x120: más de 1 MB es innecesario
AUDIO_GRANDE_MB = 3.0

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
try:
    import pygame
    pygame.mixer.init()
except Exception:
    pygame = None
    print('Aviso: no se pudo iniciar el audio; solo se revisará que los cantos existan.')

aves = pd.read_csv(BASE / 'datos' / 'aves.csv', dtype=str).fillna('')


def revisar_foto(nombre):
    ruta = IMAGENES / nombre
    if not ruta.is_file():
        return 'FALTA', 0
    mb = ruta.stat().st_size / 1e6
    try:
        with Image.open(ruta) as img:
            img.verify()
    except Exception:
        return 'NO SE ABRE', mb
    return ('PESADA' if mb > FOTO_GRANDE_MB else 'OK'), mb


def revisar_audio(nombre):
    ruta = AUDIOS / nombre
    if not ruta.is_file():
        return 'FALTA', 0
    mb = ruta.stat().st_size / 1e6
    if pygame:
        try:
            pygame.mixer.music.load(str(ruta))
        except Exception:
            return 'NO SE ABRE', mb
    return ('PESADO' if mb > AUDIO_GRANDE_MB else 'OK'), mb


filas = []
for _, ave in aves.iterrows():
    foto, mb_foto = revisar_foto(ave['Imagen'])
    audio, mb_audio = revisar_audio(ave['Audio'])
    filas.append([ave['ID'], ave['Nombre'], ave['Imagen'], foto, round(mb_foto, 2),
                  ave['Audio'], audio, round(mb_audio, 2)])
reporte = pd.DataFrame(filas, columns=['ID', 'Nombre', 'Imagen', 'Estado foto', 'MB foto',
                                       'Audio', 'Estado audio', 'MB audio'])
reporte.to_csv(BASE / 'reporte_multimedia.csv', index=False, encoding='utf-8-sig')

# Archivos que sobran: están en las carpetas pero ninguna ave los usa (casi siempre, un nombre mal escrito)
sobran_fotos = sorted({f.name for f in IMAGENES.iterdir() if f.is_file()} - set(aves['Imagen']) - {'.gitkeep'}) \
    if IMAGENES.is_dir() else []
sobran_audios = sorted({f.name for f in AUDIOS.iterdir() if f.is_file()} - set(aves['Audio']) - {'.gitkeep'}) \
    if AUDIOS.is_dir() else []

print(f'\nAves revisadas: {len(aves)}')
print('Fotos: ', reporte['Estado foto'].value_counts().to_dict())
print('Cantos:', reporte['Estado audio'].value_counts().to_dict())
print(f"Peso total: fotos {reporte['MB foto'].sum():.0f} MB, cantos {reporte['MB audio'].sum():.0f} MB")
for titulo, lista in [('Fotos que ninguna ave usa', sobran_fotos), ('Cantos que ninguna ave usa', sobran_audios)]:
    if lista:
        print(f'\n{titulo} ({len(lista)}): ' + ', '.join(lista[:15]) + (' ...' if len(lista) > 15 else ''))
problemas = reporte[(reporte['Estado foto'] != 'OK') | (reporte['Estado audio'] != 'OK')]
if problemas.empty and not sobran_fotos and not sobran_audios:
    print('\nTodo en orden.')
else:
    print(f'\nAves con algún problema: {len(problemas)}. Detalle en reporte_multimedia.csv')
    print(problemas.head(10).to_string(index=False))
sys.exit(0)
