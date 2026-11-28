"""Reporte ejecutivo: canasta básica y salario mínimo en Panamá."""

from __future__ import annotations

import streamlit as st

from components import (
    cierre,
    encabezado,
    estilos,
    figura_aumento,
    figura_cadenas,
    figura_proporcion,
    indicadores,
    nota_aumento,
    nota_cadenas,
    nota_horas,
    titulo_bloque,
)
from data_loader import cargar_corte, preparar

st.set_page_config(
    page_title="Canasta básica y salario mínimo",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    datos = preparar(cargar_corte())
    st.markdown(estilos(), unsafe_allow_html=True)
    st.markdown(encabezado(), unsafe_allow_html=True)
    st.markdown(indicadores(datos), unsafe_allow_html=True)

    columna_aumento, columna_bolsillo = st.columns(2, gap="large")
    with columna_aumento:
        st.markdown(
            titulo_bloque(
                "La canasta de ACODECO subió más que el salario",
                "Cambio desde junio de 2019. Canasta de supermercados en la provincia y salario de la Región 1.",
            ),
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            figura_aumento(datos),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.markdown(
            f'<p class="rep-nota" style="margin-top:-0.2rem">{nota_aumento(datos)}</p>',
            unsafe_allow_html=True,
        )
    with columna_bolsillo:
        st.markdown(
            titulo_bloque(
                "Qué parte del salario se va en comida",
                "Porcentaje del salario de referencia en junio. ACODECO y MEF van por separado.",
            ),
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            figura_proporcion(datos),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.markdown(
            f'<p class="rep-nota" style="margin-top:-0.2rem">{nota_horas(datos)}</p>',
            unsafe_allow_html=True,
        )

    st.markdown(
        titulo_bloque(
            "Xtra y Machetazo quedan bajo el precio típico",
            "Índice de precio de septiembre de 2026, segunda quincena. Por debajo de 100, más barata que la tienda típica.",
        ),
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        figura_cadenas(datos),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.markdown(
        f'<p class="rep-nota" style="margin-top:-0.35rem">{nota_cadenas(datos)}</p>',
        unsafe_allow_html=True,
    )

    st.markdown(cierre(datos), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
