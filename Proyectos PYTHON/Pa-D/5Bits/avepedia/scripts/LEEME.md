# Scripts de datos de AvePedia

Estos scripts generan los archivos `datos/datos_modificados/aves.csv` y `datos/datos_modificados/poblaciones.csv` a partir de fuentes públicas.
La aplicación **no los necesita para funcionar**: solo sirven para reconstruir o actualizar los datos.

Los [datos originales](../datos/datos_originales/) se obtienen de las fuentes indicadas. Los [datos modificados](../datos/datos_modificados/) son los CSV que lee Avepedia.

## Fuentes

### Fotografías y grabaciones

Cada ficha usa un JPEG de `imagenes/` y un MP3 de `audios/`. El archivo
[`datos/datos_modificados/multimedia.csv`](../datos/datos_modificados/multimedia.csv) identifica el autor, la licencia,
la página de origen y el archivo fuente de cada recurso. Conserva el nombre
científico del catálogo y la identificación de la fuente, incluida la subespecie
cuando consta en la grabación.

Las fotografías proceden de [AviCommons](https://avicommons.org/) e
[iNaturalist](https://www.inaturalist.org/). Para localizar las fotos de AviCommons
se usó [BirdNET+ Taxonomy v0.5-Nov2026](https://birdnet.cornell.edu/taxonomy)
(CC BY-SA 4.0). Las grabaciones proceden de [Xeno-canto](https://xeno-canto.org/)
e iNaturalist. Se consultaron también los registros publicados en [GBIF](https://www.gbif.org/).
Se conservaron las grabaciones completas y se convirtieron a MP3 los archivos que
lo requerían. La foto y la grabación se pueden consultar sin conexión. Los créditos
en cada ficha abren la página de origen.

### Conteos y lista de especies

1. **Audubon Christmas Bird Count (CBC)**, National Audubon Society: dataset completo
   `20250205_FullSet_AllCountries_AllYears_CBC_Data_Request.zip` (114 MB, no se sube al repositorio).
2. **Lista de las aves de la República de Panamá 2026**, Sociedad Audubon de Panamá
   (audubonpanama.org → Publicaciones). Aporta los nombres oficiales en español, el endemismo y la amenaza.

## Orden de uso

Desde la carpeta `avepedia/scripts/`, ejecuta cada script con Python. Crea primero las carpetas de salida de los pasos 1 y 3.

| Paso | Script | Qué hace |
|---|---|---|
| 1 | `extraer_panama.py <archivo.zip> <carpeta>` | Del dataset mundial del CBC, guarda solo los registros de Panamá. |
| 2 | `leer_lista_audubon.py <lista.txt> <lista.csv>` | Convierte la lista oficial (PDF pasado a texto con `pdftotext -layout`) en CSV. |
| 3 | `preparar_conteos.py <carpeta_paso1> <salida> <lista.csv>` | Limpia nombres, corrige cambios de taxonomía, calcula horas de observación, selecciona 500 especies (entre ellas el águila harpía) y calcula el índice por década cuando hay registros. |
| 4 | `actualizar_catalogo.py <salida_paso3> ../datos/datos_modificados` | Actualiza `aves.csv` y `poblaciones.csv` **conservando los ID y las fichas** ya escritas. |

## Cómo se calcula la gráfica de cada ave

- Se usan los círculos de conteo de Panamá con conteos regulares (Atlántico, Pacífico y Central del Canal desde 1973;
  Volcán desde 1996; Puerto Lara, Guna Yala y Cana en años recientes).
- Para cada especie solo se cuentan los círculos donde alguna vez fue registrada. Un conteo de esos círculos
  en el que no apareció cuenta como 0.
- Índice = individuos contados ÷ horas de observación de los grupos, sumando todos los conteos de cada década.
- Es un **índice relativo**, no la población total de la especie.

## Correcciones de taxonomía

El CBC usa algunos nombres antiguos. `preparar_conteos.py` los convierte a la lista oficial 2026
(diccionarios `EQUIVALENCIAS` y `NOMBRE_COMPLETO`). Por ejemplo, el CBC registró el Gavilán Barrigrís
como *Buteo plagiatus* hasta 2016 y como *Buteo nitidus* desde 2017; ambos se unen en una sola especie.
