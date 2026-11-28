# Avepedia — Guía de aves de Panamá para el turismo de observación

**Equipo 5Bits · Aula Pa-D · Módulo de Python · Samsung Innovation Campus**
# Integrantes 

**Isaac Salinas (lider)<br>
  Antonio Gonzales<br>
  Aramys Cedeño<br>
  Iker Martinez<br>
  Cristian Muir<br>**

## Planteamiento del problema

La Lista de las Aves de la República de Panamá de 2025 registra 1,030 especies en el país. Para quien prepara su primera salida, saber qué aves hay es solo el comienzo. El nombre de una especie puede aparecer en un conteo, su fotografía en otro portal y su canto en un tercero. Reunir esas pistas exige tiempo y conocimientos que un visitante quizá todavía no tenga. [Lista nacional de 2025, Comité de Registros de la Sociedad Audubon de Panamá](https://doi.org/10.13140/RG.2.2.36838.28486)

## Objetivos

Facilitar que turistas y residentes exploren y conozcan las aves de Panamá con una guía que reúne en un solo lugar la información que necesitan para observarlas.

- Depurar los datos y vincular los nombres, las características y los recursos de cada especie en una misma ficha.
- Ayudar a reconocer un ave por lo que se ve y se oye, mediante fotografías y grabaciones.
- Incentivar nuevas salidas con un diario en el que cada persona pueda registrar sus avistamientos y ver cómo crece su colección de especies.

## Relación con la UNESCO

La solidaridad se ve en el trabajo de los voluntarios del Conteo Navideño de Aves, que comparten lo que observan en sus recorridos. 5Bits aprovecha ese esfuerzo para que estudiantes, guías y visitantes puedan aprender a reconocer las aves de Panamá.

## Resultado del proyecto

Avepedia es una aplicación de escritorio con **500 especies**. La cifra corresponde a los nombres científicos únicos de `aves.csv`. La selección se basa en la frecuencia de registro en los conteos de Panamá e incluye al águila harpía, el ave nacional.

Antes de una salida, una turista pulsa **Explorar catálogo** en **Inicio**. En **Catálogo de aves** puede buscar por nombre común o científico y filtrar por hábitat. Si escribe "tucan pico iris", pulsa **Buscar** y abre el resultado con **Ver ficha**, encuentra al Tucán Pico Iris (*Ramphastos sulfuratus*). La foto y la descripción le permiten fijarse en los tonos verde, naranja y rojo del pico. Con **Escuchar grabación** puede oír el sonido de la especie si su equipo tiene salida de audio. La misma ficha muestra su alimentación, su hábitat y una gráfica por década.

Después de observar el tucán, abre **Mis avistamientos**, selecciona el ave, escribe la fecha y el lugar, y pulsa **Registrar avistamiento**. También puede anotar un comentario. El diario empieza vacío y se guarda en su computadora. En **Estadísticas** puede consultar tanto el total de encuentros como las especies distintas que ha visto. Si vuelve a registrar el mismo tucán, suma una observación y la colección conserva una sola especie.

## Herramientas y archivos

| Archivo o carpeta | Función |
|---|---|
| [avepedia/main.py](avepedia/main.py) | Aplicación de escritorio. CustomTkinter construye la interfaz, pandas lee y relaciona los CSV, Pillow muestra las fotos, Pygame reproduce las grabaciones y Matplotlib dibuja las gráficas. |
| [Datos originales](avepedia/datos/datos_originales/) | La [guía de fuentes](avepedia/datos/datos_originales/README.md) identifica el ZIP mundial de conteos y la lista nacional en PDF, y explica cómo obtenerlos. |
| [Datos modificados](avepedia/datos/datos_modificados/) | [aves.csv](avepedia/datos/datos_modificados/aves.csv) contiene las fichas, [poblaciones.csv](avepedia/datos/datos_modificados/poblaciones.csv) los índices por especie y década, y [multimedia.csv](avepedia/datos/datos_modificados/multimedia.csv) los créditos de cada foto y grabación. |
| [Diario local](avepedia/datos/avistamientos.csv) | Conserva entre sesiones el identificador del ave, la fecha, la ubicación y el comentario de cada avistamiento. |
| [avepedia/imagenes/](avepedia/imagenes/) y [avepedia/audios/](avepedia/audios/) | 500 fotografías JPEG y 500 grabaciones MP3 incluidas para consultar las fichas sin conexión. |
| [avepedia/scripts/](avepedia/scripts/) | Herramientas para extraer los conteos de Panamá, leer la lista nacional, conciliar nombres científicos, calcular los índices y actualizar el catálogo. Incluye un verificador multimedia. [Guía de preparación de datos](avepedia/scripts/LEEME.md) |
| [avepedia/consola.py](avepedia/consola.py) | Prototipo de consola con cinco ejemplos y cifras de población ficticias. |

## Fuentes de datos y multimedia

- **Conteo Navideño de Aves.** Del dataset mundial Christmas Bird Count de la National Audubon Society, el equipo extrajo los registros de Panamá (1973–2024). Cuando hay datos para la especie, la gráfica muestra cuántos individuos se contaron por cada hora que los grupos dedicaron a observar aves en esa década. Esta medida permite comparar conteos con distinto esfuerzo de observación. [Consulta de resultados](https://audubon.org/community-science/christmas-bird-count/access-christmas-bird-count-results) · [Formulario de solicitud del dataset](https://survey123.arcgis.com/share/7dc33b4fff77468a8bba855291f86527?portalUrl=https://audubon.maps.arcgis.com)
- **Nombres y conservación.** Para las fichas se usó la edición **2026** de la lista de la Sociedad Audubon de Panamá, que aporta los nombres en español, el endemismo y las categorías de amenaza. [Publicaciones de Audubon Panamá](https://audubonpanama.org/publicaciones.html)
- **Fotografías.** 494 proceden de AviCommons y 6 de iNaturalist, dos de ellas referenciadas mediante GBIF. Para localizar las fotografías de AviCommons se utilizó BirdNET+ Taxonomy v0.5-Nov2026 (CC BY-SA 4.0). [AviCommons](https://avicommons.org/) · [iNaturalist](https://www.inaturalist.org/) · [BirdNET+ Taxonomy](https://birdnet.cornell.edu/taxonomy)
- **Grabaciones.** Los créditos identifican 498 audios de xeno-canto referenciados mediante GBIF y 2 de iNaturalist. El equipo conservó las grabaciones completas y convirtió a MP3 las que lo requerían. [xeno-canto](https://xeno-canto.org/) · [GBIF](https://www.gbif.org/)
- Cada ficha muestra el autor y la licencia de su foto y grabación, con un enlace al original. El inventario conserva también la identificación de la fuente, la URL del archivo y, cuando figura en la fuente, el enlace a la licencia. [Créditos de los 1,000 archivos](avepedia/datos/datos_modificados/multimedia.csv)

## Cómo ejecutar Avepedia

Se necesita Python 3.11 con Tk y un entorno de escritorio. En Windows, abre PowerShell en la carpeta `Proyectos PYTHON/Pa-D/5Bits` y ejecuta estos comandos. El primero entra en la carpeta que contiene `main.py`.

```powershell
cd avepedia
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Los datos y los archivos multimedia ya están preparados. La instalación de dependencias y los enlaces externos requieren internet. Para conservar el diario entre sesiones, la aplicación necesita poder escribir en `avepedia/datos/avistamientos.csv`.
