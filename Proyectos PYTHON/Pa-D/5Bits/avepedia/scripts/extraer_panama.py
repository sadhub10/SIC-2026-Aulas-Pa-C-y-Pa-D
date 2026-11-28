# Extrae de un dataset completo del CBC (zip de Audubon) solo los registros de Panamá.
# Uso: python extraer_panama.py <archivo.zip> <carpeta_salida>
import zipfile, io, csv, sys
Z = sys.argv[1]; OUT = sys.argv[2]
z = zipfile.ZipFile(Z)
for n in z.namelist():
    key = n.split('CBC_')[1].replace('.csv','')
    with z.open(n) as f, open(f'{OUT}/pa_{key}.csv','w',newline='',encoding='utf-8') as o:
        r = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', errors='replace'))
        w = csv.writer(o); h = next(r); w.writerow(h)
        ia = h.index('abbrev'); ic = h.index('country_code') if 'country_code' in h else None
        k = 0
        for row in r:
            if row[ia].startswith('RP') or (ic is not None and len(row)>ic and row[ic]=='PA'):
                w.writerow(row); k += 1
        print(key, k)
