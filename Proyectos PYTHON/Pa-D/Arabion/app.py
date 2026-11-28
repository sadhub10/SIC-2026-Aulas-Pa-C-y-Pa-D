"""EcoTrace - Interfaz con Streamlit.

Ejecutar:  python -m streamlit run app.py
"""
from datetime import datetime

import pandas as pd
import streamlit as st

import calculos
import datos
import reportes
from modelos import Vehiculo

st.set_page_config(page_title="EcoTrace", page_icon="🚗", layout="wide")

NOMBRE_COMBUSTIBLE = {"gasolina_91": "Gasolina 91", "gasolina_95": "Gasolina 95", "diesel": "Diésel"}

# Nombres de cada modelo en años anteriores (tabla de la página Dataset del Notion)
NOMBRES_HISTORICOS = {
    "Toyota Corolla": ("Toyota", ["Corolla", "Corolla (1-mode)"]),
    "Hyundai Elantra": ("Hyundai", ["Elantra"]),
    "Nissan Sentra": ("Nissan", ["Sentra", "Sentra S"]),
    "Toyota Corolla Cross": ("Toyota", ["Corolla Cross"]),
    "Nissan Kicks": ("Nissan", ["Kicks"]),
    "Hyundai Venue": ("Hyundai", ["Venue"]),
    "Hyundai Kona": ("Hyundai", ["Kona"]),
    "Kia Seltos": ("Kia", ["Seltos"]),
    "Honda CR-V": ("Honda", ["CR-V"]),
    "Kia Sportage": ("Kia", ["Sportage"]),
    "Honda HR-V": ("Honda", ["HR-V"]),
    "Hyundai Tucson AWD": ("Hyundai", ["Tucson AWD"]),
}


# ---------------------------------------------------------------------------
# Carga de datos (se hace una sola vez, no en cada clic)
# ---------------------------------------------------------------------------
@st.cache_data
def cargar_tablas():
    df_limpio = datos.limpiar(datos.cargar_dataset())
    df_historico = datos.cargar_historico()
    precios_historicos = datos.leer_precios_historicos()
    return df_limpio, df_historico, precios_historicos


@st.cache_resource
def cargar_catalogo(_df_limpio):
    return datos.crear_catalogo(_df_limpio)


df_limpio, df_historico, precios_historicos = cargar_tablas()
catalogo = cargar_catalogo(df_limpio)
precios, vigencia = datos.leer_precios()
factores = datos.leer_factores()

por_nombre = {v.nombre(): v for v in catalogo}
nombres_catalogo = list(por_nombre)

if "historial" not in st.session_state:
    st.session_state.historial = datos.cargar_historial()


def registrar(pestana, modelo, km_mes, res):
    """Agrega una consulta al historial (se guarda en JSON con el botón de la barra lateral)."""
    st.session_state.historial.append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "pestana": pestana,
        "modelo": modelo,
        "km_mes": round(km_mes, 2),
        "costo_mes": round(res["costo_mes"], 2),
        "co2_mes": round(res["co2_mes"], 2),
    })


def mostrar_resumen(res):
    """Tarjetas con el resultado de calculos.resumen()."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Litros al mes", f"{res['litros_mes']:.2f} L")
    c2.metric("Costo estimado al mes", f"B/. {res['costo_mes']:.2f}")
    c3.metric("CO₂ estimado al mes", f"{res['co2_mes']:.2f} kg")
    c4, c5, _ = st.columns(3)
    c4.metric("Costo estimado al año", f"B/. {res['costo_anio']:.2f}")
    c5.metric("CO₂ estimado al año", f"{res['co2_anio']:.2f} kg")


# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------
fecha_vigencia = pd.to_datetime(vigencia).strftime("%d/%m/%Y")
st.sidebar.title("EcoTrace")
st.sidebar.metric("Gasolina 91 (Panamá y Colón)", f"B/. {precios['gasolina_91']:.3f} por litro")
st.sidebar.caption(
    f"Gasolina 95: B/. {precios['gasolina_95']:.3f} · Diésel: B/. {precios['diesel']:.3f}\n\n"
    f"Vigente desde el {fecha_vigencia} · Secretaría Nacional de Energía"
)
st.sidebar.divider()
st.sidebar.write(f"Consultas en el historial: **{len(st.session_state.historial)}**")
if st.sidebar.button("Guardar historial"):
    datos.guardar_historial(st.session_state.historial)
    st.sidebar.success("Historial guardado en data/historial.json")

# ---------------------------------------------------------------------------
# Encabezado y pestañas
# ---------------------------------------------------------------------------
st.title("¿Cuánto te cuesta tu carro al mes?")
st.write("Calcula el costo en combustible y el CO₂ de tu carro para ir al trabajo, con datos oficiales.")

(tab_catalogo, tab_gasto, tab_comparar, tab_otro,
 tab_ranking, tab_estadisticas, tab_historia) = st.tabs(
    ["Catálogo", "Mi gasto", "Comparar", "Otro modelo", "Ranking", "Estadísticas", "Historia 2021–2026"]
)

# ---------- 1. Catálogo ----------
with tab_catalogo:
    st.subheader("Modelos que se venden en Panamá")
    tabla = pd.DataFrame([{
        "Modelo": v.nombre(),
        "Tipo": v.tipo,
        "Motor (L)": v.motor,
        "Combustible": NOMBRE_COMBUSTIBLE[v.combustible],
        "Consumo (L/100 km)": v.consumo,
    } for v in catalogo])
    st.dataframe(tabla, hide_index=True)
    st.caption("Consumo combinado (ciudad y carretera) de Natural Resources Canada, modelos 2026.")

# ---------- 2. Mi gasto ----------
with tab_gasto:
    st.subheader("Calcula tu gasto del mes")
    with st.form("form_gasto"):
        modelo = st.selectbox("Tu modelo", nombres_catalogo, key="gasto_modelo")
        km_dia = st.number_input("Km por día (ida y vuelta)", min_value=1.0, value=40.0, step=1.0, key="gasto_km")
        dias = st.number_input("Días al mes que vas al trabajo", min_value=1, max_value=31, value=22, key="gasto_dias")
        calcular = st.form_submit_button("Calcular")
    if calcular:
        vehiculo = por_nombre[modelo]
        res = calculos.resumen(vehiculo, km_dia, dias, precios, factores)
        registrar("Mi gasto", modelo, calculos.km_mes(km_dia, dias), res)
        mostrar_resumen(res)

# ---------- 3. Comparar ----------
with tab_comparar:
    st.subheader("Compara dos modelos")
    with st.form("form_comparar"):
        col_a, col_b = st.columns(2)
        modelo_a = col_a.selectbox("Modelo A", nombres_catalogo, index=0, key="comp_a")
        modelo_b = col_b.selectbox("Modelo B", nombres_catalogo, index=len(nombres_catalogo) - 1, key="comp_b")
        km_dia_c = st.number_input("Km por día (ida y vuelta)", min_value=1.0, value=40.0, step=1.0, key="comp_km")
        dias_c = st.number_input("Días al mes que vas al trabajo", min_value=1, max_value=31, value=22, key="comp_dias")
        comparar = st.form_submit_button("Comparar")
    if comparar:
        if modelo_a == modelo_b:
            st.warning("Elige dos modelos distintos.")
        else:
            res_a = calculos.resumen(por_nombre[modelo_a], km_dia_c, dias_c, precios, factores)
            res_b = calculos.resumen(por_nombre[modelo_b], km_dia_c, dias_c, precios, factores)
            comp = calculos.comparar(res_a, res_b)
            km_c = calculos.km_mes(km_dia_c, dias_c)
            registrar("Comparar", modelo_a, km_c, res_a)
            registrar("Comparar", modelo_b, km_c, res_b)

            col_a, col_b = st.columns(2)
            for col, nombre, res in [(col_a, modelo_a, res_a), (col_b, modelo_b, res_b)]:
                col.markdown(f"**{nombre}**")
                col.metric("Costo estimado al mes", f"B/. {res['costo_mes']:.2f}")
                col.metric("CO₂ estimado al mes", f"{res['co2_mes']:.2f} kg")

            barato = modelo_a if comp["mas_barato"] == "A" else modelo_b
            st.success(
                f"El {barato} te ahorra **B/. {comp['ahorro_mes']:.2f} al mes** "
                f"(B/. {comp['ahorro_anio']:.2f} al año) y {comp['co2_evitado']:.2f} kg de CO₂ al mes."
            )

# ---------- 4. Otro modelo ----------
with tab_otro:
    st.subheader("¿Tu carro no está en el catálogo?")
    st.write("Escribe cuántos km recorre con un litro (está en el manual o en el tablero).")
    with st.form("form_otro"):
        nombre_otro = st.text_input("Nombre de tu carro", value="Mi carro", key="otro_nombre")
        km_por_litro = st.number_input("Km por litro", min_value=1.0, value=10.0, step=0.5, key="otro_kml")
        tipo_comb = st.radio("Combustible", list(NOMBRE_COMBUSTIBLE.values()), horizontal=True, key="otro_comb")
        km_dia_o = st.number_input("Km por día (ida y vuelta)", min_value=1.0, value=40.0, step=1.0, key="otro_km")
        dias_o = st.number_input("Días al mes que vas al trabajo", min_value=1, max_value=31, value=22, key="otro_dias")
        calcular_otro = st.form_submit_button("Calcular")
    if calcular_otro:
        clave_comb = {v: k for k, v in NOMBRE_COMBUSTIBLE.items()}[tipo_comb]
        consumo = calculos.kml_a_l100(km_por_litro)
        otro = Vehiculo(nombre_otro, "", "Otro", None, clave_comb, consumo)
        res = calculos.resumen(otro, km_dia_o, dias_o, precios, factores)
        registrar("Otro modelo", nombre_otro, calculos.km_mes(km_dia_o, dias_o), res)
        st.caption(f"{km_por_litro:g} km por litro = {consumo:.2f} L cada 100 km · {tipo_comb}")
        mostrar_resumen(res)

# ---------- 5. Ranking ----------
with tab_ranking:
    st.subheader("Del más barato al más caro de mantener")
    df_rank = reportes.ranking(catalogo, precios, factores)
    st.dataframe(df_rank, hide_index=True)
    st.bar_chart(df_rank.set_index("Modelo")["Costo (B/. por 100 km)"], y_label="B/. cada 100 km")

    ruta = reportes.exportar_reporte(df_rank)
    with open(ruta, "rb") as archivo:
        st.download_button("Descargar reporte", archivo, file_name="reporte.csv", mime="text/csv")

# ---------- 6. Estadísticas ----------
with tab_estadisticas:
    st.subheader("Lo que dicen los datos (carros a gasolina 2026)")
    est = reportes.estadisticas(df_limpio)
    c1, c2, c3 = st.columns(3)
    c1.metric("Consumo promedio", f"{est['promedio']:.2f} L/100 km")
    c2.metric("Consumo mediano", f"{est['mediana']:.2f} L/100 km")
    c3.metric("Correlación motor – consumo", f"{est['correlacion']:.3f}")
    st.write(
        f"Por cada litro de motor, el consumo sube unos **{est['pendiente']:.2f} L cada 100 km** "
        f"(consumo ≈ {est['intercepto']:.2f} + {est['pendiente']:.2f} × litros de motor)."
    )
    st.scatter_chart(reportes.datos_dispersion(df_limpio), x="Motor (L)", y="Consumo (L/100 km)")
    st.markdown("**Sedán vs. SUV en el catálogo**")
    st.dataframe(reportes.comparar_tipos(catalogo), hide_index=True)

# ---------- 7. historia 2021–2026 ----------
with tab_historia:
    st.subheader("¿Qué cambió más desde 2021: los carros o el precio?")

    primero = precios_historicos.iloc[0]
    ultimo = precios_historicos.iloc[-1]
    maximo = precios_historicos.loc[precios_historicos["gasolina_91"].idxmax()]
    variacion = calculos.variacion(primero["gasolina_91"], ultimo["gasolina_91"])

    c1, c2 = st.columns(2)
    c1.metric(
        "Gasolina 91 vigente (B/. por litro)", f"{ultimo['gasolina_91']:.3f}",
        f"{variacion:+.1f} % desde {primero['vigente_desde']:%m/%Y}", delta_color="inverse",
    )
    c2.metric("Precio más alto desde 2021", f"B/. {maximo['gasolina_91']:.3f}", f"{maximo['vigente_desde']:%m/%Y}",
              delta_color="off")

    st.markdown("**Precio por litro en Panamá y Colón (cada 14 días)**")
    st.line_chart(precios_historicos.set_index("vigente_desde")[["gasolina_91", "gasolina_95", "diesel"]])

    st.markdown("**CO₂ promedio de los carros nuevos por año**")
    tendencia = reportes.tendencia_anual(df_historico)
    tendencia["Año"] = tendencia["Año"].astype(str)
    st.line_chart(tendencia.set_index("Año")["CO2 promedio (g/km)"])
    st.dataframe(tendencia, hide_index=True)

    st.markdown("**Un modelo año por año**")
    modelo_h = st.selectbox("Elige un modelo", list(NOMBRES_HISTORICOS), key="modelo_historia")
    marca, nombres = NOMBRES_HISTORICOS[modelo_h]
    precios_anio = reportes.precio_por_anio(precios_historicos)
    evolucion = reportes.evolucion_modelo(df_historico, marca, nombres, precios_anio)
    evolucion["Año"] = evolucion["Año"].astype(str)
    st.dataframe(evolucion, hide_index=True)
    st.bar_chart(evolucion.set_index("Año")["Costo (B/. por 100 km)"], y_label="B/. cada 100 km")
    st.caption("Costo cada 100 km = consumo del modelo de ese año × precio promedio de la gasolina 91 de ese año.")
