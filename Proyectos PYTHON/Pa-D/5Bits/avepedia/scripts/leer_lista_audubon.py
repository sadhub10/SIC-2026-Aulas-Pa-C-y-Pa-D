"""Convierte el PDF 'Lista de las aves de la República de Panamá 2026' (texto de pdftotext -layout) en CSV."""
import re, sys, csv
txt, out = sys.argv[1], sys.argv[2]
filas = []
for linea in open(txt, encoding='utf-8'):
    m = re.match(r'^\s*(\d{1,4})\s+(.+)$', linea.rstrip())
    if not m:
        continue
    partes = re.split(r'\s{2,}', m.group(2).strip())
    if int(m.group(1)) > 1100 or len(partes) < 3 or not re.match(r'^[A-Z][a-z]+ [a-z]+', partes[2]):
        continue
    resto = partes[3:]
    filas.append([int(m.group(1)), partes[0], partes[1], partes[2],
                  resto[0] if len(resto) > 1 else (resto[0] if resto and not re.search(r'VU|EN|CR|NT', resto[0]) else ''),
                  resto[-1] if resto and re.search(r'VU|EN|CR|NT', resto[-1]) else ''])
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['no', 'nombre_es', 'nombre_en', 'nombre_cientifico', 'endemismo', 'amenaza']); w.writerows(filas)
print(len(filas))
