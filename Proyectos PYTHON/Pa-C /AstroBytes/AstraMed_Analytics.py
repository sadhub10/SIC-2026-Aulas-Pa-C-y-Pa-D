"""
========================================================================================
SAMSUNG INNOVATION CAMPUS (SIC 2025/2026) - PROYECTO FINAL MODULO PYTHON
PROYECTO: AstraMed - Plataforma Analitica Predictiva para Telemedicina
SCRIPT PRINCIPAL: AstraMed_Analytics.py
========================================================================================
"""

import sys
import os
import numpy as np
import pandas as pd

# Configurar encoding seguro para terminales Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.data_loader import load_telemedicine_data, preprocess_and_engineer_features, get_data_summary
from src.eda_analysis import (
    compute_kpis,
    analyze_specialties,
    analyze_consultation_modes,
    run_statistical_hypothesis_tests,
    analyze_symptom_specialty_concordance,
)
from src.numpy_analytics import (
    calculate_numpy_vectorized_metrics,
    compute_clinical_risk_index_numpy,
    bootstrap_satisfaction_confidence_interval_numpy,
)
from src.visualizer import generate_all_visualizations
from src.modeling import train_predictive_models, generate_clinical_recommendations


def print_banner():
    banner = """
================================================================================
              SAMSUNG INNOVATION CAMPUS - SIC 2025/2026                         
               PROYECTO FINAL PYTHON: ASTRAMED ANALYTICS                        
  Plataforma de Optimizacion Clinica, Eficiencia y Satisfaccion del Paciente    
  Equipo: Jonathan Reyes | Jesus Torres | Ivy Janssen | David Morales           
================================================================================
    """
    print(banner)


def main():
    print_banner()

    data_file = "telemedicine_consultation_dataset.csv"
    print(f"[*] Paso 1: Cargando y validando dataset desde '{data_file}'...")
    raw_df = load_telemedicine_data(data_file)
    df = preprocess_and_engineer_features(raw_df)
    summary = get_data_summary(df)

    print(f"    [OK] Total de consultas procesadas: {summary['total_registros']}")
    print(f"    [OK] Registros nulos detectados: {summary['valores_nulos_totales']}")
    print(f"    [OK] Periodo de analisis: {summary['rango_fechas'][0]} a {summary['rango_fechas'][1]}")
    print(f"    [OK] Especialidades evaluadas ({len(summary['especialidades'])}): {', '.join(summary['especialidades'])}")
    print(f"    [OK] Modalidades evaluadas ({len(summary['modalidades'])}): {', '.join(summary['modalidades'])}\n")

    print("[*] Paso 2: Calculando Indicadores Clave de Desempeno (KPIs)...")
    kpis = compute_kpis(df)
    print("    +-----------------------------------------------+-----+")
    print(f"    | Satisfaccion Promedio (escala 1 a 5):         | {kpis['satisfaccion_promedio']:<4} |")
    print(f"    | Tasa de Pacientes con Alta Satisfaccion:      | {kpis['tasa_alta_satisfaccion_pct']}%|")
    print(f"    | Tasa de Pacientes con Baja Satisfaccion:      | {kpis['tasa_baja_satisfaccion_pct']}%|")
    print(f"    | Duracion Media de Consulta (minutos):         | {kpis['duracion_promedio_min']:<4}m |")
    print(f"    | Tasa Global de Prescripcion Medica:           | {kpis['tasa_prescripcion_pct']}%|")
    print(f"    | Tasa Global de Seguimiento Clinico Requerido: | {kpis['tasa_seguimiento_pct']}%|")
    print("    +-----------------------------------------------+-----+\n")

    print("[*] Paso 3: Computacion Numerica y Algebra Vectorial con NumPy...")
    np_metrics = calculate_numpy_vectorized_metrics(df)
    print(f"    [OK] Varianza de Duracion (np.var): {np_metrics['duracion_varianza_numpy']} min²")
    print(f"    [OK] Percentiles NumPy (P25: {np_metrics['percentiles_duracion']['p25']}m, "
          f"P50: {np_metrics['percentiles_duracion']['p50_mediana']}m, "
          f"P75: {np_metrics['percentiles_duracion']['p75']}m, "
          f"IQR: {np_metrics['percentiles_duracion']['iqr']}m)")
    print(f"    [OK] Outliers Detectados por Z-Score (> 2.5 std): {np_metrics['outliers_detectados_zscore']} consultas")

    bootstrap_ci = bootstrap_satisfaction_confidence_interval_numpy(df, n_iterations=1000)
    print(f"    [OK] Bootstrap 95% CI para Satisfaccion: [{bootstrap_ci['ci_inferior_95']}, {bootstrap_ci['ci_superior_95']}] "
          f"(Media estimada: {bootstrap_ci['media_bootstrap']})")

    risk_scores, risk_labels = compute_clinical_risk_index_numpy(df)
    df["risk_score_numpy"] = risk_scores
    df["risk_category_numpy"] = risk_labels
    high_risk_count = int(np.sum(risk_labels == "ALTO RIESGO"))
    mod_risk_count = int(np.sum(risk_labels == "RIESGO MODERADO"))
    low_risk_count = int(np.sum(risk_labels == "BAJO RIESGO"))
    print(f"    [OK] Indice de Riesgo Clinico (np.dot): Alto: {high_risk_count} ({high_risk_count/len(df)*100:.1f}%) | "
          f"Moderado: {mod_risk_count} ({mod_risk_count/len(df)*100:.1f}%) | "
          f"Bajo: {low_risk_count} ({low_risk_count/len(df)*100:.1f}%)\n")

    print("[*] Paso 4: Analisis Desglosado por Especialidad Medica (Pandas GroupBy):")
    spec_df = analyze_specialties(df)
    for _, row in spec_df.iterrows():
        print(f"    - {row['specialty']:<17} | Casos: {row['total_consultas']:>3} ({row['porcentaje_volumen']:>4.1f}%) | "
              f"Duracion: {row['duracion_media']:>4.1f}m | Satisfaccion: {row['satisfaccion_media']:.2f}/5 | "
              f"Seguimiento: {row['tasa_seguimiento_pct']:>4.1f}%")
    print()

    print("[*] Paso 5: Analisis de Modalidades de Atencion (Canales):")
    mode_df = analyze_consultation_modes(df)
    for _, row in mode_df.iterrows():
        print(f"    - {row['consultation_mode']:<7} | Casos: {row['total_consultas']:>3} ({row['porcentaje_uso']:>4.1f}%) | "
              f"Duracion Media: {row['duracion_media']:>4.1f}m | Satisfaccion: {row['satisfaccion_media']:.2f}/5 | "
              f"Alta Sat: {row['alta_satisfaccion_pct']:>4.1f}%")
    print()

    print("[*] Paso 6: Verificacion de Triaje y Concordancia Sintoma-Especialidad (Hallazgos AstraMed):")
    triage_results = analyze_symptom_specialty_concordance(df)
    rash = triage_results["erupcion_fuera_dermatologia"]
    chest = triage_results["dolor_toracico_fuera_cardiologia"]
    anx = triage_results["ansiedad_fuera_psiquiatria"]
    print(f"    - Erupcion cutanea (Skin Rash) fuera de Dermatologia:  {rash['porcentaje_desviado']}% ({rash['casos_desviados']}/{rash['total_casos']} casos)")
    print(f"    - Dolor toracico (Chest Pain) fuera de Cardiologia:    {chest['porcentaje_desviado']}% ({chest['casos_desviados']}/{chest['total_casos']} casos)")
    print(f"    - Ansiedad (Anxiety) fuera de Psiquiatria:             {anx['porcentaje_desviado']}% ({anx['casos_desviados']}/{anx['total_casos']} casos)")
    print(f"    [!] Alerta Clinica: {triage_results['tasa_global_fallas_pct']}% de consultas analizadas sufren de falla de derivacion inicial.")
    print("        AstraMed implementa validacion algoritmica en el DataFrame para corregir la asignacion pre-consulta.\n")

    print("[*] Paso 7: Ejecutando Pruebas Estadisticas de Hipotesis (SciPy):")
    tests = run_statistical_hypothesis_tests(df)
    print(f"    1. Chi2 Modalidad vs Satisfaccion: p-valor = {tests['test_modalidad_satisfaccion']['p_valor']}")
    print(f"       -> {tests['test_modalidad_satisfaccion']['conclusion']}")
    print(f"    2. Chi2 Especialidad vs Seguimiento: p-valor = {tests['test_especialidad_seguimiento']['p_valor']}")
    print(f"       -> {tests['test_especialidad_seguimiento']['conclusion']}")
    print(f"    3. ANOVA Duracion entre Modalidades: p-valor = {tests['anova_duracion_modalidad']['p_valor']}")
    print(f"       -> {tests['anova_duracion_modalidad']['conclusion']}\n")

    print("[*] Paso 8: Entrenamiento y Evaluacion de Modelos de Machine Learning (Scikit-Learn)...")
    ml_results = train_predictive_models(df)
    rf_acc = ml_results["random_forest"]["accuracy"] * 100
    lr_acc = ml_results["logistic_regression"]["accuracy"] * 100
    print(f"    [OK] Exactitud Random Forest Classifier: {rf_acc:.1f}%")
    print(f"    [OK] Exactitud Regresion Logistica Base:  {lr_acc:.1f}%")
    print("    [OK] Variables de Mayor Impacto en la Satisfaccion:")
    for feat, imp in list(ml_results["random_forest"]["top_features"].items())[:5]:
        print(f"       * {feat:<28}: {imp * 100:>5.2f}%")
    print()

    print("[*] Paso 9: Generando Graficos de Alta Resolucion en 'resources/' (Matplotlib & Seaborn)...")
    generated_plots = generate_all_visualizations(
        df,
        feature_importances=ml_results["feature_importances_series"],
        risk_labels=risk_labels,
        output_dir="resources"
    )
    for plot in generated_plots:
        print(f"    [OK] Guardado: {plot}")
    print()

    print("[*] Paso 10: Recomendaciones Operativas para la Gestion de Salud:")
    recommendations = generate_clinical_recommendations(df, ml_results)
    for i, rec in enumerate(recommendations, 1):
        print(f"\n    [{i}] {rec['area']}")
        print(f"        Evidencia: {rec['hallazgo']}")
        print(f"        Accion Sugerida: {rec['accion']}")

    print("\n" + "=" * 80)
    print("PIPELINE EJECUTADO CON EXITO. Todos los entregables y recursos fueron generados.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
