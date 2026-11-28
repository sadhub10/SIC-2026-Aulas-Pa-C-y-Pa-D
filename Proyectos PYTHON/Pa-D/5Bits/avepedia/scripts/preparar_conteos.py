"""Prepara los datos del Conteo Navideño de Aves (Audubon CBC) de Panamá para AviPedia.

Uso: python preparar_conteos.py <carpeta_con_csv_de_panama> <carpeta_salida> <lista_aves_panama_2026.csv>
Entrada: pa_Circle_Species_Report.csv y pa_Effort_Many_Types_Report.csv (ya filtrados a Panamá)
         y la Lista de las aves de la República de Panamá 2026 (Sociedad Audubon de Panamá) en CSV.
Los nombres del CBC se convierten a la taxonomía de la lista oficial 2026; cuando una especie
se dividió, se usa la forma presente en el centro de Panamá.
Salida:
  conteos_panama.csv      -> una fila por especie, círculo y año (individuos, horas-grupo)
  especies_cbc_500.csv    -> las 500 especies más registradas, con su ranking
  conteos_por_decada.csv  -> índice de individuos por hora-grupo, por especie y década
"""
import re, sys
import pandas as pd

ENT, SAL, LISTA = sys.argv[1], sys.argv[2], sys.argv[3]
N_ESPECIES = 500
# Especies que se incluyen siempre aunque no estén entre las más registradas
# (ocupan el lugar de las últimas del ranking). Harpia harpyja: ave nacional de Panamá.
INCLUIR_SIEMPRE = ['Harpia harpyja']
# Círculos con conteos regulares (los de 1-3 años no sirven para tendencias)
CIRCULOS = {'RPAC': 'Atlántico', 'RPPC': 'Pacífico', 'RPCC': 'Central',
            'RPVC': 'Volcán', 'RPPL': 'Puerto Lara', 'RPGY': 'Guna Yala', 'RPCD': 'Cana'}


# Nombre del CBC -> nombre de la lista oficial 2026 (divisiones, fusiones y cambios no
# detectables por nombre científico ni por nombre en inglés)
EQUIVALENCIAS = {
    'Troglodytes aedon': 'Troglodytes musculus', 'Bubulcus ibis': 'Ardea ibis',
    'Polioptila plumbea': 'Polioptila bilineata', 'Cantorchilus modestus': 'Cantorchilus elutus',
    'Zimmerius vilissimus': 'Zimmerius parvus', 'Xenops minutus': 'Xenops mexicanus',
    'Tolmomyias assimilis': 'Tolmomyias flavotectus', 'Rhynchocyclus olivaceus': 'Rhynchocyclus aequinoctialis',
    'Sporophila americana': 'Sporophila corvina', 'Camptostoma obsoletum': 'Camptostoma flaviventre',
    'Trogon rufus': 'Trogon tenellus', 'Trogon violaceus': 'Trogon caligatus',
    'Lepidothrix coronata': 'Lepidothrix velutina', 'Momotus momota': 'Momotus subrufescens',
    'Contopus cinereus': 'Contopus bogotensis', 'Notharchus macrorhynchos': 'Notharchus hyperrhynchus',
    'Basileuterus rufifrons': 'Basileuterus delattrii', 'Gymnopithys leucaspis': 'Gymnopithys bicolor',
    'Phaethornis longuemareus': 'Phaethornis striigularis', 'Phaethornis superciliosus': 'Phaethornis longirostris',
    'Numenius phaeopus': 'Numenius hudsonicus', 'Schiffornis turdina': 'Schiffornis veraepacis',
    'Microcerculus philomela': 'Microcerculus marginatus', 'Tyto alba': 'Tyto furcata',
    'Deconychura longicauda': 'Deconychura typica', 'Myrmotherula surinamensis': 'Myrmotherula pacifica',
    'Myrmotherula brachyura': 'Myrmotherula ignota', 'Larus argentatus': 'Larus smithsonianus',
    'Chlorostilbon canivetii': 'Chlorostilbon assimilis', 'Eugenes fulgens': 'Eugenes spectabilis',
    'Colibri thalassinus': 'Colibri cyanotus', 'Pselliophorus tibialis': 'Atlapetes tibialis',
    'Myiopagis caniceps': 'Myiopagis parambae', 'Ramphocelus costaricensis': 'Ramphocelus passerinii',
    'Mitrephanes phaeocercus': 'Mitrephanes aurantiiventris',
    'Sirystes sibilator': 'Sirystes albogriseus', 'Thamnophilus punctatus': 'Thamnophilus atrinucha',
    'Herpsilochmus rufimarginatus': 'Herpsilochmus frater', 'Myiodynastes chrysocephalus': 'Myiodynastes hemichrysus',
    'Trogon aurantiiventris': 'Trogon collaris', 'Phyllomyias burmeisteri': 'Acrochordopus zeledoni',
    'Myrmeciza immaculata': 'Hafferia zeledoni', 'Basileuterus tristriatus': 'Basileuterus melanotis',
    'Momotus coeruliceps': 'Momotus lessonii',
}


# Registros del CBC sin subespecie que en Panamá corresponden a otra especie de la lista 2026.
# 'Yellow Warbler' sin grupo = migratoria norteña (la manglera viene marcada como [erithachorides Group]).
# 'Willet' = Playero Aliblanco Occidental, el abundante en Panamá.
NOMBRE_COMPLETO = {
    'Setophaga petechia': 'Setophaga aestiva',
    'Tringa semipalmata': 'Tringa inornata',
    # Mismo ave registrada con un nombre antiguo y luego con el actual (cambio de nombre en el CBC)
    'Buteo plagiatus': 'Buteo nitidus',          # hasta 2016 -> desde 2017
    'Amazona oratrix': 'Amazona ochrocephala',   # hasta 1982 -> desde 1983
}


def normal(t):
    return re.sub(r'[^a-z]', '', re.sub(r'\s*\(.*\)', '', str(t)).lower())


def a_especie(nombre):
    """Reduce un nombre del CBC a 'Género especie'. Devuelve None para registros
    que no son una especie concreta (sp., híbridos, pares con '/')."""
    if not isinstance(nombre, str):
        return None
    if re.search(r' sp\.|/| x |dae |formes', nombre):
        return None
    nombre = re.sub(r'\s*[\[\(].*$', '', nombre).strip()
    partes = nombre.split()
    return ' '.join(partes[:2]) if len(partes) >= 2 else None


# 1. Esfuerzo: horas-grupo totales por círculo y temporada
esf = pd.read_csv(f'{ENT}/pa_Effort_Many_Types_Report.csv')
horas = esf.groupby(['abbrev', 'count_yr'], as_index=False)['hours'].sum()
horas = horas[horas.abbrev.isin(CIRCULOS) & (horas.hours > 0)]

# 2. Conteos por especie
sp = pd.read_csv(f'{ENT}/pa_Circle_Species_Report.csv')
sp = sp[sp.abbrev.isin(CIRCULOS)].copy()
sp['especie'] = sp.sci_name.map(a_especie)
sp.loc[sp.sci_name.isin(NOMBRE_COMPLETO), 'especie'] = sp.sci_name.map(NOMBRE_COMPLETO)
sp = sp.dropna(subset=['especie'])

# Pasar a la taxonomía de la lista oficial 2026
lista = pd.read_csv(LISTA)
oficiales = set(lista.nombre_cientifico)
por_ingles = {normal(e): c for e, c in zip(lista.nombre_en, lista.nombre_cientifico)}
ingles_cbc = sp.groupby('especie').com_name.agg(lambda s: s.mode().iat[0])
def a_oficial(esp):
    if esp in oficiales:
        return esp
    if esp in EQUIVALENCIAS:
        return EQUIVALENCIAS[esp]
    return por_ingles.get(normal(ingles_cbc[esp]), esp)
sp['especie'] = sp.especie.map(a_oficial)
sin_lista = sorted(set(sp.especie) - oficiales)
if sin_lista:
    print('Sin equivalencia en la lista oficial:', sin_lista)
cont = sp.groupby(['especie', 'abbrev', 'count_yr'], as_index=False).how_many.sum()

# Solo conteos con esfuerzo registrado
cont = cont.merge(horas, on=['abbrev', 'count_yr'])
cont['anio'] = cont.count_yr + 1899          # conteo 74 = diciembre de 1973
cont['circulo'] = cont.abbrev.map(CIRCULOS)
cont.rename(columns={'how_many': 'individuos', 'hours': 'horas_grupo'}) \
    [['especie', 'circulo', 'anio', 'individuos', 'horas_grupo']] \
    .sort_values(['especie', 'anio', 'circulo']).to_csv(f'{SAL}/conteos_panama.csv', index=False)

# 3. Ranking: en cuántos conteos (círculo-año) apareció la especie con al menos 1 individuo
pos = cont[cont.how_many > 0]
rk = pos.groupby('especie').agg(conteos_con_registro=('count_yr', 'size'),
                                individuos_total=('how_many', 'sum')).reset_index()
rk = rk.sort_values(['conteos_con_registro', 'individuos_total'], ascending=False)
forzadas = pd.DataFrame({'especie': INCLUIR_SIEMPRE}).merge(rk, how='left').fillna(0)
rk = pd.concat([rk[~rk.especie.isin(INCLUIR_SIEMPRE)].head(N_ESPECIES - len(forzadas)), forzadas])
rk[['conteos_con_registro', 'individuos_total']] = rk[['conteos_con_registro', 'individuos_total']].astype(int)
rk.insert(0, 'ranking', range(1, len(rk) + 1))
info = lista.set_index('nombre_cientifico')
rk.insert(2, 'nombre_es', rk.especie.map(info.nombre_es))
rk.insert(3, 'nombre_en', rk.especie.map(info.nombre_en))
rk['endemismo'] = rk.especie.map(info.endemismo)
rk['amenaza'] = rk.especie.map(info.amenaza)
rk.to_csv(f'{SAL}/especies_cbc_500.csv', index=False)

# 4. Índice por década. Para cada especie se usan solo los círculos donde ha sido
#    registrada alguna vez; un conteo de esos círculos sin la especie cuenta como 0.
horas['anio'] = horas.count_yr + 1899
horas['decada'] = horas.anio // 10 * 10
filas = []
for esp in rk.especie:
    circs = pos.loc[pos.especie == esp, 'abbrev'].unique()
    h = horas[horas.abbrev.isin(circs)]
    c = cont[(cont.especie == esp) & cont.abbrev.isin(circs)]
    m = h.merge(c[['abbrev', 'count_yr', 'how_many']], on=['abbrev', 'count_yr'], how='left').fillna({'how_many': 0})
    d = m.groupby('decada').agg(ind=('how_many', 'sum'), hrs=('hours', 'sum'))
    for dec, r in d.iterrows():
        filas.append((esp, dec, round(r.ind / r.hrs, 4)))
tab = pd.DataFrame(filas, columns=['especie', 'decada', 'ind_por_hora'])
tab = tab.pivot(index='especie', columns='decada', values='ind_por_hora')
tab.columns = [f'd{c}' for c in tab.columns]
tab = tab.reindex(rk.especie).reset_index()
tab.to_csv(f'{SAL}/conteos_por_decada.csv', index=False)
print('Especies:', len(rk), '| Conteos:', len(horas), '| Década', list(tab.columns[1:]))
