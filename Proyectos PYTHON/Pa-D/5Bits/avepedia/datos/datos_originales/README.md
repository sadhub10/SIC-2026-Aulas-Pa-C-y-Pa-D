# Datos originales

Los dos archivos de entrada se obtienen externamente.

| Fuente | Archivo de entrada y uso en Avepedia |
|---|---|
| National Audubon Society | `20250205_FullSet_AllCountries_AllYears_CBC_Data_Request.zip` contiene los datos mundiales del Christmas Bird Count. El equipo extrajo los registros de Panamá para relacionar cada conteo con las horas de observación. [Consulta de resultados](https://audubon.org/community-science/christmas-bird-count/access-christmas-bird-count-results) · [Formulario de solicitud del dataset](https://survey123.arcgis.com/share/7dc33b4fff77468a8bba855291f86527?portalUrl=https://audubon.maps.arcgis.com) |
| Sociedad Audubon de Panamá | La *Lista de las aves de la República de Panamá 2026* aporta nombres en español, endemismo y categorías de amenaza. [Descargar la lista de 2026 en PDF](https://audubonpanama.org/files/11/Publicaciones/598/Lista-de-aves-de-Panama-2026-rev1) · [Publicaciones de la Sociedad Audubon de Panamá](https://www.audubonpanama.org/publicaciones.html) |

Para reproducir la preparación, solicita el ZIP con el formulario de Audubon, descarga la lista en PDF y guarda ambos archivos en esta carpeta. La aplicación utiliza directamente los [CSV preparados por 5Bits](../datos_modificados/). Los pasos de extracción y transformación están en la [guía de preparación](../../scripts/LEEME.md).
