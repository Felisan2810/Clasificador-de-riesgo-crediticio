"""
Configuración global del sistema de clasificación de riesgo crediticio
"""
import os
from pathlib import Path

# ==================== RUTAS DEL PROYECTO ====================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Crear directorios si no existen
for directory in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==================== ARCHIVOS DE DATOS ====================
CREDITO_FILE = RAW_DATA_DIR / "dataset_credito1.csv"
COVID_FILE = RAW_DATA_DIR / "dataset_covid.csv"
TEMPERATURA_FILE = RAW_DATA_DIR / "dataset_temperatura.csv"
INTEGRATED_FILE = PROCESSED_DATA_DIR / "dataset_integrado.csv"

# ==================== ARCHIVOS DE MODELOS ====================
MODEL_FILE = MODELS_DIR / "modelo_xgboost.pkl"
SCALER_FILE = MODELS_DIR / "scaler.pkl"
ENCODERS_FILE = MODELS_DIR / "encoders.pkl"
FUZZY_RULES_FILE = MODELS_DIR / "fuzzy_rules.pkl"

# ==================== ARCHIVO DE FEEDBACK ====================
FEEDBACK_FILE = LOGS_DIR / "feedback_log.csv"

# ==================== COLUMNAS DEL DATASET PRINCIPAL ====================
# Columnas a cargar del dataset de crédito (reducir memoria)
COLUMNAS_CREDITO = [
    # Información del crédito
    'PlazoReal',
    'monto',
    'Saldo',
    'TasaEfectiva',
    'fechaotorgamiento',
    
    # Información del cliente
    'SalarioNormalizado',
    'EdadDesembolsoNormalizada',
    'EstadoCivil',
    'Sexo',
    'Dependientes',
    'NivelInstruccion',
    'Ocupacion',
    
    # Scores y evaluación de riesgo
    'MaxMontoInterno',
    'iAntiguedadBancarizado',
    'ScoreOriginacionMicro',
    'Score_Sobreendeudamiento',
    
    # Balance financiero
    'Bal_TotalActivosNormalizado',
    'NetoIngresosNegocioNormalizado',
    'LiquidezDisponibleNormalizado',
    
    # Características del producto
    'SegmentoCartera',
    'IdDestinoCredito',
    'apoyogobierno',
    
    # Ubicación (para merge con COVID)
    'IdOficinaDesembolso',
    
    # Variable objetivo (Target) - Último dato disponible Sep 2023
    'Class_202309FM'          # Clasificación binaria (0=mora >30, 1=al día)
  
]

# ==================== VARIABLES PARA SISTEMA DIFUSO ====================
FUZZY_VARIABLES = [
    'ratio_deuda_ingreso',
    'iAntiguedadBancarizado',
    'Score_Sobreendeudamiento',
    'MaxMontoInterno_normalizado',
    'covid_intensity'
]

# ==================== VARIABLES PARA ML ====================
ML_FEATURES = [
    # Score difuso (generado)
    'score_riesgo_difuso',
    
    # Variables numéricas
    'PlazoReal',
    'monto',
    'TasaEfectiva',
    'SalarioNormalizado',
    'EdadDesembolsoNormalizada',
    'Dependientes',
    'iAntiguedadBancarizado',
    'ScoreOriginacionMicro',
    'Score_Sobreendeudamiento',
    'MaxMontoInterno',
    'Bal_TotalActivosNormalizado',
    'NetoIngresosNegocioNormalizado',
    'LiquidezDisponibleNormalizado',
    
    # Variables categóricas (se codificarán)
    'EstadoCivil',
    'Sexo',
    'NivelInstruccion',
    'SegmentoCartera',
    
    # Factores externos
    'covid_intensity',
    'temperatura_anomalia'
]

# ==================== VARIABLE OBJETIVO ====================
TARGET_COLUMN = 'Class_202309FM'  # 0 = mora >30 días, 1 = al día

# Opción alternativa para clasificación triclase:
# TARGET_COLUMN = 'riesgo_categoria'  # Se creará en preprocessing
TARGET_MAPPING = {
    0: 'ALTO_RIESGO',    # Mora > 30 días
    1: 'BAJO_RIESGO'     # Al día
}

# Para clasificación triclase (basada en AtrasoMaximo_202309FM):
RIESGO_TRICLASE_THRESHOLDS = {
    'BAJO_RIESGO': (0, 15),      # 0-15 días de mora
    'MEDIO_RIESGO': (16, 60),    # 16-60 días
    'ALTO_RIESGO': (61, 9999)    # >60 días
}

# ==================== PARÁMETROS DEL SISTEMA DIFUSO ====================
FUZZY_PARAMS = {
    'ratio_deuda_ingreso': {
        'range': (0, 10),
        'terms': {
            'bajo': [0, 0, 2],
            'moderado': [1, 3, 5],
            'alto': [4, 6, 8],
            'critico': [7, 10, 10]
        }
    },
    'antiguedad': {
        'range': (0, 120),
        'terms': {
            'nuevo': [0, 0, 6],
            'regular': [3, 12, 24],
            'estable': [18, 36, 60],
            'veterano': [48, 120, 120]
        }
    },
    'score_sobreendeudamiento': {
        'range': (0, 1000),
        'terms': {
            'critico': [0, 0, 300],
            'riesgoso': [200, 400, 600],
            'aceptable': [500, 700, 850],
            'excelente': [800, 1000, 1000]
        }
    },
    'covid_intensity': {
        'range': (0, 1),
        'terms': {
            'sin_impacto': [0, 0, 0.2],
            'bajo': [0.1, 0.3, 0.5],
            'moderado': [0.4, 0.6, 0.8],
            'alto': [0.7, 1.0, 1.0]
        }
    }
}

# ==================== PARÁMETROS DEL MODELO ML ====================
ML_PARAMS = {
    'test_size': 0.2,
    'random_state': 42,
    'xgboost': {
        'n_estimators': 200,
        'max_depth': 7,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 3,
        'gamma': 0.1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'random_state': 42,
        'n_jobs': -1
    }
}

# ==================== CONFIGURACIÓN DE VISUALIZACIÓN ====================
COLORS = {
    'BAJO_RIESGO': '#28a745',     # Verde
    'MEDIO_RIESGO': '#ffc107',    # Amarillo
    'ALTO_RIESGO': '#dc3545'      # Rojo
}

# ==================== MENSAJES DEL SISTEMA ====================
MESSAGES = {
    'BAJO_RIESGO': "✅ APROBACIÓN RECOMENDADA - Cliente de bajo riesgo",
    'MEDIO_RIESGO': "⚠️ REQUIERE ANÁLISIS ADICIONAL - Considerar garantías o condiciones especiales",
    'ALTO_RIESGO': "❌ RECHAZO RECOMENDADO - Cliente de alto riesgo"
}

# ==================== CONFIGURACIÓN DE LOGGING ====================
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'INFO'