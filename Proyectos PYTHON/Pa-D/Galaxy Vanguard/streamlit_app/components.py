"""Piezas visuales del reporte. Sin lógica de datos nueva."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

OLIVO = "#3E4F38"
PETROLEO = "#1E3A4C"
TERRACOTA = "#8F4E3A"
TINTA = "#1A1C19"
SECUNDARIO = "#6E6A62"
REGLA = "#E4E0D8"
GRILLA = "#E7E3DB"
FUENTE = "Source Sans 3, Helvetica Neue, Helvetica, Arial, sans-serif"


def balboas(valor: float) -> str:
    return f"B/. {valor:,.2f}"


def porcentaje(valor: float, signo: bool = False) -> str:
    numero = f"{valor:+.1f}" if signo else f"{valor:.1f}"
    return f"{numero} %"


def porcentaje_corto(valor: float, signo: bool = False) -> str:
    numero = f"{valor:+.1f}" if signo else f"{valor:.1f}"
    return f"{numero}%"


def estilos() -> str:
    return f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&display=swap');

      html, body, [class*="css"] {{
        font-family: {FUENTE};
      }}
      .stApp {{
        background: #F3F2EF;
        color: {TINTA};
      }}
      #MainMenu, footer,
      [data-testid="stHeader"],
      [data-testid="stToolbar"],
      [data-testid="stDecoration"],
      [data-testid="stSidebar"],
      [data-testid="stSidebarCollapsedControl"],
      a[aria-label="Link to heading"] {{
        display: none !important;
      }}
      .block-container {{
        max-width: 1180px;
        padding: 1.35rem 1.4rem 1.1rem;
      }}
      [data-testid="column"] {{
        min-width: 0;
      }}
      div[data-testid="stVerticalBlock"] {{
        gap: 0.35rem;
      }}
      h1.rep-titulo {{
        margin: 0;
        font-size: 2.15rem;
        font-weight: 600;
        letter-spacing: -0.025em;
        line-height: 1.12;
        color: {TINTA};
      }}
      .rep-cabecera {{
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        gap: 1.5rem;
        padding-bottom: 0.85rem;
        border-bottom: 1px solid {REGLA};
      }}
      .rep-cabecera > div {{
        flex: 1 1 auto;
        min-width: 0;
      }}
      .rep-sub {{
        margin: 0.35rem 0 0;
        max-width: 40rem;
        font-size: 1.05rem;
        line-height: 1.35;
        color: {SECUNDARIO};
      }}
      .rep-periodo {{
        margin: 0;
        flex: 0 0 auto;
        font-size: 0.95rem;
        color: {SECUNDARIO};
        letter-spacing: 0.01em;
      }}
      .rep-kpis {{
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        margin: 0.15rem 0 0.35rem;
        border-bottom: 1px solid {REGLA};
      }}
      .rep-kpi {{
        padding: 0.95rem 1.15rem 0.9rem 0;
      }}
      .rep-kpi + .rep-kpi {{
        padding-left: 1.15rem;
        border-left: 1px solid {REGLA};
      }}
      .rep-valor {{
        margin: 0;
        font-size: 2.35rem;
        font-weight: 600;
        letter-spacing: -0.035em;
        line-height: 1;
        font-variant-numeric: tabular-nums;
        color: {TINTA};
      }}
      .rep-valor.rep-alerta {{
        color: {TERRACOTA};
      }}
      .rep-etiqueta {{
        margin: 0.45rem 0 0;
        font-size: 0.98rem;
        font-weight: 600;
        line-height: 1.25;
        color: {TINTA};
      }}
      .rep-nota {{
        margin: 0.2rem 0 0;
        font-size: 0.86rem;
        line-height: 1.35;
        color: {SECUNDARIO};
      }}
      .rep-seccion {{
        margin: 0.15rem 0 0.15rem;
      }}
      .rep-seccion h2 {{
        margin: 0;
        font-size: 1.15rem;
        font-weight: 600;
        letter-spacing: -0.015em;
        color: {TINTA};
      }}
      .rep-seccion h2,
      .rep-seccion p,
      .rep-nota,
      .rep-fuentes,
      .rep-respuesta {{
        overflow-wrap: break-word;
      }}
      .rep-seccion p {{
        margin: 0.2rem 0 0;
        font-size: 0.92rem;
        line-height: 1.35;
        color: {SECUNDARIO};
      }}
      .rep-cierre {{
        margin-top: 0.35rem;
        padding: 0.95rem 0 0.2rem;
        border-top: 1px solid {REGLA};
      }}
      .rep-cierre h2 {{
        margin: 0;
        max-width: 38rem;
        font-size: 1.28rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        line-height: 1.25;
        color: {TINTA};
      }}
      .rep-respuesta {{
        margin: 0.45rem 0 0;
        max-width: 46rem;
        font-size: 1.05rem;
        line-height: 1.4;
        color: {TINTA};
      }}
      .rep-fuentes {{
        margin: 0.55rem 0 0;
        font-size: 0.8rem;
        line-height: 1.4;
        color: {SECUNDARIO};
      }}
      @media (min-width: 901px) {{
        h1.rep-titulo {{
          white-space: nowrap;
        }}
      }}
      @media (max-width: 900px) {{
        .rep-cabecera {{
          flex-direction: column;
          align-items: flex-start;
          gap: 0.35rem;
        }}
        .rep-kpis {{
          grid-template-columns: 1fr 1fr;
        }}
        .rep-kpi:nth-child(odd) {{
          padding-left: 0;
          border-left: 0;
        }}
        .rep-kpi:nth-child(3),
        .rep-kpi:nth-child(4) {{
          border-top: 1px solid {REGLA};
        }}
        .rep-valor {{
          font-size: 1.85rem;
        }}
        h1.rep-titulo {{
          font-size: 1.7rem;
        }}
        div[data-testid="stHorizontalBlock"] {{
          flex-direction: column;
        }}
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
          width: 100% !important;
          flex: 1 1 100% !important;
        }}
      }}
    </style>
    """


def encabezado() -> str:
    return """
    <header class="rep-cabecera">
      <div>
        <h1 class="rep-titulo">¿Cuánto de tu salario se va en comida?</h1>
        <p class="rep-sub">Análisis del costo de la canasta básica y el salario mínimo en Panamá.</p>
      </div>
      <p class="rep-periodo">2019, 2022 y 2026</p>
    </header>
    """


def indicadores(datos: dict) -> str:
    return f"""
    <section class="rep-kpis">
      <article class="rep-kpi">
        <p class="rep-valor">{balboas(datos["canasta_2026"])}</p>
        <p class="rep-etiqueta">Canasta ACODECO, junio 2026</p>
        <p class="rep-nota">Junio 2019: {balboas(datos["canasta_2019"])}. MEF: {balboas(datos["mef_2026"])}.</p>
      </article>
      <article class="rep-kpi">
        <p class="rep-valor">{balboas(datos["salario_2026"])}</p>
        <p class="rep-etiqueta">Salario mínimo de referencia</p>
        <p class="rep-nota">Gran empresa, Región 1. {balboas(datos["hora_2026"])} por hora × 208. En 2019: {balboas(datos["salario_2019"])}.</p>
      </article>
      <article class="rep-kpi">
        <p class="rep-valor">{porcentaje_corto(datos["pct_2026"])}</p>
        <p class="rep-etiqueta">De ese salario, canasta ACODECO</p>
        <p class="rep-nota">Junio 2019: {porcentaje(datos["pct_2019"])}. El MEF equivale al {porcentaje(datos["pct_mef_2026"])}.</p>
      </article>
      <article class="rep-kpi">
        <p class="rep-valor rep-alerta">{porcentaje_corto(datos["var_canasta_2026"], signo=True)}</p>
        <p class="rep-etiqueta">Canasta ACODECO desde 2019</p>
        <p class="rep-nota">El salario subió {porcentaje(datos["var_salario_2026"], signo=True)}. El MEF, {porcentaje(datos["var_mef_2026"], signo=True)}.</p>
      </article>
    </section>
    """


def titulo_bloque(titulo: str, texto: str) -> str:
    return f"""
    <div class="rep-seccion">
      <h2>{titulo}</h2>
      <p>{texto}</p>
    </div>
    """


def _base_layout(alto: int) -> dict:
    return dict(
        font=dict(family=FUENTE, color=TINTA, size=14),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=alto,
        margin=dict(l=4, r=8, t=28, b=4),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            x=0,
            font=dict(size=13, color=TINTA),
        ),
        hoverlabel=dict(font=dict(family=FUENTE, size=13), bgcolor="#FFFdfb", bordercolor=REGLA),
        uniformtext=dict(minsize=12, mode="show"),
    )


def _posiciones(corte: pd.DataFrame) -> tuple[list[int], list[str]]:
    """Posiciones fijas. Plotly lee un año suelto como fecha y, en UTC-5, 2026 pasa a 2025."""
    orden = list(corte.sort_values("anio")["anio"].astype(int))
    return list(range(len(orden))), [str(anio) for anio in orden]


def figura_aumento(datos: dict) -> go.Figure:
    """Cambio porcentual de la canasta ACODECO y del salario, respecto a junio de 2019."""
    corte = datos["corte"].sort_values("anio")
    posiciones, anios = _posiciones(corte)
    canasta = [float(v) for v in corte["var_canasta_pct"]]
    salario = [float(v) for v in corte["var_salario_pct"]]
    figura = go.Figure()
    figura.add_trace(
        go.Bar(
            name="Canasta ACODECO",
            x=posiciones,
            y=canasta,
            marker_color=OLIVO,
            text=["" if valor == 0 else porcentaje(valor, signo=True) for valor in canasta],
            textposition="outside",
            textfont=dict(color=OLIVO, size=13),
            hovertemplate="Canasta ACODECO<br>%{y:.1f} % desde 2019<extra></extra>",
            cliponaxis=False,
        )
    )
    figura.add_trace(
        go.Bar(
            name="Salario Región 1",
            x=posiciones,
            y=salario,
            marker_color=PETROLEO,
            text=["" if valor == 0 else porcentaje(valor, signo=True) for valor in salario],
            textposition="outside",
            textfont=dict(color=PETROLEO, size=13),
            hovertemplate="Salario Región 1<br>%{y:.1f} % desde 2019<extra></extra>",
            cliponaxis=False,
        )
    )
    figura.update_layout(
        barmode="group",
        bargap=0.32,
        bargroupgap=0.12,
        yaxis=dict(
            title="",
            ticksuffix=" %",
            range=[0, 22],
            gridcolor=GRILLA,
            zerolinecolor="#C9C4BB",
            showline=False,
            tickfont=dict(size=12, color=SECUNDARIO),
        ),
        xaxis=dict(
            type="linear",
            tickmode="array",
            tickvals=posiciones,
            ticktext=anios,
            showline=False,
            tickfont=dict(size=14, color=TINTA),
        ),
        **_base_layout(268),
    )
    figura.update_layout(margin=dict(l=8, r=8, t=32, b=8))
    return figura


def figura_proporcion(datos: dict) -> go.Figure:
    """Parte del salario de referencia que cubre cada canasta en junio."""
    corte = datos["corte"].sort_values("anio")
    _posiciones_bajas, anios = _posiciones(corte)
    # El valor más alto queda arriba: 2019, luego 2022, luego 2026.
    posiciones = list(range(len(anios) - 1, -1, -1))
    acodeco = [float(v) for v in corte["pct_salario_acodeco"]]
    mef = [float(v) for v in corte["pct_salario_mef"]]
    figura = go.Figure()
    figura.add_trace(
        go.Bar(
            name="ACODECO",
            y=posiciones,
            x=acodeco,
            orientation="h",
            marker_color=OLIVO,
            text=[porcentaje(valor) for valor in acodeco],
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(color="#FFFFFF", size=13),
            hovertemplate="ACODECO: %{x:.1f} % del salario<extra></extra>",
            cliponaxis=False,
        )
    )
    figura.add_trace(
        go.Bar(
            name="MEF",
            y=posiciones,
            x=mef,
            orientation="h",
            marker_color="#6F5844",
            text=[porcentaje(valor) for valor in mef],
            textposition="inside",
            insidetextanchor="end",
            textfont=dict(color="#FFFFFF", size=13),
            hovertemplate="MEF: %{x:.1f} % del salario<extra></extra>",
            cliponaxis=False,
        )
    )
    figura.update_layout(
        barmode="group",
        bargap=0.28,
        bargroupgap=0.08,
        xaxis=dict(
            range=[0, 100],
            autorange=False,
            ticksuffix=" %",
            dtick=25,
            gridcolor=GRILLA,
            zeroline=False,
            showline=False,
            tickfont=dict(size=12, color=SECUNDARIO),
        ),
        yaxis=dict(
            type="linear",
            tickmode="array",
            tickvals=posiciones,
            ticktext=anios,
            showline=False,
            tickfont=dict(size=14, color=TINTA),
        ),
        **_base_layout(268),
    )
    figura.update_layout(margin=dict(l=52, r=28, t=32, b=8))
    return figura


def figura_cadenas(datos: dict) -> go.Figure:
    """Índice de septiembre de 2026. 100 es la tienda típica de ese corte."""
    grupos = datos["cadenas"].sort_values("indice")
    nombres = list(grupos["grupo"])
    indices = [float(valor) for valor in grupos["indice"]]
    colores = [OLIVO if valor < 100 else TERRACOTA for valor in indices]
    figura = go.Figure()
    figura.add_trace(
        go.Bar(
            y=nombres,
            x=indices,
            orientation="h",
            marker_color=colores,
            text=[f"{valor:.1f}" for valor in indices],
            textposition="outside",
            textfont=dict(color=TINTA, size=13),
            hovertemplate="%{y}: índice %{x:.1f}<extra></extra>",
            cliponaxis=False,
            showlegend=False,
        )
    )
    figura.add_vline(x=100, line_width=1, line_color=SECUNDARIO)
    figura.update_layout(
        xaxis=dict(
            range=[70, 145],
            gridcolor=GRILLA,
            zeroline=False,
            showline=False,
            tickfont=dict(size=12, color=SECUNDARIO),
        ),
        yaxis=dict(
            autorange="reversed",
            showline=False,
            tickfont=dict(size=14, color=TINTA),
        ),
        **_base_layout(248),
    )
    figura.update_layout(margin=dict(l=110, r=36, t=12, b=8))
    return figura


def nota_horas(datos: dict) -> str:
    acodeco = datos["horas_acodeco"]
    mef = datos["horas_mef"]
    return (
        f"En junio de 2026 la canasta de ACODECO equivalía al {datos['pct_2026']:.1f} % "
        f"de ese salario. En junio de 2019 era el {datos['pct_2019']:.1f} % "
        f"y en junio de 2022 el {datos['pct_2022']:.1f} %. "
        f"Pagarla exigía {acodeco[2019]:.1f} horas en 2019, {acodeco[2022]:.1f} en 2022 "
        f"y {acodeco[2026]:.1f} en 2026. "
        f"El costo del MEF pasó de {datos['pct_mef_2019']:.1f} % a {datos['pct_mef_2026']:.1f} %, "
        f"y de {mef[2019]:.1f} a {mef[2026]:.1f} horas."
    )


def nota_cadenas(datos: dict) -> str:
    grupos = datos["cadenas"].sort_values("indice")
    barata = grupos.iloc[0]
    cara = grupos.iloc[-1]
    return (
        f"100 es la tienda típica de ese corte. {barata['grupo']} queda en {barata['indice']:.1f} "
        f"y {cara['grupo']} en {cara['indice']:.1f}. "
        f"La estimación del costo de junio va de {balboas(float(barata['costo']))} "
        f"a {balboas(float(cara['costo']))}. "
        f"El índice de 2026 es de la segunda quincena de septiembre. "
        f"El monto es el costo oficial de ACODECO en junio multiplicado por el índice y dividido entre 100. "
        f"ACODECO no publica las cantidades de cada producto, así que no es una suma de los 59 precios."
    )


def cierre(datos: dict) -> str:
    respuesta = (
        f"De junio de 2019 a junio de 2026, la canasta de ACODECO subió "
        f"{porcentaje(datos['var_canasta_2026'])} y el salario mínimo de referencia "
        f"{porcentaje(datos['var_salario_2026'])}. "
        f"El costo del MEF, en su propia medición, subió {porcentaje(datos['var_mef_2026'])}."
    )
    detalle = (
        "Junio, el mes presente en las dos canastas. "
        "Salario de comercio al por menor, gran empresa, Región 1 (hora × 208). "
        "ACODECO mide supermercados de la provincia de Panamá. "
        "El MEF mide el costo calórico familiar de Panamá y San Miguelito. No se promedian."
    )
    return f"""
    <section class="rep-cierre">
      <h2>¿El salario mínimo ha crecido al mismo ritmo que el costo de alimentarse?</h2>
      <p class="rep-respuesta">{respuesta}</p>
      <p class="rep-fuentes">Fuentes: INEC, ACODECO, MEF y Gaceta Oficial. {detalle}</p>
    </section>
    """


def nota_aumento(datos: dict) -> str:
    return (
        f"De 2022 a 2026 el salario subió {porcentaje(datos['var_salario_22_26'])} "
        f"y la canasta de ACODECO {porcentaje(datos['var_canasta_22_26'])}. "
        f"El costo del MEF subió {porcentaje(datos['var_mef_2022'])} hasta 2022 "
        f"y {porcentaje(datos['var_mef_2026'])} hasta 2026."
    )
