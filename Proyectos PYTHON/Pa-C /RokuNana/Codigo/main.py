from pathlib import Path
import argparse
import webbrowser
from analisis import ejecutar

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='AquaLytics: limpiar datos y abrir el panel de calidad del agua.')
    parser.add_argument('--sin-abrir',action='store_true',help='Generar resultados sin abrir el navegador')
    args=parser.parse_args()
    tabla,_,_,indicadores=ejecutar()
    print(f"Proceso terminado: {len(tabla)} actividades; {indicadores['sitios']} estaciones.")
    print('Potabilidad no determinada. Consulta las excedencias y la cobertura en el panel.')
    ruta=Path(__file__).resolve().parent/'resultados/Panel_AquaLytics.html'
    print(ruta)
    if not args.sin_abrir:webbrowser.open(ruta.as_uri())
