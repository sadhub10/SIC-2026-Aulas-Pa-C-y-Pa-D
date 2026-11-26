"""
Módulo de Computación Numérica y Álgebra Vectorial con NumPy
Proyecto: AstraMed - Samsung Innovation Campus (SIC)
Demuestra el uso avanzado de NumPy: broadcasting, arrays n-dimensionales,
percentiles, normalización min-max, z-scores y cálculo de índice compuesto de riesgo.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple


def calculate_numpy_vectorized_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula métricas estadísticas descriptivas y de dispersión utilizando
    operaciones vectoriales nativas de NumPy sobre arrays de NumPy.
    """
    # Extracción de arrays unidimensionales de NumPy
    durations = df["duration_minutes"].to_numpy(dtype=np.float64)
    ages = df["patient_age"].to_numpy(dtype=np.float64)
    satisfactions = df["patient_satisfaction"].to_numpy(dtype=np.float64)

    # 1. Medidas de tendencia central y dispersión con NumPy
    dur_mean = np.mean(durations)
    dur_median = np.median(durations)
    dur_std = np.std(durations, ddof=1)  # Desviación estándar muestral
    dur_variance = np.var(durations, ddof=1)

    # 2. Percentiles y rangos intercuartílicos con np.percentile
    p25, p50, p75, p90, p95 = np.percentile(durations, [25, 50, 75, 90, 95])
    iqr = p75 - p25

    # 3. Cálculo de Z-Scores vectorizados: z = (x - mean) / std
    z_scores_duration = (durations - dur_mean) / dur_std
    outliers_mask = np.abs(z_scores_duration) > 2.5
    num_outliers = np.sum(outliers_mask)

    # 4. Matriz de correlación de Pearson calculada con np.corrcoef
    data_matrix = np.vstack([durations, ages, satisfactions])
    correlation_matrix = np.corrcoef(data_matrix)

    # 5. Normalización Min-Max vectorial con NumPy: (x - min) / (max - min)
    min_val, max_val = np.min(durations), np.max(durations)
    dur_normalized = (durations - min_val) / (max_val - min_val)

    return {
        "duracion_media_numpy": round(float(dur_mean), 2),
        "duracion_mediana_numpy": round(float(dur_median), 2),
        "duracion_std_numpy": round(float(dur_std), 2),
        "duracion_varianza_numpy": round(float(dur_variance), 2),
        "percentiles_duracion": {
            "p25": round(float(p25), 2),
            "p50_mediana": round(float(p50), 2),
            "p75": round(float(p75), 2),
            "p90": round(float(p90), 2),
            "p95": round(float(p95), 2),
            "iqr": round(float(iqr), 2),
        },
        "outliers_detectados_zscore": int(num_outliers),
        "matriz_correlacion_numpy": np.round(correlation_matrix, 4).tolist(),
        "ejemplo_normalizado_minmax": np.round(dur_normalized[:5], 3).tolist(),
    }


def compute_clinical_risk_index_numpy(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Construye un Índice Compuesto de Riesgo Operacional (ICRO) utilizando álgebra vectorial
    y pesos ponderados mediante producto punto (dot product) con NumPy.

    Factores ponderados:
    - w1: Duración relativa normalizada (pesa 35%)
    - w2: Edad del paciente normalizada (pesa 25%)
    - w3: Banderas clínicas binarias (receta, seguimiento) (pesa 20%)
    - w4: Inverso de satisfacción (menor satisfacción = mayor riesgo de deserción) (pesa 20%)
    """
    # Arrays de entrada
    durations = df["duration_minutes"].to_numpy(dtype=np.float64)
    ages = df["patient_age"].to_numpy(dtype=np.float64)
    follow_up = np.where(df["follow_up_required"] == "Yes", 1.0, 0.0)
    prescrip = np.where(df["prescription_given"] == "Yes", 1.0, 0.0)
    satisfaction = df["patient_satisfaction"].to_numpy(dtype=np.float64)

    # Normalización Min-Max con NumPy
    norm_dur = (durations - np.min(durations)) / (np.max(durations) - np.min(durations))
    norm_age = (ages - np.min(ages)) / (np.max(ages) - np.min(ages))
    inv_sat = (5.0 - satisfaction) / 4.0  # Si satisfacción es 1 -> 1.0 (máximo riesgo)
    clinical_need = 0.5 * follow_up + 0.5 * prescrip

    # Matriz de características N x 4
    feature_matrix = np.column_stack([norm_dur, norm_age, clinical_need, inv_sat])

    # Vector de ponderación de pesos (suma 1.0)
    weights = np.array([0.35, 0.25, 0.20, 0.20], dtype=np.float64)

    # Producto punto vectorial con np.dot
    risk_scores = np.dot(feature_matrix, weights) * 100.0  # Escala 0 a 100

    # Clasificación categórica de riesgo con np.select
    conditions = [
        risk_scores >= 65.0,
        (risk_scores >= 40.0) & (risk_scores < 65.0),
        risk_scores < 40.0,
    ]
    categories = np.array(["ALTO RIESGO", "RIESGO MODERADO", "BAJO RIESGO"])
    risk_labels = np.select(conditions, categories, default="DESCONOCIDO")

    return risk_scores, risk_labels


def bootstrap_satisfaction_confidence_interval_numpy(df: pd.DataFrame, n_iterations: int = 1000, ci: float = 95.0) -> Dict[str, float]:
    """
    Implementa un remuestreo Bootstrap no paramétrico utilizando el generador
    de números pseudoaleatorios de NumPy para calcular intervalos de confianza
    al 95% para la satisfacción media de los pacientes.
    """
    rng = np.random.default_rng(seed=42)
    satisfactions = df["patient_satisfaction"].to_numpy(dtype=np.float64)
    n = len(satisfactions)

    # Remuestreo con reemplazo: matriz de shape (n_iterations, n)
    resamples = rng.choice(satisfactions, size=(n_iterations, n), replace=True)
    bootstrap_means = np.mean(resamples, axis=1)

    # Percentiles del intervalo de confianza
    lower_percentile = (100.0 - ci) / 2.0
    upper_percentile = 100.0 - lower_percentile

    ci_lower = np.percentile(bootstrap_means, lower_percentile)
    ci_upper = np.percentile(bootstrap_means, upper_percentile)
    mean_estimate = np.mean(bootstrap_means)

    return {
        "media_bootstrap": round(float(mean_estimate), 3),
        "ci_inferior_95": round(float(ci_lower), 3),
        "ci_superior_95": round(float(ci_upper), 3),
        "ancho_intervalo": round(float(ci_upper - ci_lower), 3),
    }
