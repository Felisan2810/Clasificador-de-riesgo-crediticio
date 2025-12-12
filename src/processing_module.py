#MODULO 2- Modulo de procesamiento 
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging
from colorama import Fore, Style

from fuzzy_system import FuzzyCreditRiskSystem
from ml_model import CreditRiskMLModel
from feature_engineering import FeatureEngineer
from config import MODEL_FILE, ENCODERS_FILE, TARGET_MAPPING, ML_FEATURES

logger = logging.getLogger(__name__)


class ProcessingModule:
    
    def __init__(self, modelo_path: str = None, encoders_path: str = None):
        self.fuzzy_system = None
        self.ml_model = None
        self.feature_engineer = None
        
    
        self._initialize_components(modelo_path, encoders_path)
        
    def _initialize_components(self, modelo_path: str = None, encoders_path: str = None):
 
        logger.info("Inicializando componentes del sistema hibrido...")
        

        try:
            self.fuzzy_system = FuzzyCreditRiskSystem()
            logger.info("Sistema difuso inicializado")
        except Exception as e:
            logger.error(f"Error al inicializar sistema difuso: {e}")
            raise
        
        try:
            self.feature_engineer = FeatureEngineer()
            if encoders_path and encoders_path.exists():
                self.feature_engineer.load_transformers(str(encoders_path))
                logger.info("Feature engineer cargado")
            else:
                logger.warning("Encoders no encontrados, se usaran valores por defecto")
        except Exception as e:
            logger.error(f"Error al cargar feature engineer: {e}")
            raise
        
        try:
            self.ml_model = CreditRiskMLModel()
            if modelo_path and modelo_path.exists():
                self.ml_model.load_model(str(modelo_path))
                logger.info("Modelo ML cargado")
            else:
                logger.warning("Modelo ML no encontrado")
                logger.warning("Por favor entrena el modelo con: python train_model.py")
        except Exception as e:
            logger.error(f"Error al cargar modelo ML: {e}")
            raise
    
    def preprocesar_entrada(self, datos: Dict) -> pd.DataFrame:

        df = pd.DataFrame([datos])
 
        if 'ratio_deuda_ingreso' not in df.columns:
            df['ratio_deuda_ingreso'] = df['monto'] / (df['SalarioNormalizado'] + 1e-5)
            df['ratio_deuda_ingreso'] = df['ratio_deuda_ingreso'].clip(0, 10)
        

        if 'MaxMontoInterno_normalizado' not in df.columns and 'MaxMontoInterno' in df.columns:
            df['MaxMontoInterno_normalizado'] = df['MaxMontoInterno'] / 50000.0 
            df['MaxMontoInterno_normalizado'] = df['MaxMontoInterno_normalizado'].clip(0, 1)
  
        if 'covid_intensity' not in df.columns:
            df['covid_intensity'] = 0.3  
        
        if 'temperatura_anomalia' not in df.columns:
            df['temperatura_anomalia'] = 0.0  
        
        return df
    
    def fase_sistema_difuso(self, df: pd.DataFrame) -> np.ndarray:
        logger.info("FASE 1: Evaluando con sistema difuso...")
        
        scores_difusos = []
        
        for idx, row in df.iterrows():
            inputs_difusos = {
                'ratio_deuda': row.get('ratio_deuda_ingreso', 0),
                'antiguedad': row.get('iAntiguedadBancarizado', 0),
                'score_sobreendeud': row.get('Score_Sobreendeudamiento', 500),
                'deuda_max': row.get('MaxMontoInterno_normalizado', 0),
                'covid': row.get('covid_intensity', 0)
            }
            
            score = self.fuzzy_system.evaluate(inputs_difusos)
            scores_difusos.append(score)
        
        logger.info(f"Sistema difuso evaluado. Score promedio: {np.mean(scores_difusos):.2f}/100")
        
        return np.array(scores_difusos)
    
    def fase_preparacion_ml(self, df: pd.DataFrame, scores_difusos: np.ndarray) -> pd.DataFrame:
        logger.info("FASE 2: Preparando features para ML...")
        
        df_features = df.copy()
        df_features['score_riesgo_difuso'] = scores_difusos
        
        try:
            df_features = self.feature_engineer.prepare_features(df_features, fit=False)
        except Exception:
            pass

        expected_cols = []
        try:
            if hasattr(self.feature_engineer, 'feature_names') and self.feature_engineer.feature_names:
                expected_cols = self.feature_engineer.feature_names
            else:
                expected_cols = ML_FEATURES
        except:
            expected_cols = ML_FEATURES

        from sklearn.preprocessing import LabelEncoder
        cols_texto = df_features.select_dtypes(include=['object']).columns
        for col in cols_texto:
            le = LabelEncoder()
            df_features[col] = df_features[col].fillna('DESCONOCIDO').astype(str)
            df_features[col] = le.fit_transform(df_features[col])

        df_final = pd.DataFrame(index=df_features.index)
        
        for col in expected_cols:
            if col in df_features.columns:
                df_final[col] = df_features[col]
        
            elif col.replace('_encoded', '') in df_features.columns:
                col_base = col.replace('_encoded', '')
                df_final[col] = df_features[col_base]
            

            else:
                df_final[col] = 0

        logger.info(f"Features alineadas: {len(df_final.columns)} variables listas para XGBoost")
        return df_final
    
    def fase_clasificacion_ml(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        logger.info("FASE 3: Clasificando con modelo ML...")
        
        if not self.ml_model.is_trained:
            logger.error("El modelo ML no esta entrenado")
            raise ValueError("Modelo ML no disponible. Ejecute: python train_model.py")
        
        predicciones = self.ml_model.predict(X)
        probabilidades = self.ml_model.predict_proba(X)
        
        logger.info("Clasificacion ML completada")
        
        return predicciones, probabilidades
    
    def procesar(self, datos: Dict) -> Dict:
        print("\n" + "="*60)
        print(Fore.CYAN + Style.BRIGHT + "PROCESAMIENTO HIBRIDO INICIADO")
        print("="*60 + "\n")
        
        try:
            # Preprocesar entrada
            df = self.preprocesar_entrada(datos)
            
            # FASE 1: Sistema Difuso
            scores_difusos = self.fase_sistema_difuso(df)
            score_difuso = scores_difusos[0]
            
            # FASE 2: Preparar features para ML
            X_ml = self.fase_preparacion_ml(df, scores_difusos)
            
            # FASE 3: Clasificación ML
            predicciones, probabilidades = self.fase_clasificacion_ml(X_ml)
            
            # Resultado crudo del ML
            prediccion_ml = predicciones[0]
            proba_ml = probabilidades[0]
            clase_ml = TARGET_MAPPING.get(prediccion_ml, f"CLASE_{prediccion_ml}")
            confianza_ml = proba_ml.max() * 100
            
           
            
            clase_final = clase_ml
            confianza_final = confianza_ml
            nota_decision = "Basada en Modelo ML"
            
           
            if score_difuso > 76:
                print(Fore.YELLOW + f"⚠️ ALERTA: Riesgo Difuso Crítico ({score_difuso:.2f}). Activando protocolo de rechazo.")
                if clase_ml == 'BAJO_RIESGO':
                    clase_final = 'ALTO_RIESGO'
                    confianza_final = max(confianza_ml, score_difuso)
                    nota_decision = "VETO POR RIESGO DIFUSO EXTREMO"
                    proba_ml = [0.95, 0.05] 

        
            elif 50 <= score_difuso <= 75:
                # Si el ML dice BAJO, pero el difuso está preocupado (Medio)
                if clase_ml == 'BAJO_RIESGO':
                    print(Fore.CYAN + f"ℹ️ AJUSTE: Cliente en zona gris (Difuso: {score_difuso:.2f}). Asignando Riesgo Medio.")
                    clase_final = 'MEDIO_RIESGO'
                    confianza_final = score_difuso # La confianza es el score difuso
                    nota_decision = "AJUSTE HÍBRIDO (ZONA GRIS)"
                    
                    # Simulamos probabilidades equilibradas para el gráfico
                    proba_ml = [0.40, 0.60] # Visualmente amarillo/intermedio
            
    
            
            # Construir resultado
            resultado = {
                'clase': clase_final,
                'prediccion_numerica': int(prediccion_ml),
                'probabilidades': {
                    TARGET_MAPPING.get(i, f"CLASE_{i}"): float(prob) * 100
                    for i, prob in enumerate(proba_ml)
                },
                'confianza': float(confianza_final),
                'score_difuso': float(score_difuso),
                'interpretacion_difusa': self.fuzzy_system.interpret_score(score_difuso),
                'datos_entrada': datos,
                'nota_decision': nota_decision # Agregamos esta nota para saber qué pasó
            }
            
            if nota_decision != "Basada en Modelo ML":
                print(Fore.RED + f" DECISIÓN FINAL MODIFICADA: {nota_decision}")
            
            print(Fore.GREEN + "\n PROCESAMIENTO COMPLETADO EXITOSAMENTE\n")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en procesamiento: {e}")
            print(Fore.RED + f"\n Error en procesamiento: {e}\n")
            raise
    
    def procesar_batch(self, df: pd.DataFrame) -> pd.DataFrame:
       
        logger.info(f"Procesando {len(df)} solicitudes en batch...")
        

        df_ml_ready_list = []
        scores_list = []
        
        # 1. Difuso
        for idx, row in df.iterrows():
             # Convertir fila a dict
             drow = row.to_dict()

             df_unit = self.preprocesar_entrada(drow)
             scores = self.fase_sistema_difuso(df_unit)
             scores_list.append(scores[0])
             
             # ML Prep
             x_ml = self.fase_preparacion_ml(df_unit, scores)
             df_ml_ready_list.append(x_ml)
             
        if df_ml_ready_list:
            X_batch = pd.concat(df_ml_ready_list, ignore_index=True)
            predicciones, probabilidades = self.fase_clasificacion_ml(X_batch)
            
            df['prediccion'] = [TARGET_MAPPING.get(p, f"CLASE_{p}") for p in predicciones]
            df['confianza'] = probabilidades.max(axis=1) * 100
            df['score_difuso'] = scores_list
        
        logger.info("Procesamiento batch completado")
        
        return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from config import MODEL_FILE, ENCODERS_FILE
    
    datos_prueba = {
        'monto': 15000.0,
        'PlazoReal': 24,
        'TasaEfectiva': 25.5,
        'EdadDesembolsoNormalizada': 35,
        'SalarioNormalizado': 3500.0,
        'Dependientes': 2,
        'EstadoCivil': 'CASADO',
        'Sexo': 1,
        'iAntiguedadBancarizado': 36,
        'MaxMontoInterno': 8000.0,
        'ScoreOriginacionMicro': 720,
        'Score_Sobreendeudamiento': 650,
        'Bal_TotalActivosNormalizado': 25000.0,
        'NetoIngresosNegocioNormalizado': 4200.0,
        'LiquidezDisponibleNormalizado': 3000.0,
        'SegmentoCartera': 2,
        'apoyogobierno': 0,
        'covid_intensity': 0.4,
        'temperatura_anomalia': 0.2
    }
    
    try:
        procesador = ProcessingModule(modelo_path=MODEL_FILE, encoders_path=ENCODERS_FILE)
        resultado = procesador.procesar(datos_prueba)
        print("\nResultado:")
        print(resultado)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nNota: Primero debes entrenar el modelo con: python train_model.py")