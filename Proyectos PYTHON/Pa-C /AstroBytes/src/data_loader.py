"""
Módulo de Carga, Validación e Ingeniería de Características
Proyecto: AstraMed - Samsung Innovation Campus (SIC)
"""

import os
import pandas as pd
from typing import Tuple, Optional


def load_telemedicine_data(filepath: str = "telemedicine_consultation_dataset.csv") -> pd.DataFrame:
    """
    Carga el conjunto de datos de consultas de telemedicina y valida la estructura.

    Args:
        filepath: Ruta relativa o absoluta hacia el archivo CSV.

    Returns:
        pd.DataFrame con los datos validados.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si faltan columnas requeridas en el dataset.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo de datos en: {filepath}")

    df = pd.read_csv(filepath)

    required_columns = [
        "consultation_id",
        "patient_age",
        "gender",
        "specialty",
        "consultation_mode",
        "symptom",
        "diagnosis",
        "duration_minutes",
        "prescription_given",
        "follow_up_required",
        "patient_satisfaction",
        "consultation_date",
    ]

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Faltan columnas obligatorias en el dataset: {missing_cols}")

    return df


def preprocess_and_engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Realiza limpieza de tipos de datos y generación de nuevas variables analíticas.

    Args:
        df: DataFrame original de telemedicina.

    Returns:
        DataFrame transformado con columnas enriquecidas para analítica y modelado.
    """
    data = df.copy()

    # Conversión de fecha y extracción temporal
    data["consultation_date"] = pd.to_datetime(data["consultation_date"])
    data["year_month"] = data["consultation_date"].dt.to_period("M").astype(str)
    data["month_name"] = data["consultation_date"].dt.month_name()
    data["quarter"] = data["consultation_date"].dt.to_period("Q").astype(str)

    # Rango etario estandarizado en salud
    bins_age = [0, 18, 35, 60, 120]
    labels_age = ["0-18 Pediátrico", "19-35 Joven Adulto", "36-60 Adulto", "60+ Adulto Mayor"]
    data["age_group"] = pd.cut(data["patient_age"], bins=bins_age, labels=labels_age, right=True)

    # Categorización de duración de consulta (minutos)
    bins_duration = [0, 15, 30, 45, 120]
    labels_duration = ["Corta (<15 min)", "Media (15-30 min)", "Estándar (31-45 min)", "Prolongada (>45 min)"]
    data["duration_group"] = pd.cut(data["duration_minutes"], bins=bins_duration, labels=labels_duration, right=True)

    # Nivel de satisfacción del paciente
    # Escala Likert de 1 a 5
    bins_satisfaction = [0, 2, 3, 5]
    labels_satisfaction = ["Baja (1-2)", "Neutra (3)", "Alta (4-5)"]
    data["satisfaction_category"] = pd.cut(data["patient_satisfaction"], bins=bins_satisfaction, labels=labels_satisfaction)

    # Banderas binarias útiles para analítica y machine learning
    data["is_high_satisfaction"] = (data["patient_satisfaction"] >= 4).astype(int)
    data["is_low_satisfaction"] = (data["patient_satisfaction"] <= 2).astype(int)
    data["follow_up_binary"] = (data["follow_up_required"] == "Yes").astype(int)
    data["prescription_binary"] = (data["prescription_given"] == "Yes").astype(int)

    # -------------------------------------------------------------------------
    # Reglas Clínicas de Triaje Inteligente: Concordancia Síntoma vs Especialidad
    # -------------------------------------------------------------------------
    # Mapeo clínico primario de síntoma -> especialidad recomendada
    primary_specialty_map = {
        "Skin Rash": "Dermatology",
        "Chest Pain": "Cardiology",
        "Anxiety": "Psychiatry",
        "Fever": "General Medicine",
        "Cough": "General Medicine",
        "Headache": "General Medicine",
    }

    def determine_expected_specialty(row):
        # En pacientes pediátricos (<=18 años), Pediatría es la especialidad preferente para síntomas generales
        if row["patient_age"] <= 18 and row["symptom"] in ["Fever", "Cough", "Headache"]:
            return "Pediatrics"
        return primary_specialty_map.get(row["symptom"], "General Medicine")

    data["expected_specialty"] = data.apply(determine_expected_specialty, axis=1)

    # Verificación de concordancia directa en el DataFrame
    data["is_specialty_concordant"] = (data["specialty"] == data["expected_specialty"]).astype(int)
    data["symptom_specialty_mismatch"] = (data["specialty"] != data["expected_specialty"]).astype(int)
    data["triage_derivation_status"] = data["is_specialty_concordant"].map({
        1: "Concordante",
        0: "Falla de Derivación"
    })

    return data


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Genera un resumen ejecutivo de la calidad y dimensiones del conjunto de datos.
    """
    return {
        "total_registros": len(df),
        "total_columnas": len(df.columns),
        "valores_nulos_totales": int(df.isnull().sum().sum()),
        "especialidades": df["specialty"].unique().tolist(),
        "modalidades": df["consultation_mode"].unique().tolist(),
        "rango_fechas": (str(df["consultation_date"].min()), str(df["consultation_date"].max())),
        "promedio_satisfaccion": round(float(df["patient_satisfaction"].mean()), 2),
        "promedio_duracion_min": round(float(df["duration_minutes"].mean()), 2),
    }
