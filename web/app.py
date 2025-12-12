"""
Backend FastAPI para Sistema de Riesgo Crediticio
Wrapper sobre el código existente sin modificarlo
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import sys
import os
import pandas as pd
import json
from pathlib import Path
import logging

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

# Importar módulos existentes (SIN MODIFICARLOS)
from processing_module import ProcessingModule
from ml_model import CreditRiskMLModel
from fuzzy_system import FuzzyCreditRiskSystem
from feedback_module import FeedbackModule
from config import MODEL_FILE, ENCODERS_FILE, FEEDBACK_FILE

# NUEVO: Importar APIs en tiempo real
try:
    from apis_realtime import (
        get_realtime_external_factors,
        MinisterioSaludAPI,
        SenamhiAPI,
        GeolocalizacionService
    )
    REALTIME_ENABLED = True
except ImportError:
    REALTIME_ENABLED = False
    logging.warning("⚠️ APIs en tiempo real no disponibles")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear app FastAPI
app = FastAPI(
    title="Sistema Híbrido de Riesgo Crediticio",
    description="API para clasificación de riesgo con lógica difusa y ML",
    version="1.0.0"
)

# CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# ==================== MODELOS PYDANTIC ====================

class SolicitudCredito(BaseModel):
    monto: float
    PlazoReal: int
    TasaEfectiva: float
    EdadDesembolsoNormalizada: int
    SalarioNormalizado: float
    Dependientes: int
    NivelInstruccion: int = 4
    EstadoCivil: str
    Sexo: int
    iAntiguedadBancarizado: int
    MaxMontoInterno: float
    ScoreOriginacionMicro: int
    Score_Sobreendeudamiento: int
    Bal_TotalActivosNormalizado: float
    NetoIngresosNegocioNormalizado: float
    LiquidezDisponibleNormalizado: float
    SegmentoCartera: int
    apoyogobierno: int
    covid_intensity: float = 0.3
    temperatura_anomalia: float = 0.0

class FeedbackRequest(BaseModel):
    id_evaluacion: str
    prediccion: str
    resultado_real: str
    datos_evaluacion: Dict

# ==================== ESTADO GLOBAL ====================

class AppState:
    def __init__(self):
        self.procesador = None
        self.fuzzy_system = None
        self.feedback_module = None
        self.modelo_entrenado = False
        
    def initialize(self):
        """Inicializar componentes si el modelo existe"""
        try:
            if MODEL_FILE.exists():
                self.procesador = ProcessingModule(
                    modelo_path=MODEL_FILE,
                    encoders_path=ENCODERS_FILE
                )
                self.fuzzy_system = FuzzyCreditRiskSystem()
                self.feedback_module = FeedbackModule()
                self.modelo_entrenado = True
                logger.info("✅ Sistema inicializado correctamente")
            else:
                logger.warning("⚠️ Modelo no encontrado. Debe entrenarse primero.")
                self.modelo_entrenado = False
        except Exception as e:
            logger.error(f"❌ Error al inicializar: {e}")
            self.modelo_entrenado = False

state = AppState()

# ==================== RUTAS ====================

@app.on_event("startup")
async def startup_event():
    """Ejecutar al inicio"""
    state.initialize()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Servir página principal"""
    html_file = Path("web/static/index.html")
    if html_file.exists():
        return html_file.read_text(encoding='utf-8')
    return "<h1>Sistema de Riesgo Crediticio</h1><p>Archivo index.html no encontrado</p>"

@app.get("/api/health")
async def health_check():
    """Verificar estado del sistema"""
    return {
        "status": "ok",
        "modelo_entrenado": state.modelo_entrenado,
        "modelo_path": str(MODEL_FILE),
        "modelo_exists": MODEL_FILE.exists()
    }

@app.post("/api/predict")
async def predict(solicitud: SolicitudCredito):
    """Predicción con sistema híbrido (difuso + ML)"""
    if not state.modelo_entrenado:
        raise HTTPException(
            status_code=400,
            detail="Modelo no entrenado. Use /api/train primero."
        )
    
    try:
        # Convertir a diccionario
        datos = solicitud.dict()
        
        # Procesar con sistema híbrido
        resultado = state.procesador.procesar(datos)
        
        return {
            "success": True,
            "resultado": resultado
        }
        
    except Exception as e:
        logger.error(f"Error en predicción: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict-only-ml")
async def predict_only_ml(solicitud: SolicitudCredito):
    """Predicción SOLO con ML (sin lógica difusa)"""
    if not state.modelo_entrenado:
        raise HTTPException(
            status_code=400,
            detail="Modelo no entrenado. Use /api/train primero."
        )
    
    try:
        datos = solicitud.dict()
        
        # Preparar datos sin score difuso
        df = state.procesador.preprocesar_entrada(datos)
        df['score_riesgo_difuso'] = 50.0  # Valor neutral
        
        # Solo ML
        X_ml = state.procesador.fase_preparacion_ml(df, [50.0])
        predicciones, probabilidades = state.procesador.fase_clasificacion_ml(X_ml)
        
        from config import TARGET_MAPPING
        
        resultado = {
            "clase": TARGET_MAPPING.get(predicciones[0], f"CLASE_{predicciones[0]}"),
            "prediccion_numerica": int(predicciones[0]),
            "probabilidades": {
                TARGET_MAPPING.get(i, f"CLASE_{i}"): float(prob) * 100
                for i, prob in enumerate(probabilidades[0])
            },
            "confianza": float(probabilidades[0].max() * 100),
            "score_difuso": 50.0,
            "interpretacion_difusa": "NO APLICADO",
            "datos_entrada": datos
        }
        
        return {
            "success": True,
            "resultado": resultado
        }
        
    except Exception as e:
        logger.error(f"Error en predicción ML: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict-only-fuzzy")
async def predict_only_fuzzy(solicitud: SolicitudCredito):
    """Predicción SOLO con lógica difusa"""
    try:
        datos = solicitud.dict()
        
        # Calcular score difuso
        df = state.procesador.preprocesar_entrada(datos)
        score_difuso = state.fuzzy_system.evaluate({
            'ratio_deuda': df['ratio_deuda_ingreso'].iloc[0],
            'antiguedad': datos.get('iAntiguedadBancarizado', 0),
            'score_sobreendeud': datos.get('Score_Sobreendeudamiento', 500),
            'deuda_max': df.get('MaxMontoInterno_normalizado', [0]).iloc[0],
            'covid': datos.get('covid_intensity', 0)
        })
        
        # Clasificar basado solo en score difuso
        if score_difuso < 35:
            clase = "BAJO_RIESGO"
        elif score_difuso < 65:
            clase = "MEDIO_RIESGO"
        else:
            clase = "ALTO_RIESGO"
        
        # Calcular confianza basada en qué tan lejos está de los límites
        if score_difuso < 35:
            confianza = 100 - (score_difuso / 35 * 20)  # 80-100% confianza
        elif score_difuso < 65:
            confianza = 70  # Zona gris, menor confianza
        else:
            confianza = 80 + ((score_difuso - 65) / 35 * 20)  # 80-100% confianza
        
        resultado = {
            "clase": clase,
            "score_difuso": float(score_difuso),
            "interpretacion_difusa": state.fuzzy_system.interpret_score(score_difuso),
            "confianza": float(confianza),
            "probabilidades": {
                "BAJO_RIESGO": float(100 - score_difuso) if score_difuso < 50 else 0,
                "MEDIO_RIESGO": float(100 - abs(50 - score_difuso) * 2) if 30 < score_difuso < 70 else 0,
                "ALTO_RIESGO": float(score_difuso) if score_difuso > 50 else 0
            },
            "datos_entrada": datos
        }
        
        return {
            "success": True,
            "resultado": resultado
        }
        
    except Exception as e:
        logger.error(f"Error en predicción difusa: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def register_feedback(feedback: FeedbackRequest):
    """Registrar feedback de una evaluación"""
    try:
        state.feedback_module.registrar_feedback(
            id_evaluacion=feedback.id_evaluacion,
            prediccion=feedback.prediccion,
            resultado_real=feedback.resultado_real,
            datos_evaluacion=feedback.datos_evaluacion
        )
        
        return {"success": True, "message": "Feedback registrado"}
        
    except Exception as e:
        logger.error(f"Error al registrar feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feedback/stats")
async def get_feedback_stats():
    """Obtener estadísticas de feedback"""
    try:
        metricas = state.feedback_module.obtener_metricas_feedback()
        
        # Convertir confusion matrix a formato JSON
        if 'confusion_matrix' in metricas:
            metricas['confusion_matrix'] = metricas['confusion_matrix'].to_dict()
        
        return {
            "success": True,
            "metricas": metricas
        }
        
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model/info")
async def get_model_info():
    """Obtener información del modelo"""
    if not state.modelo_entrenado:
        return {
            "entrenado": False,
            "mensaje": "Modelo no entrenado"
        }
    
    try:
        # Cargar métricas del modelo
        import joblib
        model_data = joblib.load(MODEL_FILE)
        
        return {
            "entrenado": True,
            "metricas": model_data.get('training_metrics', {}),
            "features": len(model_data.get('feature_importance', [])),
            "fecha_entrenamiento": str(MODEL_FILE.stat().st_mtime)
        }
        
    except Exception as e:
        return {
            "entrenado": True,
            "error": str(e)
        }

@app.post("/api/train/start")
async def start_training():
    """
    Iniciar entrenamiento del modelo
    NOTA: En producción, esto debería ser un job en background
    """
    try:
        # Aquí normalmente llamarías a train_model.py
        # Por ahora retornamos instrucciones
        
        return {
            "success": False,
            "message": "Entrenamiento debe ejecutarse manualmente",
            "instrucciones": "Ejecutar: python train_model.py",
            "nota": "En producción, esto sería un job asíncrono"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/model/delete")
async def delete_model():
    """Eliminar modelo entrenado"""
    try:
        if MODEL_FILE.exists():
            MODEL_FILE.unlink()
            logger.info("Modelo eliminado")
            
        if ENCODERS_FILE.exists():
            ENCODERS_FILE.unlink()
            logger.info("Encoders eliminados")
        
        state.modelo_entrenado = False
        state.procesador = None
        
        return {
            "success": True,
            "message": "Modelo eliminado correctamente"
        }
        
    except Exception as e:
        logger.error(f"Error al eliminar modelo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/examples")
async def get_examples():
    """Obtener casos de ejemplo"""
    ejemplos = [
        {
            "nombre": "Cliente de Bajo Riesgo",
            "datos": {
                "monto": 15000.0,
                "PlazoReal": 24,
                "TasaEfectiva": 25.5,
                "EdadDesembolsoNormalizada": 35,
                "SalarioNormalizado": 3500.0,
                "Dependientes": 2,
                "NivelInstruccion": 6,
                "EstadoCivil": "CASADO",
                "Sexo": 1,
                "iAntiguedadBancarizado": 36,
                "MaxMontoInterno": 8000.0,
                "ScoreOriginacionMicro": 720,
                "Score_Sobreendeudamiento": 650,
                "Bal_TotalActivosNormalizado": 25000.0,
                "NetoIngresosNegocioNormalizado": 4200.0,
                "LiquidezDisponibleNormalizado": 3000.0,
                "SegmentoCartera": 2,
                "apoyogobierno": 0,
                "covid_intensity": 0.3,
                "temperatura_anomalia": 0.2
            }
        },
        {
            "nombre": "Cliente de Alto Riesgo",
            "datos": {
                "monto": 25000.0,
                "PlazoReal": 12,
                "TasaEfectiva": 35.0,
                "EdadDesembolsoNormalizada": 22,
                "SalarioNormalizado": 1500.0,
                "Dependientes": 3,
                "NivelInstruccion": 3,
                "EstadoCivil": "SOLTERO",
                "Sexo": 1,
                "iAntiguedadBancarizado": 3,
                "MaxMontoInterno": 20000.0,
                "ScoreOriginacionMicro": 380,
                "Score_Sobreendeudamiento": 250,
                "Bal_TotalActivosNormalizado": 5000.0,
                "NetoIngresosNegocioNormalizado": 1200.0,
                "LiquidezDisponibleNormalizado": 500.0,
                "SegmentoCartera": 4,
                "apoyogobierno": 0,
                "covid_intensity": 0.7,
                "temperatura_anomalia": 0.5
            }
        }
    ]
    
    return {"success": True, "ejemplos": ejemplos}

# ==================== ENDPOINTS DE DATOS EN TIEMPO REAL ====================

@app.get("/api/realtime/covid/{departamento}")
async def get_covid_realtime(departamento: str):
    """Obtener datos COVID en tiempo real para un departamento"""
    if not REALTIME_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="APIs en tiempo real no disponibles"
        )
    
    try:
        intensity = MinisterioSaludAPI.get_covid_intensity_by_department(departamento)
        
        return {
            "success": True,
            "departamento": departamento,
            "covid_intensity": intensity,
            "descripcion": "Intensidad normalizada (0-1) basada en casos totales"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/temperatura/{departamento}")
async def get_temperatura_realtime(departamento: str):
    """Obtener temperatura en tiempo real para un departamento"""
    if not REALTIME_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="APIs en tiempo real no disponibles"
        )
    
    try:
        anomalia = SenamhiAPI.get_temperature_anomaly(departamento)
        
        return {
            "success": True,
            "departamento": departamento,
            "temperatura_anomalia": anomalia,
            "descripcion": "Anomalía en °C respecto al promedio histórico"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/factores")
async def get_factores_externos(departamento: Optional[str] = None):
    """Obtener todos los factores externos en tiempo real"""
    if not REALTIME_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="APIs en tiempo real no disponibles"
        )
    
    try:
        factores = get_realtime_external_factors(departamento=departamento)
        
        return {
            "success": True,
            "factores": factores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/realtime/mapa-covid")
async def get_mapa_covid():
    """Obtener datos para mapa de COVID por departamentos"""
    if not REALTIME_ENABLED:
        return {
            "success": False,
            "message": "APIs en tiempo real no disponibles"
        }
    
    try:
        stats = MinisterioSaludAPI.get_all_departments_stats()
        
        return {
            "success": True,
            "departamentos": stats
        }
    except Exception as e:
        logger.error(f"Error en mapa COVID: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/api/realtime/mapa-temperatura")
async def get_mapa_temperatura():
    """Obtener datos para mapa de temperatura por departamentos"""
    if not REALTIME_ENABLED:
        return {
            "success": False,
            "message": "APIs en tiempo real no disponibles"
        }
    
    try:
        temps = SenamhiAPI.get_temperature_map_data()
        
        return {
            "success": True,
            "departamentos": temps
        }
    except Exception as e:
        logger.error(f"Error en mapa temperatura: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/api/predict-realtime")
async def predict_with_realtime_data(solicitud: SolicitudCredito, departamento: Optional[str] = None):
    """
    Predicción utilizando datos externos en TIEMPO REAL
    """
    if not state.modelo_entrenado:
        raise HTTPException(
            status_code=400,
            detail="Modelo no entrenado. Use /api/train primero."
        )
    
    try:
        # Obtener factores externos en tiempo real
        if REALTIME_ENABLED and departamento:
            factores = get_realtime_external_factors(departamento=departamento)
            
            # Sobreescribir datos estáticos con datos en tiempo real
            datos = solicitud.dict()
            datos['covid_intensity'] = factores['covid_intensity']
            datos['temperatura_anomalia'] = factores['temperatura_anomalia']
            
            logger.info(f"📡 Usando datos en tiempo real: COVID={factores['covid_intensity']:.3f}, Temp={factores['temperatura_anomalia']:+.2f}°C")
        else:
            datos = solicitud.dict()
        
        # Procesar con sistema híbrido
        resultado = state.procesador.procesar(datos)
        
        # Agregar metadata de fuente de datos
        resultado['fuente_datos'] = 'TIEMPO_REAL' if REALTIME_ENABLED and departamento else 'ESTATICOS'
        if REALTIME_ENABLED and departamento:
            resultado['factores_externos_realtime'] = factores
        
        return {
            "success": True,
            "resultado": resultado
        }
        
    except Exception as e:
        logger.error(f"Error en predicción tiempo real: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== EJECUTAR ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)