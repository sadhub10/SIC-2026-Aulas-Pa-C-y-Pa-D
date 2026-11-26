"""
Módulo de Visualización Gráfica de Alto Impacto
Proyecto: AstraMed - Samsung Innovation Campus (SIC)
Alineado con la paleta institucional Samsung (#034EA2, #1428A0, #5C9CE6)
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Configuración de estilo global
SAMSUNG_BLUE = "#034EA2"
SAMSUNG_DARK = "#0B192C"
SAMSUNG_LIGHT_BLUE = "#00A9E0"
SAMSUNG_ACCENT = "#2A60E4"
SAMSUNG_GRAY = "#F4F6F9"
PALETTE_SAMSUNG = ["#034EA2", "#00A9E0", "#5C9CE6", "#203A43", "#7A869A"]

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.edgecolor"] = "#CCCCCC"
plt.rcParams["axes.linewidth"] = 0.8


def plot_specialty_distribution(df: pd.DataFrame, output_dir: str = "resources") -> str:
    """Genera gráfico de barras con el volumen y porcentaje de consultas por especialidad."""
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)

    spec_counts = df["specialty"].value_counts()
    bars = ax.barh(spec_counts.index, spec_counts.values, color=SAMSUNG_BLUE, edgecolor="none", height=0.6)

    # Añadir etiquetas con valores absolutos y porcentajes
    total = len(df)
    for bar in bars:
        width = bar.get_width()
        pct = (width / total) * 100
        ax.text(
            width + 2,
            bar.get_y() + bar.get_height() / 2,
            f"{int(width)} ({pct:.1f}%)",
            va="center",
            ha="left",
            fontweight="bold",
            color="#222222",
        )

    ax.set_title("Volumen de Consultas por Especialidad Médica", fontsize=13, fontweight="bold", pad=15, color=SAMSUNG_DARK)
    ax.set_xlabel("Número de Consultas", fontsize=10, labelpad=8)
    ax.set_xlim(0, max(spec_counts.values) + 20)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    out_path = os.path.join(output_dir, "01_distribucion_especialidades.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_satisfaction_by_mode(df: pd.DataFrame, output_dir: str = "resources") -> str:
    """Genera gráfico de barras apiladas de satisfacción según la modalidad (Video, Audio, Chat)."""
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

    crosstab_pct = pd.crosstab(df["consultation_mode"], df["satisfaction_category"], normalize="index") * 100
    colors = ["#E63946", "#F1FAEE", "#2A9D8F"]  # Rojo suave para baja, claro para neutra, verde azulado para alta
    colors_samsung = ["#D9534F", "#F0AD4E", "#034EA2"]

    crosstab_pct.plot(kind="bar", stacked=True, ax=ax, color=colors_samsung, width=0.55, edgecolor="white", linewidth=1)

    ax.set_title("Distribución de Satisfacción según Modalidad de Consulta", fontsize=13, fontweight="bold", pad=15, color=SAMSUNG_DARK)
    ax.set_xlabel("Modalidad de Consulta", fontsize=10, labelpad=8)
    ax.set_ylabel("Porcentaje de Pacientes (%)", fontsize=10)
    ax.set_xticklabels(crosstab_pct.index, rotation=0, fontweight="bold")
    ax.set_ylim(0, 100)
    ax.legend(title="Nivel de Satisfacción", frameon=True, facecolor="white", edgecolor="#DDD")

    # Valores dentro de las barras
    for c in ax.containers:
        for patch in c:
            h = patch.get_height()
            if h > 8:
                ax.text(
                    patch.get_x() + patch.get_width() / 2,
                    patch.get_y() + h / 2,
                    f"{h:.1f}%",
                    ha="center",
                    va="center",
                    color="white" if patch.get_facecolor()[0] < 0.6 else "black",
                    fontweight="bold",
                    fontsize=9,
                )

    out_path = os.path.join(output_dir, "02_satisfaccion_por_modalidad.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_duration_vs_satisfaction(df: pd.DataFrame, output_dir: str = "resources") -> str:
    """Genera boxplot de la duración de consultas según el nivel de satisfacción reportado."""
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

    sns.boxplot(
        x="patient_satisfaction",
        y="duration_minutes",
        data=df,
        ax=ax,
        hue="patient_satisfaction",
        palette=["#D9534F", "#F0AD4E", "#5BC0DE", "#0275D8", "#034EA2"],
        width=0.5,
        boxprops=dict(alpha=0.85),
        legend=False,
    )

    # Medias por nivel de satisfacción
    means = df.groupby("patient_satisfaction")["duration_minutes"].mean()
    for i, m in enumerate(means):
        ax.scatter(i, m, color="black", s=35, zorder=5)
        ax.text(i, m + 2.0, f"x̄={m:.1f}m", ha="center", fontsize=8, fontweight="bold", color="#111")

    ax.set_title("Duración de Consulta Médica por Nivel de Satisfacción (1 a 5)", fontsize=13, fontweight="bold", pad=15, color=SAMSUNG_DARK)
    ax.set_xlabel("Puntaje de Satisfacción del Paciente", fontsize=10, labelpad=8)
    ax.set_ylabel("Duración (minutos)", fontsize=10)
    ax.set_ylim(0, 70)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    out_path = os.path.join(output_dir, "03_duracion_vs_satisfaccion.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_followup_and_prescription(df: pd.DataFrame, output_dir: str = "resources") -> str:
    """Genera gráfico comparativo de tasa de seguimiento y recetas por especialidad."""
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)

    grouped = df.groupby("specialty").agg(
        receta=("prescription_binary", lambda x: x.mean() * 100),
        seguimiento=("follow_up_binary", lambda x: x.mean() * 100),
    ).reset_index()

    x = np.arange(len(grouped))
    width = 0.35

    rects1 = ax.bar(x - width / 2, grouped["receta"], width, label="Requiere Receta (%)", color=SAMSUNG_BLUE)
    rects2 = ax.bar(x + width / 2, grouped["seguimiento"], width, label="Requiere Seguimiento (%)", color=SAMSUNG_LIGHT_BLUE)

    ax.set_title("Tasas de Prescripción y Seguimiento Clínico por Especialidad", fontsize=13, fontweight="bold", pad=15, color=SAMSUNG_DARK)
    ax.set_xlabel("Especialidad Médica", fontsize=10, labelpad=8)
    ax.set_ylabel("Porcentaje (%)", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(grouped["specialty"], fontweight="bold")
    ax.set_ylim(0, 75)
    ax.legend(frameon=True, facecolor="white")
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for r in rects1:
        ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 1, f"{r.get_height():.1f}%", ha="center", fontsize=8, fontweight="bold")
    for r in rects2:
        ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 1, f"{r.get_height():.1f}%", ha="center", fontsize=8, fontweight="bold")

    out_path = os.path.join(output_dir, "04_seguimiento_por_especialidad.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_symptom_diagnosis_heatmap(df: pd.DataFrame, output_dir: str = "resources") -> str:
    """Genera matriz de calor de correlación clínica entre síntomas de ingreso y diagnósticos finales."""
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    matrix = pd.crosstab(df["symptom"], df["diagnosis"])
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", ax=ax, cbar_kws={"label": "Frecuencia de Casos"}, linewidths=0.5)

    ax.set_title("Matriz de Co-ocurrencia: Síntomas vs Diagnósticos", fontsize=13, fontweight="bold", pad=15, color=SAMSUNG_DARK)
    ax.set_xlabel("Diagnóstico Clínico Emitido", fontsize=10, labelpad=8, fontweight="bold")
    ax.set_ylabel("Síntoma Principal de Ingreso", fontsize=10, labelpad=8, fontweight="bold")
    ax.tick_params(axis="x", rotation=30)

    out_path = os.path.join(output_dir, "05_matriz_sintoma_diagnostico.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_feature_importance(importances: pd.Series, output_dir: str = "resources") -> str:
    """Genera gráfico de barras con la importancia de variables del modelo predictivo."""
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

    top_features = importances.head(10).sort_values(ascending=True)
    bars = ax.barh(top_features.index, top_features.values * 100, color=SAMSUNG_BLUE, height=0.6)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.3, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", va="center", ha="left", fontweight="bold", fontsize=8)

    ax.set_title("Importancia de Características - Modelo Predictivo de Satisfacción", fontsize=12, fontweight="bold", pad=15, color=SAMSUNG_DARK)
    ax.set_xlabel("Importancia Relativa (%)", fontsize=10, labelpad=8)
    ax.set_xlim(0, max(top_features.values * 100) + 5)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    out_path = os.path.join(output_dir, "06_importancia_caracteristicas.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def plot_executive_multipanel_dashboard(df: pd.DataFrame, risk_labels: np.ndarray = None, output_dir: str = "resources") -> str:
    """
    Genera un Dashboard Ejecutivo Multi-Panel integrado utilizando Matplotlib GridSpec puro,
    demostrando control avanzado de ejes, subplots, ejes gemelos (twinx) y anotaciones.
    """
    import matplotlib.gridspec as gridspec

    os.makedirs(output_dir, exist_ok=True)
    fig = plt.figure(figsize=(16, 12), dpi=300)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.25)

    # -------------------------------------------------------------
    # Panel 1 (gs[0, 0]): Histograma de Duraciones con Percentiles NumPy
    # -------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    durations = df["duration_minutes"].to_numpy()
    n_bins, bins, patches = ax1.hist(durations, bins=15, color=SAMSUNG_BLUE, edgecolor="white", alpha=0.85)

    p25, p50, p75 = np.percentile(durations, [25, 50, 75])
    mean_val = np.mean(durations)

    ax1.axvline(mean_val, color="#D9534F", linestyle="--", linewidth=2, label=f"Media ({mean_val:.1f} m)")
    ax1.axvline(p50, color="#F0AD4E", linestyle=":", linewidth=2, label=f"Mediana P50 ({p50:.1f} m)")
    ax1.axvline(p25, color="#5CB85C", linestyle="-.", linewidth=1.5, label=f"P25 ({p25:.1f} m)")
    ax1.axvline(p75, color="#00A9E0", linestyle="-.", linewidth=1.5, label=f"P75 ({p75:.1f} m)")

    ax1.set_title("A. Distribución de Duración con Percentiles NumPy", fontsize=12, fontweight="bold", color=SAMSUNG_DARK)
    ax1.set_xlabel("Duración de la Consulta (minutos)", fontsize=10)
    ax1.set_ylabel("Frecuencia de Consultas", fontsize=10)
    ax1.legend(loc="upper right", frameon=True, fontsize=8)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    # -------------------------------------------------------------
    # Panel 2 (gs[0, 1]): Satisfacción Media y Proporción por Modalidad
    # -------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    mode_stats = df.groupby("consultation_mode").agg(
        sat_mean=("patient_satisfaction", "mean"),
        vol=("consultation_id", "count")
    ).reset_index()

    colors_mode = [SAMSUNG_BLUE, SAMSUNG_LIGHT_BLUE, SAMSUNG_ACCENT]
    bars = ax2.bar(mode_stats["consultation_mode"], mode_stats["sat_mean"], color=colors_mode, width=0.45, edgecolor="none")
    ax2.set_ylim(0, 5)
    ax2.axhline(3.0, color="gray", linestyle="--", linewidth=1, label="Nivel Neutro (3.0)")
    ax2.set_title("B. Satisfacción Promedio según Canal de Consulta", fontsize=12, fontweight="bold", color=SAMSUNG_DARK)
    ax2.set_xlabel("Modalidad de Telemedicina", fontsize=10)
    ax2.set_ylabel("Satisfacción Media (Escala 1 a 5)", fontsize=10)
    ax2.legend(loc="lower right", fontsize=8)

    for bar, vol in zip(bars, mode_stats["vol"]):
        y_val = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width() / 2, y_val + 0.12, f"{y_val:.2f}/5\n(n={vol})", ha="center", fontsize=9, fontweight="bold")

    # -------------------------------------------------------------
    # Panel 3 (gs[1, 0]): Volumen Etario con Eje Gemelo (twinx) de Seguimiento
    # -------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    age_analysis = df.groupby("age_group", observed=True).agg(
        total=("consultation_id", "count"),
        follow_pct=("follow_up_binary", lambda x: np.mean(x) * 100)
    ).reset_index()

    x_indices = np.arange(len(age_analysis))
    bars3 = ax3.bar(x_indices, age_analysis["total"], color=SAMSUNG_BLUE, alpha=0.75, width=0.4, label="Volumen Consultas")
    ax3.set_xticks(x_indices)
    ax3.set_xticklabels(age_analysis["age_group"], rotation=15, fontsize=9)
    ax3.set_ylabel("Total de Pacientes", fontsize=10, color=SAMSUNG_BLUE)
    ax3.set_title("C. Volumen por Grupo Etario y Tasa de Seguimiento (Dual Axis)", fontsize=12, fontweight="bold", color=SAMSUNG_DARK)

    # Eje secundario twinx
    ax3_twin = ax3.twinx()
    ax3_twin.plot(x_indices, age_analysis["follow_pct"], color="#E63946", marker="o", linewidth=2.5, label="Tasa Seguimiento (%)")
    ax3_twin.set_ylabel("Tasa de Seguimiento Requerido (%)", fontsize=10, color="#E63946")
    ax3_twin.set_ylim(0, 100)
    ax3_twin.grid(False)

    for i, pct in enumerate(age_analysis["follow_pct"]):
        ax3_twin.text(i, pct + 3, f"{pct:.1f}%", ha="center", color="#E63946", fontweight="bold", fontsize=9)

    # -------------------------------------------------------------
    # Panel 4 (gs[1, 1]): Distribución del Índice Compuesto de Riesgo (NumPy)
    # -------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    if risk_labels is not None:
        unique_labels, counts = np.unique(risk_labels, return_counts=True)
        colors_risk = {"BAJO RIESGO": "#5CB85C", "RIESGO MODERADO": "#F0AD4E", "ALTO RIESGO": "#D9534F"}
        bar_colors = [colors_risk.get(label, SAMSUNG_BLUE) for label in unique_labels]
        bars4 = ax4.bar(unique_labels, counts, color=bar_colors, width=0.5, edgecolor="none")
        ax4.set_title("D. Clasificación del Índice Compuesto de Riesgo (Álgebra NumPy)", fontsize=12, fontweight="bold", color=SAMSUNG_DARK)
        ax4.set_xlabel("Nivel de Riesgo Operacional y Clínico", fontsize=10)
        ax4.set_ylabel("Número de Casos", fontsize=10)

        for bar in bars4:
            h = bar.get_height()
            pct = (h / len(df)) * 100
            ax4.text(bar.get_x() + bar.get_width() / 2, h + 3, f"{h} ({pct:.1f}%)", ha="center", fontweight="bold", fontsize=9)
    else:
        ax4.text(0.5, 0.5, "Datos de riesgo no disponibles", ha="center", va="center")

    fig.suptitle("ASTRAMED - DASHBOARD EJECUTIVO DE TELEMEDICINA\nSamsung Innovation Campus (SIC 2025/2026)", fontsize=15, fontweight="bold", color=SAMSUNG_DARK, y=0.98)

    out_path = os.path.join(output_dir, "00_dashboard_ejecutivo_multipanel.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    return out_path


def plot_triage_concordance(df: pd.DataFrame, output_dir: str = "resources") -> str:
    """
    Genera un gráfico de barras comparativo de fallas de derivación en triaje clínico
    para los tres síntomas clave: Erupción cutánea, Dolor torácico y Ansiedad.
    """
    os.makedirs(output_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)

    # Datos calculados
    symptoms_eval = [
        ("Erupción cutánea\n(Skin Rash)", "Dermatology", "Skin Rash"),
        ("Dolor torácico\n(Chest Pain)", "Cardiology", "Chest Pain"),
        ("Ansiedad\n(Anxiety)", "Psychiatry", "Anxiety")
    ]

    labels = []
    correct_pcts = []
    mismatch_pcts = []

    for label, target_spec, sym in symptoms_eval:
        sub = df[df["symptom"] == sym]
        corr = (sub["specialty"] == target_spec).mean() * 100
        mis = 100.0 - corr
        labels.append(label)
        correct_pcts.append(corr)
        mismatch_pcts.append(mis)

    y = np.arange(len(labels))
    height = 0.45

    # Barras horizontales apiladas
    bars1 = ax.barh(y, correct_pcts, height, label="Asignado a Especialidad Correcta (%)", color=SAMSUNG_BLUE, edgecolor="none")
    bars2 = ax.barh(y, mismatch_pcts, height, left=correct_pcts, label="Falla de Derivación Clínica (Fuera de Especialidad) (%)", color="#D9534F", edgecolor="none")

    ax.set_title("Fallas de Derivación en Triaje Clínico por Síntoma Principal (AstraMed)", fontsize=12, fontweight="bold", pad=15, color=SAMSUNG_DARK)
    ax.set_xlabel("Porcentaje de Consultas (%)", fontsize=10, labelpad=8)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontweight="bold", fontsize=9)
    ax.set_xlim(0, 105)
    ax.legend(loc="lower right", frameon=True, fontsize=8)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    # Añadir porcentajes dentro de las barras
    for bar in bars1:
        w = bar.get_width()
        if w > 10:
            ax.text(w / 2, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", ha="center", va="center", color="white", fontweight="bold", fontsize=9)

    for bar, left in zip(bars2, correct_pcts):
        w = bar.get_width()
        ax.text(left + w / 2, bar.get_y() + bar.get_height() / 2, f"{w:.1f}% ALERTA", ha="center", va="center", color="white", fontweight="bold", fontsize=9)

    out_path = os.path.join(output_dir, "07_coherencia_triaje_especialidad.png")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    return out_path


def generate_all_visualizations(df: pd.DataFrame, feature_importances: pd.Series = None, risk_labels: np.ndarray = None, output_dir: str = "resources") -> list:
    """Ejecuta la generación completa de gráficos y retorna la lista de archivos creados."""
    plots = [
        plot_executive_multipanel_dashboard(df, risk_labels=risk_labels, output_dir=output_dir),
        plot_specialty_distribution(df, output_dir),
        plot_satisfaction_by_mode(df, output_dir),
        plot_duration_vs_satisfaction(df, output_dir),
        plot_followup_and_prescription(df, output_dir),
        plot_symptom_diagnosis_heatmap(df, output_dir),
        plot_triage_concordance(df, output_dir),
    ]
    if feature_importances is not None:
        plots.append(plot_feature_importance(feature_importances, output_dir))
    return plots
