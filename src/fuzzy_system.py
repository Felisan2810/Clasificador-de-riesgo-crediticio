import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import logging
import pandas as pd
from typing import Dict, Any
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class FuzzyCreditRiskSystem:
  
    
    def __init__(self):
        self.sistema = None
        self.simulacion = None
        self._build_system()
        
    def _build_system(self):
        logger.info("Construyendo sistema de inferencia difuso...")
        
        # VARIABLES DE ENTRADA 
        
        # 1. Ratio Deuda-Ingreso
        self.ratio_deuda = ctrl.Antecedent(np.arange(0, 10.1, 0.1), 'ratio_deuda')
        self.ratio_deuda['bajo'] = fuzz.trimf(self.ratio_deuda.universe, [0, 0, 2])
        self.ratio_deuda['moderado'] = fuzz.trimf(self.ratio_deuda.universe, [1, 3, 5])
        self.ratio_deuda['alto'] = fuzz.trimf(self.ratio_deuda.universe, [4, 6, 8])
        self.ratio_deuda['critico'] = fuzz.trimf(self.ratio_deuda.universe, [7, 10, 10])
        
        # 2. Antigüedad Bancarizada (en meses)
        self.antiguedad = ctrl.Antecedent(np.arange(0, 121, 1), 'antiguedad')
        self.antiguedad['nuevo'] = fuzz.trimf(self.antiguedad.universe, [0, 0, 6])
        self.antiguedad['regular'] = fuzz.trimf(self.antiguedad.universe, [3, 12, 24])
        self.antiguedad['estable'] = fuzz.trimf(self.antiguedad.universe, [18, 36, 60])
        self.antiguedad['veterano'] = fuzz.trimf(self.antiguedad.universe, [48, 120, 120])
        
        # 3. Score de Sobreendeudamiento
        self.score_sobreendeud = ctrl.Antecedent(np.arange(0, 1001, 1), 'score_sobreendeud')
        self.score_sobreendeud['critico'] = fuzz.trimf(self.score_sobreendeud.universe, [0, 0, 300])
        self.score_sobreendeud['riesgoso'] = fuzz.trimf(self.score_sobreendeud.universe, [200, 400, 600])
        self.score_sobreendeud['aceptable'] = fuzz.trimf(self.score_sobreendeud.universe, [500, 700, 850])
        self.score_sobreendeud['excelente'] = fuzz.trimf(self.score_sobreendeud.universe, [800, 1000, 1000])
        
        # 4. Deuda Máxima Normalizada
        self.deuda_max = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'deuda_max')
        self.deuda_max['baja'] = fuzz.trimf(self.deuda_max.universe, [0, 0, 0.3])
        self.deuda_max['media'] = fuzz.trimf(self.deuda_max.universe, [0.2, 0.5, 0.7])
        self.deuda_max['alta'] = fuzz.trimf(self.deuda_max.universe, [0.6, 1.0, 1.0])
        
        # 5. Intensidad COVID (0-1)
        self.covid = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'covid')
        self.covid['sin_impacto'] = fuzz.trimf(self.covid.universe, [0, 0, 0.2])
        self.covid['bajo'] = fuzz.trimf(self.covid.universe, [0.1, 0.3, 0.5])
        self.covid['moderado'] = fuzz.trimf(self.covid.universe, [0.4, 0.6, 0.8])
        self.covid['alto'] = fuzz.trimf(self.covid.universe, [0.7, 1.0, 1.0])
        
        # ============== DEFINIR VARIABLE DE SALIDA ==============
        self.riesgo_difuso = ctrl.Consequent(np.arange(0, 101, 1), 'riesgo_difuso')
        self.riesgo_difuso['muy_bajo'] = fuzz.trimf(self.riesgo_difuso.universe, [0, 0, 25])
        self.riesgo_difuso['bajo'] = fuzz.trimf(self.riesgo_difuso.universe, [15, 35, 50])
        self.riesgo_difuso['medio'] = fuzz.trimf(self.riesgo_difuso.universe, [40, 55, 70])
        self.riesgo_difuso['alto'] = fuzz.trimf(self.riesgo_difuso.universe, [60, 75, 90])
        self.riesgo_difuso['muy_alto'] = fuzz.trimf(self.riesgo_difuso.universe, [85, 100, 100])
        
        # REGLAS DIFUSAS 
        reglas = self._create_rules()
        
        #  SISTEMA DE CONTROL 
        self.sistema = ctrl.ControlSystem(reglas)
        self.simulacion = ctrl.ControlSystemSimulation(self.sistema)
        
        logger.info(f"Sistema difuso construido con {len(reglas)} reglas")
        
    def _create_rules(self):
       
        reglas = []
        
        # REGLAS DE ALTO RIESGO
        reglas.append(
            ctrl.Rule(
                self.ratio_deuda['critico'] & self.antiguedad['nuevo'],
                self.riesgo_difuso['muy_alto']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.score_sobreendeud['critico'] & self.deuda_max['alta'],
                self.riesgo_difuso['muy_alto']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.ratio_deuda['alto'] & self.score_sobreendeud['riesgoso'],
                self.riesgo_difuso['alto']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.covid['alto'] & self.ratio_deuda['alto'],
                self.riesgo_difuso['alto']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.antiguedad['nuevo'] & self.deuda_max['alta'],
                self.riesgo_difuso['alto']
            )
        )
        
        # REGLAS DE RIESGO MEDIO
        reglas.append(
            ctrl.Rule(
                self.ratio_deuda['moderado'] & self.antiguedad['regular'],
                self.riesgo_difuso['medio']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.score_sobreendeud['riesgoso'] & self.covid['moderado'],
                self.riesgo_difuso['medio']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.deuda_max['media'] & self.ratio_deuda['moderado'],
                self.riesgo_difuso['medio']
            )
        )
        
        # REGLAS DE BAJO RIESGO
        reglas.append(
            ctrl.Rule(
                self.ratio_deuda['bajo'] & self.antiguedad['estable'],
                self.riesgo_difuso['bajo']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.score_sobreendeud['excelente'] & self.deuda_max['baja'],
                self.riesgo_difuso['muy_bajo']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.antiguedad['veterano'] & self.score_sobreendeud['aceptable'],
                self.riesgo_difuso['bajo']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.ratio_deuda['bajo'] & self.covid['sin_impacto'],
                self.riesgo_difuso['muy_bajo']
            )
        )
        
        # REGLAS COMBINADAS COMPLEJAS
        reglas.append(
            ctrl.Rule(
                self.ratio_deuda['moderado'] & self.antiguedad['estable'] & self.score_sobreendeud['aceptable'],
                self.riesgo_difuso['bajo']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.ratio_deuda['alto'] & self.antiguedad['veterano'] & self.score_sobreendeud['excelente'],
                self.riesgo_difuso['medio']
            )
        )
        
        reglas.append(
            ctrl.Rule(
                self.covid['alto'] & self.antiguedad['nuevo'] & self.ratio_deuda['moderado'],
                self.riesgo_difuso['alto']
            )
        )
        
        return reglas
    
    def evaluate(self, inputs: Dict[str, float]) -> float:
       
        try:

            self.simulacion.input['ratio_deuda'] = np.clip(inputs.get('ratio_deuda', 0), 0, 10)
            self.simulacion.input['antiguedad'] = np.clip(inputs.get('antiguedad', 0), 0, 120)
            self.simulacion.input['score_sobreendeud'] = np.clip(inputs.get('score_sobreendeud', 500), 0, 1000)
            self.simulacion.input['deuda_max'] = np.clip(inputs.get('deuda_max', 0), 0, 1)
            self.simulacion.input['covid'] = np.clip(inputs.get('covid', 0), 0, 1)
            
        
            self.simulacion.compute()
            
            return self.simulacion.output['riesgo_difuso']
            
        except Exception as e:
            logger.warning(f"Error en evaluación difusa: {e}")
            return 50.0
    
    def evaluate_batch(self, df: pd.DataFrame) -> np.ndarray:
        
        logger.info(f"Evaluando sistema difuso para {len(df):,} registros...")
        
        scores = []
        for idx, row in df.iterrows():
            inputs = {
                'ratio_deuda': row.get('ratio_deuda_ingreso', 0),
                'antiguedad': row.get('iAntiguedadBancarizado', 0),
                'score_sobreendeud': row.get('Score_Sobreendeudamiento', 500),
                'deuda_max': row.get('MaxMontoInterno_normalizado', 0),
                'covid': row.get('covid_intensity', 0)
            }
            
            score = self.evaluate(inputs)
            scores.append(score)
            
            if (idx + 1) % 1000 == 0:
                logger.info(f"Procesados: {idx + 1:,} registros")
        
        logger.info("Evaluación difusa completada")
        
        return np.array(scores)
    
    def interpret_score(self, score: float) -> str:
       
        if score < 25:
            return "MUY_BAJO"
        elif score < 45:
            return "BAJO"
        elif score < 65:
            return "MEDIO"
        elif score < 85:
            return "ALTO"
        else:
            return "MUY_ALTO"


if __name__ == "__main__":
    # Prueba del sistema difuso
    print("Inicializando sistema difuso...")
    fuzzy_system = FuzzyCreditRiskSystem()
    
    # Casos de prueba
    casos_prueba = [
        {
            'nombre': 'Cliente de Bajo Riesgo',
            'inputs': {
                'ratio_deuda': 1.5,
                'antiguedad': 48,
                'score_sobreendeud': 850,
                'deuda_max': 0.2,
                'covid': 0.1
            }
        },
        {
            'nombre': 'Cliente de Riesgo Medio',
            'inputs': {
                'ratio_deuda': 4.0,
                'antiguedad': 18,
                'score_sobreendeud': 550,
                'deuda_max': 0.5,
                'covid': 0.4
            }
        },
        {
            'nombre': 'Cliente de Alto Riesgo',
            'inputs': {
                'ratio_deuda': 8.0,
                'antiguedad': 2,
                'score_sobreendeud': 250,
                'deuda_max': 0.9,
                'covid': 0.8
            }
        }
    ]
    
    print("EVALUACIÓN DE CASOS DE PRUEBA")

    
    for caso in casos_prueba:
        score = fuzzy_system.evaluate(caso['inputs'])
        categoria = fuzzy_system.interpret_score(score)
        
        print(f"\n{caso['nombre']}:")
        print(f"  Score Difuso: {score:.2f}/100")
        print(f"  Categoría: {categoria}")