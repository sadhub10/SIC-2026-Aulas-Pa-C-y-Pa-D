"""Actualiza datos/aves.csv y datos/poblaciones.csv a partir de una nueva salida de preparar_conteos.py,
conservando los ID y las fichas (hábitat, alimentación, descripción) de las especies que ya existían.

Uso: python actualizar_catalogo.py <carpeta_salida_preparar_conteos> <carpeta_datos_de_la_app> [renombres]
  renombres (opcional): pares viejo=nuevo de nombres científicos que son la misma especie con otro nombre,
  separados por coma. Ej: "Tringa semipalmata=Tringa inornata"
Las especies que salen de la lista liberan su ID, y las que entran lo reutilizan.
"""
import re
import sys
import unicodedata

import pandas as pd

CBC, DATOS = sys.argv[1], sys.argv[2]
RENOMBRES = dict(p.split('=') for p in sys.argv[3].split(',')) if len(sys.argv) > 3 else {}
COLUMNAS = ['ID', 'Nombre', 'Nombre científico', 'Hábitat', 'Alimentación', 'Descripción',
            'Imagen', 'Audio', 'Endemismo', 'Amenaza']


def archivo(nombre):
    texto = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '_', texto).strip('_')


nuevo = pd.read_csv(f'{CBC}/especies_cbc_500.csv', dtype=str).fillna('')
series = pd.read_csv(f'{CBC}/conteos_por_decada.csv')
actual = pd.read_csv(f'{DATOS}/aves.csv', dtype=str).fillna('')
actual['Nombre científico'] = actual['Nombre científico'].replace(RENOMBRES)
por_especie = actual.set_index('Nombre científico')

# ID: se conserva el de cada especie que sigue; las nuevas toman los ID que quedaron libres
ids = {e: por_especie.at[e, 'ID'] for e in nuevo.especie if e in por_especie.index}
libres = sorted(set(actual.ID) - set(ids.values()))
for e in nuevo.especie:
    if e not in ids:
        ids[e] = libres.pop(0) if libres else f'AV{len(ids) + 1:03d}'

filas = []
for _, r in nuevo.iterrows():
    previa = por_especie.loc[r.especie] if r.especie in por_especie.index else None
    filas.append({
        'ID': ids[r.especie], 'Nombre': r.nombre_es, 'Nombre científico': r.especie,
        'Hábitat': previa['Hábitat'] if previa is not None else '',
        'Alimentación': previa['Alimentación'] if previa is not None else '',
        'Descripción': previa['Descripción'] if previa is not None else '',
        'Imagen': archivo(r.nombre_es) + '.jpg', 'Audio': archivo(r.nombre_es) + '.mp3',
        'Endemismo': r.endemismo, 'Amenaza': r.amenaza,
    })
aves = pd.DataFrame(filas, columns=COLUMNAS)
assert aves.ID.is_unique and aves.Imagen.is_unique
aves.to_csv(f'{DATOS}/aves.csv', index=False, encoding='utf-8-sig')

largo = series.melt(id_vars='especie', var_name='Década', value_name='Individuos por hora').dropna()
largo['Década'] = largo['Década'].str[1:].astype(int)
largo.insert(0, 'ID', largo.especie.map(ids))
largo.drop(columns='especie').sort_values(['ID', 'Década']) \
    .to_csv(f'{DATOS}/poblaciones.csv', index=False, encoding='utf-8-sig')

entran = [f"{ids[e]} {e}" for e in nuevo.especie if e not in por_especie.index]
salen = [f"{r.ID} {r['Nombre científico']}" for _, r in actual.iterrows() if r['Nombre científico'] not in ids]
print('Especies:', len(aves), '| Entran:', entran, '| Salen:', salen)
