import re
import unicodedata
import webbrowser
from collections import Counter
from csv import DictReader
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
import pandas as pd
from PIL import Image, ImageOps
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    import pygame
    pygame.mixer.init()
    AUDIO_DISPONIBLE = True
except Exception:
    AUDIO_DISPONIBLE = False

BASE = Path(__file__).resolve().parent
DATOS = BASE / 'datos'
DATOS_MODIFICADOS = DATOS / 'datos_modificados'
IMAGENES = BASE / 'imagenes'
AUDIOS = BASE / 'audios'
for carpeta in (DATOS, DATOS_MODIFICADOS, IMAGENES, AUDIOS):
    carpeta.mkdir(exist_ok=True)

ARCHIVO_AVES = DATOS_MODIFICADOS / 'aves.csv'
ARCHIVO_AVISTAMIENTOS = DATOS / 'avistamientos.csv'
ARCHIVO_POBLACIONES = DATOS_MODIFICADOS / 'poblaciones.csv'

COLUMNAS_AVES = ['ID', 'Nombre', 'Nombre científico', 'Hábitat', 'Alimentación',
                 'Descripción', 'Imagen', 'Audio', 'Endemismo', 'Amenaza']
COLUMNAS_POBLACIONES = ['ID', 'Década', 'Individuos por hora']
COLUMNAS_AVISTAMIENTOS = ['ID', 'Fecha', 'Ubicación', 'Comentario']
AVES_POR_PAGINA = 25
TODOS_LOS_HABITATS = 'Todos los hábitats'

# Códigos de la Lista de las aves de la República de Panamá 2026 (Sociedad Audubon de Panamá)
REGIONES_ENDEMISMO = {
    'BC': 'tierras bajas del Caribe occidental',
    'AO': 'tierras altas del oeste (Costa Rica y Panamá)',
    'BP': 'tierras bajas del Pacífico occidental',
    'BE': 'tierras bajas del este (Darién)',
    'AE': 'tierras altas del este (Darién)',
}
NIVELES_AMENAZA = {'CR': 'en peligro crítico', 'EN': 'amenazada', 'VU': 'vulnerable', 'NT': 'casi amenazada'}

# Si falta algún archivo se crea vacío, para que la aplicación abra igual.
for archivo, columnas in [(ARCHIVO_AVES, COLUMNAS_AVES),
                          (ARCHIVO_POBLACIONES, COLUMNAS_POBLACIONES),
                          (ARCHIVO_AVISTAMIENTOS, COLUMNAS_AVISTAMIENTOS)]:
    if not archivo.exists():
        pd.DataFrame(columns=columnas).to_csv(archivo, index=False, encoding='utf-8-sig')

aves = pd.read_csv(ARCHIVO_AVES, dtype=str).fillna('')
for columna in COLUMNAS_AVES:
    if columna not in aves.columns:
        aves[columna] = ''


def sin_acentos(texto):
    # 'Tucán' -> 'tucan', para que la búsqueda no dependa de tildes ni mayúsculas
    texto = unicodedata.normalize('NFKD', str(texto))
    return ''.join(c for c in texto if not unicodedata.combining(c)).lower()


texto_busqueda = (aves['Nombre'] + ' ' + aves['Nombre científico']).map(sin_acentos)
poblaciones = pd.read_csv(ARCHIVO_POBLACIONES)
avistamientos = pd.read_csv(ARCHIVO_AVISTAMIENTOS, dtype=str).fillna('')
creditos = {}
archivo_creditos = DATOS_MODIFICADOS / 'multimedia.csv'
if archivo_creditos.is_file():
    with archivo_creditos.open(encoding='utf-8-sig', newline='') as archivo:
        creditos = {(fila['Especie del catálogo'], fila['Archivo']): fila for fila in DictReader(archivo)}

# Paleta de la guía de campo.
BOSQUE = '#193D32'
VERDE = '#30694D'
PAPEL = '#F6F4EA'
TINTA = '#203B30'
SECUNDARIO = '#526759'
ALERTA = '#944513'

ctk.set_appearance_mode('light')
ctk.set_default_color_theme('green')
ventana = ctk.CTk()
ventana.title('AvePedia')
ventana.geometry('1080x700')
ventana.minsize(850, 580)

menu = ctk.CTkFrame(ventana, width=190, corner_radius=0, fg_color=BOSQUE)
menu.pack(side='left', fill='y')
menu.pack_propagate(False)
ventana.configure(fg_color=PAPEL)
contenido = ctk.CTkFrame(ventana, fg_color='transparent')
contenido.pack(side='right', fill='both', expand=True, padx=15, pady=15)

botones_menu = {}
# Recuerda la búsqueda del catálogo para volver al mismo lugar desde una ficha
estado_catalogo = {'texto': '', 'habitat': TODOS_LOS_HABITATS, 'pagina': 0}


def limpiar(seccion):
    for nombre, boton_menu in botones_menu.items():
        boton_menu.configure(fg_color=VERDE if nombre == seccion else 'transparent')
    if AUDIO_DISPONIBLE:
        pygame.mixer.music.stop()
    for elemento in contenido.winfo_children():
        elemento.destroy()


def encabezado(texto):
    ctk.CTkLabel(contenido, text=texto, font=('Georgia', 32, 'bold'),
                 text_color=TINTA).pack(anchor='w', padx=12, pady=(10, 12))


def boton(padre, texto, accion, ancho=140):
    return ctk.CTkButton(padre, text=texto, command=accion, width=ancho, height=34,
                         fg_color=VERDE, hover_color=BOSQUE, text_color='white')


def guardar_avistamientos():
    avistamientos.to_csv(ARCHIVO_AVISTAMIENTOS, index=False, encoding='utf-8-sig')


def lista_habitats():
    habitats = sorted(h for h in aves['Hábitat'].unique() if h)
    return [TODOS_LOS_HABITATS] + habitats


def buscar_aves(texto, habitat):
    coincide = texto_busqueda.str.contains(sin_acentos(texto.strip()), regex=False)
    if habitat != TODOS_LOS_HABITATS:
        coincide = coincide & (aves['Hábitat'] == habitat)
    return aves[coincide]


def describir_endemismo(codigos):
    regiones = [REGIONES_ENDEMISMO[c.strip()] for c in codigos.split(',') if c.strip() in REGIONES_ENDEMISMO]
    if not regiones:
        return 'No es endémica'
    return 'Endémica regional de: ' + '; '.join(regiones)


def describir_amenaza(codigos):
    # Sin corchetes: estado en Panamá. Entre corchetes: estado mundial (UICN).
    partes = []
    for codigo in codigos.split(','):
        codigo = codigo.strip()
        mundial = codigo.startswith('[')
        nivel = NIVELES_AMENAZA.get(codigo.strip('[]'))
        if nivel:
            partes.append(f"{nivel} {'a nivel mundial' if mundial else 'en Panamá'}")
    if not partes:
        return 'Sin amenaza registrada'
    texto = '; '.join(partes)
    return texto[0].upper() + texto[1:]


def mostrar_credito(ave, tipo, padre):
    credito = creditos.get((ave['Nombre científico'], ave[tipo]))
    if credito:
        etiqueta = f"{tipo}: {credito['Autor']} · {credito['Licencia']} · {credito['Fuente']} ↗"
        enlace = ctk.CTkLabel(padre, text=etiqueta, font=('Arial', 12, 'underline'),
                              cursor='hand2', wraplength=540)
        enlace.pack(pady=(0, 5))
        enlace.bind('<Button-1>', lambda _: webbrowser.open(credito['Página de origen']))


def foto_ave(ave, ancho, alto):
    try:
        with Image.open(IMAGENES / ave['Imagen']) as original:
            foto = ImageOps.exif_transpose(original).convert('RGB')
        foto.thumbnail((ancho, alto))
        return ctk.CTkImage(light_image=foto, size=foto.size)
    except (OSError, ValueError):
        return None


def reproducir_audio(ave, mensaje):
    ruta = AUDIOS / str(ave['Audio'])
    if not ruta.is_file():
        mensaje.configure(text='No hay grabación disponible para esta especie.', text_color=ALERTA)
    elif not AUDIO_DISPONIBLE:
        mensaje.configure(text='No se pudo inicializar el dispositivo de audio.', text_color=ALERTA)
    else:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(ruta))
            pygame.mixer.music.play()
            mensaje.configure(text='')
        except Exception:
            mensaje.configure(text='No se pudo reproducir la grabación.', text_color=ALERTA)


def mostrar_grafica(identificador, padre):
    datos_ave = poblaciones[poblaciones['ID'].astype(str) == str(identificador)].sort_values('Década')
    if datos_ave.empty:
        ctk.CTkLabel(padre, text='Sin datos del Conteo Navideño para esta especie.').pack(pady=10)
        return
    etiquetas = [f'{int(d)}s' for d in datos_ave['Década']]
    figura = Figure(figsize=(5, 2.7), dpi=95, constrained_layout=True)
    eje = figura.add_subplot(111)
    eje.plot(etiquetas, datos_ave['Individuos por hora'], marker='o', color=VERDE)
    eje.set_title('Conteo Navideño de Aves en Panamá')
    eje.set_xlabel('Década')
    eje.set_ylabel('Individuos por hora')
    eje.set_ylim(bottom=0)
    eje.grid(alpha=0.25)
    canvas = FigureCanvasTkAgg(figura, master=padre)
    canvas.draw()
    canvas.get_tk_widget().pack(padx=10, pady=(10, 2), fill='x')
    ctk.CTkLabel(padre, text='Fuente: Audubon Christmas Bird Count (1973-2024). Índice de individuos '
                            'contados por hora de observación, no la población total.',
                 font=('Arial', 11), text_color=SECUNDARIO, wraplength=560).pack(pady=(0, 8))


def mostrar_ficha(codigo):
    seleccion = aves[aves['ID'] == codigo]
    if seleccion.empty:
        return
    ave = seleccion.iloc[0]
    limpiar('Catálogo de aves')
    encabezado(ave['Nombre'])
    zona = ctk.CTkScrollableFrame(contenido, fg_color='white')
    zona.pack(fill='both', expand=True, padx=15, pady=10)
    foto = foto_ave(ave, 420, 270)
    ctk.CTkLabel(zona, text='' if foto else 'Sin fotografía', image=foto).pack(pady=(14, 4))
    mostrar_credito(ave, 'Imagen', zona)
    for campo in ['Nombre científico', 'Hábitat', 'Alimentación', 'Descripción']:
        valor = ave[campo] or 'Pendiente'
        ctk.CTkLabel(zona, text=f'{campo}: {valor}', wraplength=580, justify='left').pack(pady=4)
    ctk.CTkLabel(zona, text=f"Endemismo: {describir_endemismo(ave['Endemismo'])}",
                 wraplength=580, justify='left').pack(pady=4)
    ctk.CTkLabel(zona, text=f"Estado de conservación: {describir_amenaza(ave['Amenaza'])}",
                 wraplength=580, justify='left').pack(pady=4)
    mensaje_audio = ctk.CTkLabel(zona, text='')
    boton(zona, 'Escuchar grabación', lambda: reproducir_audio(ave, mensaje_audio)).pack(pady=(8, 0))
    mostrar_credito(ave, 'Audio', zona)
    mensaje_audio.pack()
    mostrar_grafica(codigo, zona)
    boton(zona, 'Volver al catálogo', mostrar_catalogo).pack(pady=10)


def mostrar_catalogo():
    limpiar('Catálogo de aves')
    encabezado('Catálogo de aves')
    barra = ctk.CTkFrame(contenido, fg_color='transparent')
    barra.pack(fill='x', padx=12, pady=7)
    entrada = ctk.CTkEntry(barra, width=170, placeholder_text='Buscar por nombre común o científico')
    entrada.pack(side='left', fill='x', expand=True, padx=(0, 8))
    if estado_catalogo['texto']:
        entrada.insert(0, estado_catalogo['texto'])
    filtro = ctk.CTkComboBox(barra, values=lista_habitats(), width=200, state='readonly',
                             command=lambda _: buscar(nueva_busqueda=True))
    filtro.set(estado_catalogo['habitat'])
    filtro.pack(side='left', padx=5)
    boton(barra, 'Buscar', lambda: buscar(nueva_busqueda=True), ancho=85).pack(side='left', padx=5)

    resumen = ctk.CTkLabel(contenido, text='')
    resumen.configure(text_color=SECUNDARIO)
    resumen.pack(anchor='w', padx=12)
    lista = ctk.CTkScrollableFrame(contenido, fg_color='transparent')
    lista.pack(fill='both', expand=True, padx=5, pady=6)
    paginacion = ctk.CTkFrame(contenido, fg_color='transparent')
    paginacion.pack(pady=(0, 6))
    boton_anterior = boton(paginacion, '< Anterior', lambda: cambiar_pagina(-1), ancho=110)
    boton_anterior.pack(side='left', padx=8)
    boton_siguiente = boton(paginacion, 'Siguiente >', lambda: cambiar_pagina(1), ancho=110)
    boton_siguiente.pack(side='left', padx=8)

    def cambiar_pagina(paso):
        estado_catalogo['pagina'] += paso
        buscar()

    def buscar(*_, nueva_busqueda=False):
        estado_catalogo['texto'] = entrada.get().strip()
        estado_catalogo['habitat'] = filtro.get()
        if nueva_busqueda:
            estado_catalogo['pagina'] = 0
        for elemento in lista.winfo_children():
            elemento.destroy()

        resultado = buscar_aves(estado_catalogo['texto'], estado_catalogo['habitat'])
        total = len(resultado)
        paginas = max(1, -(-total // AVES_POR_PAGINA))
        estado_catalogo['pagina'] = min(max(estado_catalogo['pagina'], 0), paginas - 1)
        inicio = estado_catalogo['pagina'] * AVES_POR_PAGINA
        pagina = resultado.iloc[inicio:inicio + AVES_POR_PAGINA]

        if total == 0:
            resumen.configure(text='')
            ctk.CTkLabel(lista, text='No se encontraron aves.').pack(pady=15)
        else:
            resumen.configure(text=f'Mostrando {inicio + 1}-{inicio + len(pagina)} de {total} aves '
                                   f'(página {estado_catalogo["pagina"] + 1} de {paginas})')
        boton_anterior.configure(state='normal' if estado_catalogo['pagina'] > 0 else 'disabled')
        boton_siguiente.configure(state='normal' if estado_catalogo['pagina'] < paginas - 1 else 'disabled')

        for _, ave in pagina.iterrows():
            tarjeta = ctk.CTkFrame(lista, fg_color='white', corner_radius=12)
            tarjeta.pack(fill='x', padx=4, pady=4)
            foto = foto_ave(ave, 82, 70)
            ctk.CTkLabel(tarjeta, image=foto, text='', width=82).pack(side='left', padx=10)
            boton(tarjeta, 'Ver ficha', lambda codigo=ave['ID']: mostrar_ficha(codigo),
                  ancho=84).pack(side='right', padx=10)
            ctk.CTkLabel(tarjeta, text=ave['Nombre'], text_color=TINTA,
                         font=('Georgia', 17, 'bold')).pack(anchor='w', pady=(7, 0))
            ctk.CTkLabel(tarjeta, text=ave['Nombre científico'], font=('Arial', 13, 'italic'),
                         height=19, text_color=SECUNDARIO).pack(anchor='w')
            detalle = f"{ave['Hábitat'] or 'Pendiente'}  ·  {ave['Alimentación'] or 'Pendiente'}"
            ctk.CTkLabel(tarjeta, text=detalle, height=20, text_color=SECUNDARIO).pack(anchor='w', pady=(0, 7))
        try:
            lista._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    entrada.bind('<Return>', lambda _: buscar(nueva_busqueda=True))
    buscar()


def mostrar_avistamientos():
    limpiar('Mis avistamientos')
    encabezado('Mis avistamientos')
    zona = ctk.CTkScrollableFrame(contenido, fg_color='white')
    zona.pack(fill='both', expand=True, padx=15, pady=10)
    ctk.CTkLabel(zona, text='Ave:').pack(pady=(8, 0))
    # Con 500 especies, primero se escribe parte del nombre y la lista muestra solo las coincidencias
    busqueda = ctk.CTkEntry(zona, width=300, placeholder_text='Escribe para buscar el ave')
    busqueda.pack(pady=4)
    selector = ctk.CTkComboBox(zona, values=[], width=300, state='readonly')
    selector.pack(pady=4)
    pista = ctk.CTkLabel(zona, text='', text_color=ALERTA)
    pista.pack()

    def filtrar_selector(*_):
        coincidencias = buscar_aves(busqueda.get(), TODOS_LOS_HABITATS)['Nombre'].tolist()
        if not coincidencias:
            selector.configure(values=['Sin coincidencias'])
            selector.set('Sin coincidencias')
            pista.configure(text='Ninguna ave coincide con ese nombre. Prueba con otra palabra.')
            return
        selector.configure(values=coincidencias[:40])
        selector.set(coincidencias[0])
        if len(coincidencias) > 40 and busqueda.get().strip():
            pista.configure(text=f'{len(coincidencias)} coincidencias: escribe más para afinar la búsqueda.')
        else:
            pista.configure(text='')

    busqueda.bind('<KeyRelease>', filtrar_selector)
    filtrar_selector()
    fecha = ctk.CTkEntry(zona, width=300, placeholder_text='Fecha (DD/MM/AAAA)')
    fecha.pack(pady=6)
    ubicacion = ctk.CTkEntry(zona, width=300, placeholder_text='Ubicación')
    ubicacion.pack(pady=6)
    ctk.CTkLabel(zona, text='Comentario (opcional):').pack(pady=(6, 0))
    comentario = ctk.CTkTextbox(zona, width=330, height=65)
    comentario.pack(pady=6)
    mensaje = ctk.CTkLabel(zona, text='')
    mensaje.pack(pady=4)
    contenedor_registros = ctk.CTkFrame(zona)

    def refrescar():
        for elemento in contenedor_registros.winfo_children():
            elemento.destroy()
        if avistamientos.empty:
            ctk.CTkLabel(contenedor_registros, text='No tienes avistamientos todavía.').pack(pady=12)
            return
        for posicion, registro in avistamientos.reset_index(drop=True).iterrows():
            coincidencia = aves[aves['ID'] == registro['ID']]
            nombre = coincidencia.iloc[0]['Nombre'] if not coincidencia.empty else registro['ID']
            tarjeta = ctk.CTkFrame(contenedor_registros)
            tarjeta.pack(fill='x', padx=8, pady=5)
            ctk.CTkLabel(tarjeta, text=f"{nombre} | {registro['Fecha']} | {registro['Ubicación']}\n{registro['Comentario']}",
                         wraplength=460, justify='left').pack(pady=5)
            boton(tarjeta, 'Eliminar', lambda i=posicion: eliminar(i), ancho=90).pack(pady=4)

    def eliminar(posicion):
        global avistamientos
        avistamientos = avistamientos.drop(avistamientos.index[posicion]).reset_index(drop=True)
        guardar_avistamientos()
        refrescar()

    def registrar():
        global avistamientos
        nombre = selector.get()
        seleccion = aves[aves['Nombre'] == nombre]
        f = fecha.get().strip()
        lugar = ubicacion.get().strip()
        if seleccion.empty or not f or not lugar:
            mensaje.configure(text='Completa el ave, la fecha y la ubicación.', text_color=ALERTA)
            return
        try:
            dia = datetime.strptime(f, '%d/%m/%Y')
        except ValueError:
            mensaje.configure(text='La fecha debe ser válida y usar DD/MM/AAAA.', text_color=ALERTA)
            return
        if dia > datetime.now():
            mensaje.configure(text='La fecha no puede estar en el futuro.', text_color=ALERTA)
            return
        nuevo = pd.DataFrame([{
            'ID': seleccion.iloc[0]['ID'],
            'Fecha': f,
            'Ubicación': lugar,
            'Comentario': comentario.get('1.0', 'end').strip()
        }])
        avistamientos = pd.concat([avistamientos, nuevo], ignore_index=True)
        guardar_avistamientos()
        fecha.delete(0, 'end')
        ubicacion.delete(0, 'end')
        comentario.delete('1.0', 'end')
        mensaje.configure(text='¡Avistamiento guardado!', text_color=VERDE)
        refrescar()

    boton(zona, 'Registrar avistamiento', registrar).pack(pady=9)
    contenedor_registros.pack(fill='x', padx=8, pady=12)
    refrescar()


def mostrar_estadisticas():
    limpiar('Estadísticas')
    encabezado('Estadísticas')
    zona = ctk.CTkScrollableFrame(contenido, fg_color='white')
    zona.pack(fill='both', expand=True, padx=15, pady=10)
    total = len(aves)
    vistas = avistamientos['ID'].nunique() if not avistamientos.empty else 0
    porcentaje = (vistas / total * 100) if total else 0
    ctk.CTkLabel(zona, text=f'Especies observadas: {vistas} de {total} ({porcentaje:.1f}%)',
                 font=('Arial', 18, 'bold')).pack(pady=14)
    barra = ctk.CTkProgressBar(zona, width=420)
    barra.pack(pady=8)
    barra.set(porcentaje / 100)
    ctk.CTkLabel(zona, text=f'Total de avistamientos: {len(avistamientos)}').pack(pady=9)
    if avistamientos.empty:
        ctk.CTkLabel(zona, text='Registra un avistamiento para ver estadísticas por hábitat.').pack(pady=12)
        return
    observadas = aves[aves['ID'].isin(avistamientos['ID'])]['Nombre'].tolist()
    ctk.CTkLabel(zona, text='Tu colección: ' + ', '.join(observadas), wraplength=560, justify='left').pack(pady=6)
    relacionados = avistamientos.merge(aves[['ID', 'Hábitat']], on='ID', how='left')
    habitats = relacionados['Hábitat'].fillna('').replace('', 'Sin clasificar')
    conteos = habitats.value_counts()
    ctk.CTkLabel(zona, text=f'Hábitat más frecuente: {conteos.index[0]} ({conteos.iloc[0]} avistamientos)').pack(pady=12)
    figura = Figure(figsize=(6, 3), dpi=95, constrained_layout=True)
    eje = figura.add_subplot(111)
    eje.bar(conteos.index.tolist(), conteos.values, color=VERDE)
    eje.set_ylabel('Avistamientos')
    eje.set_title('Avistamientos por hábitat')
    eje.tick_params(axis='x', rotation=20)
    canvas = FigureCanvasTkAgg(figura, master=zona)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='x', padx=8, pady=12)


def tipo_licencia(texto):
    # 'CC BY-NC-SA 4.0', 'CC BY-NC-2.0-DE' -> 'CC BY-NC-SA', 'CC BY-NC': agrupa sin la versión
    texto = texto.strip().upper()
    if texto.startswith('CC0'):
        return 'CC0'
    return re.sub(r'[\s-]*\d.*$', '', texto) or 'Sin especificar'


def enlace(padre, texto, url):
    etiqueta = ctk.CTkLabel(padre, text=texto + ' ↗', font=('Arial', 13, 'underline'),
                            cursor='hand2', wraplength=600)
    etiqueta.pack(pady=(0, 4))
    etiqueta.bind('<Button-1>', lambda _: webbrowser.open(url))


def mostrar_acerca_de():
    limpiar('Acerca de')
    encabezado('Acerca de AvePedia')
    zona = ctk.CTkScrollableFrame(contenido, fg_color='white')
    zona.pack(fill='both', expand=True, padx=15, pady=10)

    def titulo(texto):
        ctk.CTkLabel(zona, text=texto, font=('Arial', 18, 'bold')).pack(pady=(16, 6))

    def parrafo(texto):
        ctk.CTkLabel(zona, text=texto, wraplength=600, justify='left').pack(pady=4)

    parrafo('AvePedia es una enciclopedia y diario de observación de las aves de Panamá. '
            f'Su catálogo reúne {len(aves)} especies: las más registradas en los Conteos Navideños '
            'de Aves de Panamá, más el Águila Harpía por ser el ave nacional.')

    titulo('Datos de las especies')
    parrafo('Lista de especies y gráficas por década: Conteo Navideño de Aves (Christmas Bird Count), '
            'National Audubon Society, círculos de Panamá, 1973-2024. Organizado en Panamá por la '
            'Sociedad Audubon de Panamá.')
    enlace(zona, 'Conteo Navideño de Aves (Audubon)', 'https://www.audubon.org/community-science/christmas-bird-count/access-christmas-bird-count-results')
    parrafo('Nombres en español, endemismo y estado de conservación: Lista de las aves de la República '
            'de Panamá 2026, Sociedad Audubon de Panamá.')
    enlace(zona, 'Publicaciones de la Sociedad Audubon de Panamá', 'https://audubonpanama.org/publicaciones.html')
    parrafo('Las gráficas muestran individuos contados por hora de observación: un índice relativo de '
            'abundancia, no la población total de cada especie.')

    titulo('Fotografías y grabaciones')
    if creditos:
        archivos = list(creditos.values())
        fuentes = Counter(fila['Fuente'] for fila in archivos)
        licencias = Counter(tipo_licencia(fila['Licencia']) for fila in archivos)
        parrafo(f'{len(archivos)} archivos de: ' + ', '.join(f'{f} ({n})' for f, n in fuentes.most_common()) + '.')
        parrafo('Licencias: ' + ', '.join(f'{l} ({n})' for l, n in licencias.most_common()) + '.')
    parrafo('El autor, la licencia y el enlace al original de cada fotografía y grabación aparecen '
            'en la ficha de cada ave. Se usan con fines educativos, sin fines comerciales.')

    titulo('Tecnología')
    parrafo('Python 3.9.5, CustomTkinter, Pandas, Matplotlib, Pillow y Pygame. '
            'Los avistamientos se guardan en el archivo datos/avistamientos.csv de cada computadora.')


def mostrar_inicio():
    limpiar('Inicio')
    encabezado('Aves de Panamá')
    ctk.CTkLabel(contenido, text=f'{len(aves)} especies en el catálogo', text_color=SECUNDARIO,
                 font=('Arial', 16)).pack(anchor='w', padx=14)
    acciones = ctk.CTkFrame(contenido, fg_color='transparent')
    acciones.pack(anchor='w', padx=12, pady=(12, 22))
    boton(acciones, 'Explorar catálogo', mostrar_catalogo).pack(side='left', padx=(0, 8))
    boton(acciones, 'Registrar avistamiento', mostrar_avistamientos).pack(side='left')

    if aves.empty:
        ctk.CTkLabel(contenido, text='Catálogo vacío. Revisa datos/datos_modificados/aves.csv.', text_color=ALERTA).pack()
        return
    tucan = aves[aves['Nombre científico'] == 'Ramphastos sulfuratus']
    ave = tucan.iloc[0] if not tucan.empty else aves.iloc[0]
    portada = ctk.CTkFrame(contenido, fg_color='white', corner_radius=14)
    portada.pack(fill='x', padx=12)
    foto = foto_ave(ave, 360, 210)
    ctk.CTkLabel(portada, image=foto, text='' if foto else 'Sin fotografía').pack(pady=(16, 4))
    mostrar_credito(ave, 'Imagen', portada)
    ctk.CTkLabel(portada, text=ave['Nombre'], font=('Georgia', 24, 'bold'), text_color=TINTA).pack()
    ctk.CTkLabel(portada, text=ave['Nombre científico'], font=('Arial', 14, 'italic'),
                 text_color=SECUNDARIO).pack()
    boton(portada, 'Ver ficha', lambda: mostrar_ficha(ave['ID'])).pack(pady=(6, 14))


ctk.CTkLabel(menu, text='AvePedia', font=('Georgia', 29, 'bold'), text_color=PAPEL).pack(
    anchor='w', padx=17, pady=(30, 24))
for texto, funcion in [
    ('Inicio', mostrar_inicio),
    ('Catálogo de aves', mostrar_catalogo),
    ('Mis avistamientos', mostrar_avistamientos),
    ('Estadísticas', mostrar_estadisticas),
    ('Acerca de', mostrar_acerca_de),
]:
    opcion = ctk.CTkButton(menu, text=texto, command=funcion, anchor='w', height=40,
                           fg_color='transparent', hover_color=VERDE, text_color=PAPEL)
    opcion.pack(fill='x', padx=12, pady=3)
    botones_menu[texto] = opcion

mostrar_inicio()
ventana.mainloop()
