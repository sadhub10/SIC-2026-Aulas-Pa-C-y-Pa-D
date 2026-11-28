"""AquaLytics: limpieza trazable y evaluación descriptiva, sin regresión."""
from pathlib import Path
import json
import zipfile
import time
import hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

BASE = Path(__file__).resolve().parent
MAPA = {
    'pH': ('ph', 'pH'),
    'Specific conductance': ('conductividad_uS_cm', 'µS/cm'),
    'Chloride': ('cloruros_mg_l', 'mg/L'),
    'Fluoride': ('fluoruros_mg_l', 'mg/L'),
    'Sulfate': ('sulfatos_mg_l', 'mg/L'),
    'Hardness, Ca, Mg': ('dureza_mg_l_CaCO3', 'mg/L CaCO3'),
    'Total dissolved solids': ('tds_mg_l', 'mg/L'),
    'Oxygen': ('oxigeno_disuelto_mg_l', 'mg/L'),
    'Dissolved oxygen (DO)': ('oxigeno_disuelto_mg_l', 'mg/L'),
    'Temperature, water': ('temp_agua_C', '°C'),
    'Turbidity': ('turbidez', 'unidad original'),
}
ETIQUETAS = {
    'ph': 'pH', 'conductividad_uS_cm': 'Conductividad (µS/cm)',
    'cloruros_mg_l': 'Cloruros (mg/L)', 'fluoruros_mg_l': 'Fluoruros (mg/L)',
    'sulfatos_mg_l': 'Sulfatos (mg/L)', 'dureza_mg_l_CaCO3': 'Dureza (mg/L CaCO3)',
    'tds_mg_l': 'SDT (mg/L)', 'oxigeno_disuelto_mg_l': 'Oxígeno disuelto (mg/L)',
    'temp_agua_C': 'Temperatura (°C)', 'turbidez_FNU': 'Turbidez (FNU)',
    'turbidez_NTRU': 'Turbidez (NTRU)',
}
CLAVES = ['OrganizationIdentifier', 'ActivityIdentifier']
SITIO = 'MonitoringLocationIdentifier'
FECHA = 'ActivityStartDate'
FUENTE = 'https://asep.gob.pa/wp-content/uploads/agua/legislacion/dgnti_21-2019_mod.pdf'


def reglas():
    return json.loads((BASE / 'limites.json').read_text(encoding='utf-8'))


def normalizar(nombre, unidad, valor):
    """No convierte saturación a mg/L ni turbidez FNU/NTRU a NTU."""
    if nombre not in MAPA:
        return None, np.nan, 'fuera_del_alcance'
    parametro, _ = MAPA[nombre]
    unidad = '' if pd.isna(unidad) else str(unidad).strip().lower()
    valor = pd.to_numeric(valor, errors='coerce')
    if pd.isna(valor) or not np.isfinite(valor):
        return parametro, np.nan, 'sin_valor_numerico'
    if parametro == 'ph':
        if unidad not in ('', 'std units', 'ph units', 'ph'):
            return parametro, np.nan, 'unidad_incompatible'
        return parametro, valor if 0 <= valor <= 14 else np.nan, 'valido' if 0 <= valor <= 14 else 'fisicamente_invalido'
    if parametro == 'turbidez':
        return ('turbidez_' + unidad.upper(), valor, 'valido') if unidad in ('fnu', 'ntru') and valor >= 0 else (parametro, np.nan, 'unidad_incompatible')
    permitidas = {
        'conductividad_uS_cm': ('us/cm', 'us/cm @25c'),
        'dureza_mg_l_CaCO3': ('mg/l caco3',), 'temp_agua_C': ('deg c',),
    }.get(parametro, ('mg/l',))
    if unidad not in permitidas:
        return parametro, np.nan, 'unidad_incompatible'
    if parametro != 'temp_agua_C' and valor < 0:
        return parametro, np.nan, 'fisicamente_invalido'
    return parametro, float(valor), 'valido'


def estado_valor(valor, minimo=None, maximo=None):
    if pd.isna(valor):
        return 'Sin dato'
    fuera = (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo)
    return 'Fuera de referencia' if fuera else 'Dentro de referencia'


def limpiar(original):
    datos = original.drop_duplicates().copy()
    for c in datos.select_dtypes(include='object'):
        datos[c] = datos[c].str.strip().replace('', np.nan)
    datos['fecha'] = pd.to_datetime(datos[FECHA], errors='coerce')
    datos['es_control'] = datos.ActivityTypeCode.fillna('').str.contains('Quality Control', case=False)
    normalizados = [normalizar(n, u, v) for n, u, v in zip(datos.CharacteristicName, datos['ResultMeasure/MeasureUnitCode'], datos.ResultMeasureValue)]
    datos[['parametro', 'valor', 'motivo']] = pd.DataFrame(normalizados, index=datos.index)
    censurado = datos.ResultDetectionConditionText.notna()
    datos.loc[censurado & datos.parametro.notna(), ['valor', 'motivo']] = [np.nan, 'censurado_no_imputado']
    datos.loc[datos.fecha.isna(), ['valor', 'motivo']] = [np.nan, 'fecha_invalida']
    sin_id = datos[CLAVES + [SITIO]].isna().any(axis=1)
    datos.loc[sin_id, ['valor', 'motivo']] = [np.nan, 'identificador_ausente']
    datos['es_preliminar'] = datos.ResultStatusIdentifier.eq('Preliminary')
    datos['es_estimado'] = datos.ResultValueTypeName.eq('Estimated')
    datos['unidad_ph_inferida'] = datos.parametro.eq('ph') & datos['ResultMeasure/MeasureUnitCode'].isna()
    # Se marcan atípicos dentro de cada organismo y parámetro; nunca se eliminan.
    datos['atipico_iqr'] = False
    validos = datos.motivo.eq('valido') & ~datos.es_control
    for _, grupo in datos[validos].groupby(['OrganizationIdentifier', 'parametro']):
        if len(grupo) < 8:
            continue
        q1, q3 = grupo.valor.quantile([.25, .75]); amplitud = q3 - q1
        if amplitud > 0:
            datos.loc[grupo.index, 'atipico_iqr'] = (grupo.valor < q1 - 1.5*amplitud) | (grupo.valor > q3 + 1.5*amplitud)
    return datos


def construir_muestras(datos):
    universo = datos[~datos.es_control & datos.fecha.notna() & datos[CLAVES + [SITIO]].notna().all(axis=1)]
    meta = universo.groupby(CLAVES, as_index=False).agg({SITIO: 'first', FECHA: 'first', 'ActivityMediaSubdivisionName': 'first', 'ActivityTypeCode': 'first'})
    validos = universo[universo.motivo.eq('valido')]
    tabla = validos.pivot_table(index=CLAVES, columns='parametro', values='valor', aggfunc='median').reset_index()
    tabla = meta.merge(tabla, on=CLAVES, how='left')
    for c in ETIQUETAS:
        if c not in tabla: tabla[c] = np.nan
    # Evaluar cada observación, antes de la mediana: una excedencia no desaparece al agregar.
    limites = reglas()['panama']
    detalles = []
    for _, muestra in tabla.iterrows():
        grupo = universo[(universo.OrganizationIdentifier == muestra.OrganizationIdentifier) & (universo.ActivityIdentifier == muestra.ActivityIdentifier)]
        evaluados = fuera = 0
        for parametro, limite in limites.items():
            g = grupo[(grupo.parametro == parametro) & grupo.motivo.eq('valido')]
            estados = [estado_valor(v, limite.get('min'), limite.get('max')) for v in g.valor]
            estado = 'Fuera de referencia' if 'Fuera de referencia' in estados else ('Dentro de referencia' if estados else 'Sin dato')
            evaluados += bool(estados); fuera += estado == 'Fuera de referencia'
            detalles.append({**{k: muestra[k] for k in CLAVES + [SITIO, FECHA]}, 'parametro': parametro,
                             'estado': estado, 'n_mediciones': len(g), 'min_observado': g.valor.min(), 'max_observado': g.valor.max(),
                             'fracciones': '|'.join(sorted(g.ResultSampleFractionText.dropna().unique())),
                             'preliminar': bool(g.es_preliminar.any()), 'estimado': bool(g.es_estimado.any())})
        indice = muestra.name
        tabla.loc[indice, 'parametros_evaluados'] = evaluados
        tabla.loc[indice, 'parametros_fuera'] = fuera
        tabla.loc[indice, 'estado'] = 'Con excedencias' if fuera else ('Sin excedencias observadas' if evaluados else 'Sin datos evaluables')
        tabla.loc[indice, 'cobertura_pct'] = 100*evaluados/len(limites)
        tabla.loc[indice, 'preliminar'] = bool(grupo.es_preliminar.any())
        tabla.loc[indice, 'estimado'] = bool(grupo.es_estimado.any())
    tabla['potabilidad'] = 'No determinada'
    return tabla, pd.DataFrame(detalles)


def auditar_pivote(datos, pivote):
    """Comparación por estación y fecha sólo para auditar el agregado suministrado."""
    g = datos[(~datos.es_control) & datos.motivo.eq('valido')]
    reconstruido = g.pivot_table(index=[SITIO, FECHA], columns='parametro', values='valor', aggfunc='mean').reset_index()
    unido = pivote.merge(reconstruido, on=[SITIO, FECHA], how='outer', suffixes=('_adjunto', '_reconstruido'), indicator=True)
    filas = []
    for _, r in unido.iterrows():
        for p in sorted(set(pivote.columns) & set(ETIQUETAS)):
            a, b = r.get(p+'_adjunto', np.nan), r.get(p+'_reconstruido', np.nan)
            iguales = (pd.isna(a) and pd.isna(b)) or (pd.notna(a) and pd.notna(b) and np.isclose(a,b,rtol=1e-6,atol=1e-8))
            if not iguales:
                filas.append({SITIO:r[SITIO], FECHA:r[FECHA], 'parametro':p, 'valor_adjunto':a, 'valor_reconstruido':b, 'coincidencia_clave':r['_merge']})
    return pd.DataFrame(filas)


def visualizar(tabla, resumen, salida):
    sns.set_theme(style='whitegrid', font_scale=.95)
    plt.rcParams.update({'figure.dpi':130, 'savefig.dpi':160})
    rutas=[]
    def guardar(nombre):
        plt.tight_layout(); ruta=salida / f'{nombre}.png'; plt.savefig(ruta,bbox_inches='tight');plt.close();rutas.append(ruta)
    cols=list(ETIQUETAS)
    faltantes=tabla[cols].isna().mean().mul(100).sort_values()
    plt.figure(figsize=(9,5));plt.barh([ETIQUETAS[c] for c in faltantes.index],faltantes,color='#285e73');plt.xlim(0,105);plt.xlabel('Actividades sin medición válida (%)');plt.title('Cobertura de los parámetros');guardar('01_faltantes')
    fig,ejes=plt.subplots(3,3,figsize=(11,9))
    for eje,p in zip(ejes.flat,cols[:9]):
        v=tabla[p].dropna();eje.hist(v,bins=20,color='#3a8195',edgecolor='white');eje.set_title(f'{ETIQUETAS[p]} · n={len(v)}',fontsize=10);eje.set_ylabel('Actividades')
        r=reglas()['panama'].get(p,{})
        for limite in [r.get('min'),r.get('max')]:
            if limite is not None:eje.axvline(limite,color='#b54435',linestyle='--')
    fig.suptitle('Distribuciones y referencias panameñas',y=1.01);guardar('02_distribuciones')
    plt.figure(figsize=(9,5)); colores=['#b54435' if x else '#285e73' for x in resumen.fuera]
    plt.barh([ETIQUETAS[x] for x in resumen.parametro],resumen.porcentaje_fuera,color=colores)
    for i,r in resumen.iterrows():plt.text(r.porcentaje_fuera+.7,i,f'{int(r.fuera)}/{int(r.evaluables)}',va='center')
    plt.xlim(0,110);plt.xlabel('Fuera de referencia entre actividades evaluables (%)');plt.title('Excedencias por parámetro · el denominador cambia');guardar('03_excedencias')
    corr=tabla[cols[:9]].corr(method='spearman',min_periods=20)
    pares=tabla[cols[:9]].notna().astype(int).T @ tabla[cols[:9]].notna().astype(int)
    corr.to_csv(salida.parent/'correlaciones_spearman.csv');pares.to_csv(salida.parent/'n_pares_correlacion.csv')
    plt.figure(figsize=(10,8));sns.heatmap(corr.rename(index=ETIQUETAS,columns=ETIQUETAS),annot=True,fmt='.2f',vmin=-1,vmax=1,cmap='vlag',mask=corr.isna().to_numpy(),square=True);plt.title('Spearman · mínimo 20 pares · asociación, sin causalidad');guardar('04_spearman')
    plt.figure(figsize=(9,5))
    for org,g in tabla.groupby('OrganizationIdentifier'):
        plt.scatter(g.conductividad_uS_cm,g.cloruros_mg_l,label=org,alpha=.6,s=24)
    plt.xscale('symlog',linthresh=1);plt.yscale('symlog',linthresh=1);plt.xlabel('Conductividad (µS/cm), escala symlog');plt.ylabel('Cloruros (mg/L), escala symlog');plt.legend();plt.title('Relación entre conductividad y cloruros');guardar('05_dispersion')
    plt.figure(figsize=(9,5));sitios=tabla[SITIO].value_counts().head(5).index
    for sitio,g in tabla[tabla[SITIO].isin(sitios)].groupby(SITIO):
        g=g.sort_values(FECHA);plt.plot(pd.to_datetime(g[FECHA]),g.ph,marker='.',label=sitio)
    plt.axhspan(6.5,8.5,color='#abd5b1',alpha=.25);plt.ylabel('pH');plt.title('pH en los cinco sitios con más actividades');plt.legend(fontsize=7);guardar('06_serie_ph')
    plt.figure(figsize=(9,4));conteos=tabla.estado.value_counts();plt.barh(conteos.index,conteos.values,color='#285e73');plt.xlabel('Actividades rutinarias y observaciones de campo');plt.title('Resultado de la evaluación parcial');guardar('07_estados')
    fig,ejes=plt.subplots(1,2,figsize=(10,4))
    for eje,p in zip(ejes,['conductividad_uS_cm','ph']):
        sns.boxplot(data=tabla,x='OrganizationIdentifier',y=p,ax=eje,color='#b8d7df',fliersize=3);eje.set_xlabel('Organismo');eje.set_ylabel(ETIQUETAS[p])
    ejes[0].set_yscale('log');ejes[0].set_ylim(3,25000);fig.suptitle('Distribuciones por organismo · atípicos conservados');guardar('08_cajas')
    return rutas


def ejecutar():
    inicio=time.perf_counter(); salida=BASE/'datos/procesados';salida.mkdir(parents=True,exist_ok=True)
    resultados=BASE/'resultados';(resultados/'graficos').mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(BASE/'datos/originales/resultphyschem.zip') as z:
        with z.open('resultphyschem.csv') as f: original=pd.read_csv(f,low_memory=False)
    pivote=pd.read_csv(BASE/'datos/originales/tabla_calidad_agua_pivoteada.csv')
    datos=limpiar(original);tabla,detalles=construir_muestras(datos)
    auditoria=auditar_pivote(datos,pivote)
    resumen=detalles.groupby('parametro').agg(evaluables=('n_mediciones',lambda x:int((x>0).sum())),fuera=('estado',lambda x:int(x.eq('Fuera de referencia').sum()))).reset_index()
    resumen['porcentaje_fuera']=100*resumen.fuera/resumen.evaluables.replace(0,np.nan)
    datos.to_csv(salida/'mediciones_auditadas.csv',index=False)
    datos[datos.motivo.ne('valido')].to_csv(salida/'registros_no_utilizados.csv',index=False)
    datos[datos.es_control].to_csv(salida/'controles_calidad.csv',index=False)
    tabla.to_csv(salida/'muestras_limpias.csv',index=False)
    detalles.to_csv(salida/'evaluacion_por_parametro.csv',index=False)
    auditoria.to_csv(salida/'diferencias_pivote_adjunto.csv',index=False)
    resumen.to_csv(resultados/'resumen_excedencias.csv',index=False)
    tabla[list(ETIQUETAS)].describe(percentiles=[.25,.5,.75,.9]).T.to_csv(resultados/'estadisticas_descriptivas.csv')
    tabla[list(ETIQUETAS)].isna().sum().rename('faltantes').to_csv(resultados/'faltantes.csv')
    # Sensibilidad: solamente datos aceptados/finales y no estimados.
    fiables=datos[~datos.es_preliminar & ~datos.es_estimado]
    tabla_fiable,detalle_fiable=construir_muestras(fiables)
    tabla_fiable.to_csv(salida/'sensibilidad_aceptados_finales.csv',index=False)
    for ruta in (BASE/'datos/originales').iterdir():
        assert ruta.is_file()
    indicadores={
        'filas_originales':len(original), 'columnas_originales':len(original.columns),
        'filas_pivote_adjunto':len(pivote), 'duplicados_exactos':int(original.duplicated().sum()),
        'actividades':len(tabla), 'sitios':int(tabla[SITIO].nunique()),
        'fecha_min':tabla[FECHA].min(), 'fecha_max':tabla[FECHA].max(),
        'filas_control_calidad':int(datos.es_control.sum()),
        'mediciones_validas_rutinarias':int((datos.motivo.eq('valido') & ~datos.es_control).sum()),
        'atipicos_conservados':int(datos.atipico_iqr.sum()),
        'motivos':datos.motivo.value_counts().to_dict(),
        'estados':tabla.estado.value_counts().to_dict(),
        'actividades_preliminares':int(tabla.preliminar.sum()),
        'actividades_estimadas':int(tabla.estimado.sum()),
        'cobertura_mediana_pct':float(tabla.cobertura_pct.median()),
        'diferencias_pivote':len(auditoria),
        'diferencias_por_parametro':auditoria.parametro.value_counts().to_dict() if len(auditoria) else {},
        'sensibilidad_actividades':len(tabla_fiable),
        'sensibilidad_estados':tabla_fiable.estado.value_counts().to_dict(),
        'segundos_limpieza_y_evaluacion':round(time.perf_counter()-inicio,3),
        'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'datos/originales').iterdir()},
    }
    rutas=visualizar(tabla,resumen,resultados/'graficos')
    (resultados/'indicadores.json').write_text(json.dumps(indicadores,ensure_ascii=False,indent=2),encoding='utf-8')
    from panel import crear_panel
    crear_panel(tabla,detalles,resumen,indicadores,rutas)
    return tabla,detalles,resumen,indicadores


if __name__=='__main__':
    _,_,_,indicadores=ejecutar()
    print(json.dumps(indicadores,ensure_ascii=False,indent=2))
