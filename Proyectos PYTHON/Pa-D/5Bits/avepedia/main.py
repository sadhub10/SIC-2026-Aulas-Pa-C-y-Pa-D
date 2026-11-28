import os
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
IMAGENES = BASE / 'imagenes'
AUDIOS = BASE / 'audios'
for carpeta in (DATOS, IMAGENES, AUDIOS):
    carpeta.mkdir(exist_ok=True)

ARCHIVO_AVES = DATOS / 'aves.csv'
ARCHIVO_AVISTAMIENTOS = DATOS / 'avistamientos.csv'
ARCHIVO_POBLACIONES = DATOS / 'poblaciones.csv'

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
archivo_creditos = DATOS / 'multimedia.csv'
if archivo_creditos.is_file():
    with archivo_creditos.open(encoding='utf-8-sig', newline='') as archivo:
        creditos = {(fila['Especie del catálogo'], fila['Archivo']): fila for fila in DictReader(archivo)}

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('green')
ventana = ctk.CTk()
ventana.title('AvePedia')
ventana.geometry('1080x700')
ventana.minsize(850, 580)

menu = ctk.CTkFrame(ventana, width=220, corner_radius=0)
menu.pack(side='left', fill='y')
menu.pack_propagate(False)
contenido = ctk.CTkFrame(ventana)
contenido.pack(side='right', fill='both', expand=True, padx=15, pady=15)

imagenes_cargadas = []
# Recuerda la búsqueda del catálogo para volver al mismo lugar desde una ficha
estado_catalogo = {'texto': '', 'habitat': TODOS_LOS_HABITATS, 'pagina': 0}


def limpiar():
    if AUDIO_DISPONIBLE:
        pygame.mixer.music.stop()
    imagenes_cargadas.clear()
    for elemento in contenido.winfo_children():
        elemento.destroy()


def encabezado(texto):
    ctk.CTkLabel(contenido, text=texto, font=('Arial', 27, 'bold')).pack(pady=(18, 12))


def aviso(texto, color='white'):
    ctk.CTkLabel(contenido, text=texto, text_color=color, wraplength=500).pack(pady=8)


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


def imagen_ave(ave, padre):
    ruta = IMAGENES / str(ave['Imagen'])
    if not ruta.is_file():
        ctk.CTkLabel(padre, text='Sin fotografía', width=150, height=120).pack(padx=10, pady=8)
        return
    try:
        with Image.open(ruta) as original:
            foto = ImageOps.exif_transpose(original).convert('RGB')
        escala = min(320 / foto.width, 220 / foto.height, 1)
        tamano = (max(1, round(foto.width * escala)), max(1, round(foto.height * escala)))
        imagen = ctk.CTkImage(light_image=foto, dark_image=foto, size=tamano)
        imagenes_cargadas.append(imagen)
        ctk.CTkLabel(padre, image=imagen, text='').pack(padx=10, pady=8)
        mostrar_credito(ave, 'Imagen', padre)
    except Exception:
        ctk.CTkLabel(padre, text='No se pudo abrir la imagen').pack(padx=10, pady=8)


def reproducir_audio(ave, mensaje):
    ruta = AUDIOS / str(ave['Audio'])
    if not ruta.is_file():
        mensaje.configure(text='No hay grabación disponible para esta especie.', text_color='orange')
    elif not AUDIO_DISPONIBLE:
        mensaje.configure(text='No se pudo inicializar el dispositivo de audio.', text_color='orange')
    else:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(str(ruta))
            pygame.mixer.music.play()
            mensaje.configure(text='')
        except Exception:
            mensaje.configure(text='No se pudo reproducir la grabación.', text_color='orange')


def mostrar_grafica(identificador, padre):
    datos_ave = poblaciones[poblaciones['ID'].astype(str) == str(identificador)].sort_values('Década')
    if datos_ave.empty:
        ctk.CTkLabel(padre, text='Sin datos del Conteo Navideño para esta especie.').pack(pady=10)
        return
    etiquetas = [f'{int(d)}s' for d in datos_ave['Década']]
    figura = Figure(figsize=(5, 2.7), dpi=95, constrained_layout=True)
    eje = figura.add_subplot(111)
    eje.plot(etiquetas, datos_ave['Individuos por hora'], marker='o')
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
                 font=('Arial', 11), text_color='gray', wraplength=560).pack(pady=(0, 8))


def mostrar_ficha(codigo):
    seleccion = aves[aves['ID'] == codigo]
    if seleccion.empty:
        return
    ave = seleccion.iloc[0]
    limpiar()
    encabezado(ave['Nombre'])
    zona = ctk.CTkScrollableFrame(contenido)
    zona.pack(fill='both', expand=True, padx=15, pady=10)
    imagen_ave(ave, zona)
    for campo in ['Nombre científico', 'Hábitat', 'Alimentación', 'Descripción']:
        valor = ave[campo] or 'Pendiente'
        ctk.CTkLabel(zona, text=f'{campo}: {valor}', wraplength=580, justify='left').pack(pady=4)
    ctk.CTkLabel(zona, text=f"Endemismo: {describir_endemismo(ave['Endemismo'])}",
                 wraplength=580, justify='left').pack(pady=4)
    ctk.CTkLabel(zona, text=f"Estado de conservación: {describir_amenaza(ave['Amenaza'])}",
                 wraplength=580, justify='left').pack(pady=4)
    mensaje_audio = ctk.CTkLabel(zona, text='')
    ctk.CTkButton(zona, text='Escuchar grabación', command=lambda: reproducir_audio(ave, mensaje_audio)).pack(pady=(8, 0))
    mostrar_credito(ave, 'Audio', zona)
    mensaje_audio.pack()
    mostrar_grafica(codigo, zona)
    ctk.CTkButton(zona, text='Volver al catálogo', command=mostrar_catalogo).pack(pady=10)


def mostrar_catalogo():
    limpiar()
    encabezado('Catálogo de aves')
    barra = ctk.CTkFrame(contenido, fg_color='transparent')
    barra.pack(pady=7)
    entrada = ctk.CTkEntry(barra, width=300, placeholder_text='Buscar por nombre común o científico')
    entrada.pack(side='left', padx=5)
    if estado_catalogo['texto']:
        entrada.insert(0, estado_catalogo['texto'])
    filtro = ctk.CTkComboBox(barra, values=lista_habitats(), width=200, state='readonly',
                             command=lambda _: buscar(nueva_busqueda=True))
    filtro.set(estado_catalogo['habitat'])
    filtro.pack(side='left', padx=5)
    ctk.CTkButton(barra, text='Buscar', width=90,
                  command=lambda: buscar(nueva_busqueda=True)).pack(side='left', padx=5)

    resumen = ctk.CTkLabel(contenido, text='')
    resumen.pack()
    lista = ctk.CTkScrollableFrame(contenido)
    lista.pack(fill='both', expand=True, padx=15, pady=8)
    paginacion = ctk.CTkFrame(contenido, fg_color='transparent')
    paginacion.pack(pady=(0, 6))
    boton_anterior = ctk.CTkButton(paginacion, text='< Anterior', width=110, command=lambda: cambiar_pagina(-1))
    boton_anterior.pack(side='left', padx=8)
    boton_siguiente = ctk.CTkButton(paginacion, text='Siguiente >', width=110, command=lambda: cambiar_pagina(1))
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
            tarjeta = ctk.CTkFrame(lista)
            tarjeta.pack(fill='x', padx=8, pady=6)
            ctk.CTkLabel(tarjeta, text=f"{ave['Nombre']} — {ave['Nombre científico']}",
                         font=('Arial', 16, 'bold')).pack(pady=(8, 3))
            ctk.CTkLabel(tarjeta, text=f"Hábitat: {ave['Hábitat'] or 'Pendiente'} | "
                                       f"Alimentación: {ave['Alimentación'] or 'Pendiente'}",
                         wraplength=500).pack(pady=3)
            ctk.CTkButton(tarjeta, text='Ver ficha',
                          command=lambda codigo=ave['ID']: mostrar_ficha(codigo)).pack(pady=8)
        try:
            lista._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    entrada.bind('<Return>', lambda _: buscar(nueva_busqueda=True))
    buscar()


def mostrar_avistamientos():
    limpiar()
    encabezado('Mis avistamientos')
    zona = ctk.CTkScrollableFrame(contenido)
    zona.pack(fill='both', expand=True, padx=15, pady=10)
    ctk.CTkLabel(zona, text='Ave:').pack(pady=(8, 0))
    # Con 500 especies, primero se escribe parte del nombre y la lista muestra solo las coincidencias
    busqueda = ctk.CTkEntry(zona, width=300, placeholder_text='Escribe para buscar el ave')
    busqueda.pack(pady=4)
    selector = ctk.CTkComboBox(zona, values=[], width=300, state='readonly')
    selector.pack(pady=4)
    pista = ctk.CTkLabel(zona, text='', text_color='orange')
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
            ctk.CTkButton(tarjeta, text='Eliminar', width=90,
                          command=lambda i=posicion: eliminar(i)).pack(pady=4)

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
            mensaje.configure(text='Completa el ave, la fecha y la ubicación.', text_color='orange')
            return
        try:
            dia = datetime.strptime(f, '%d/%m/%Y')
        except ValueError:
            mensaje.configure(text='La fecha debe ser válida y usar DD/MM/AAAA.', text_color='orange')
            return
        if dia > datetime.now():
            mensaje.configure(text='La fecha no puede estar en el futuro.', text_color='orange')
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
        mensaje.configure(text='¡Avistamiento guardado!', text_color='lightgreen')
        refrescar()

    ctk.CTkButton(zona, text='Registrar avistamiento', command=registrar).pack(pady=9)
    contenedor_registros.pack(fill='x', padx=8, pady=12)
    refrescar()


def mostrar_estadisticas():
    limpiar()
    encabezado('Estadísticas')
    zona = ctk.CTkScrollableFrame(contenido)
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
    eje.bar(conteos.index.tolist(), conteos.values)
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
    limpiar()
    encabezado('Acerca de AvePedia')
    zona = ctk.CTkScrollableFrame(contenido)
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
    limpiar()
    encabezado('Bienvenido a AvePedia')
    aviso('Tu enciclopedia y diario de observación de aves de Panamá.')
    if aves.empty:
        aviso(f'No se encontró el catálogo de aves. Revisa el archivo {ARCHIVO_AVES.name} '
              'en la carpeta datos.', 'orange')
    ctk.CTkLabel(contenido, text=f'{len(aves)} especies en el catálogo',
                 font=('Arial', 19)).pack(pady=12)
    ctk.CTkButton(contenido, text='Explorar catálogo', command=mostrar_catalogo).pack(pady=10)
    ctk.CTkButton(contenido, text='Registrar avistamiento', command=mostrar_avistamientos).pack(pady=10)


ctk.CTkLabel(menu, text='AvePedia', font=('Arial', 27, 'bold')).pack(pady=36)
for texto, funcion in [
    ('Inicio', mostrar_inicio),
    ('Catálogo de aves', mostrar_catalogo),
    ('Mis avistamientos', mostrar_avistamientos),
    ('Estadísticas', mostrar_estadisticas),
    ('Acerca de', mostrar_acerca_de),
]:
    ctk.CTkButton(menu, text=texto, width=185, command=funcion).pack(pady=10)

mostrar_inicio()
ventana.mainloop()
