#MODULO 4- FEEBACK

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
import logging
from colorama import Fore, Style
from pathlib import Path
from config import FEEDBACK_FILE, MODEL_FILE, ENCODERS_FILE

logger = logging.getLogger(__name__)


class FeedbackModule:
    
    def __init__(self, feedback_file: Path = FEEDBACK_FILE):
        self.feedback_file = feedback_file
        self._initialize_feedback_log()
        
    def _initialize_feedback_log(self):
        if not self.feedback_file.exists():
            df_inicial = pd.DataFrame(columns=[
                'id_evaluacion',
                'fecha_evaluacion',
                'fecha_feedback',
                'prediccion_sistema',
                'resultado_real',
                'correcto',
                'monto',
                'score_difuso',
                'confianza',
                'datos_cliente'
            ])
            df_inicial.to_csv(self.feedback_file, index=False)
            logger.info(f"Archivo de feedback inicializado: {self.feedback_file}")
    
    def registrar_feedback(
        self,
        id_evaluacion: str,
        prediccion: str,
        resultado_real: str,
        datos_evaluacion: Dict
    ):
        
        try:
            # Verificar si la predicción fue correcta
            correcto = (prediccion == resultado_real)
            
            # Crear registro
            nuevo_registro = {
                'id_evaluacion': id_evaluacion,
                'fecha_evaluacion': datos_evaluacion.get('fecha_evaluacion', datetime.now()),
                'fecha_feedback': datetime.now(),
                'prediccion_sistema': prediccion,
                'resultado_real': resultado_real,
                'correcto': correcto,
                'monto': datos_evaluacion.get('datos_entrada', {}).get('monto', 0),
                'score_difuso': datos_evaluacion.get('score_difuso', 0),
                'confianza': datos_evaluacion.get('confianza', 0),
                'datos_cliente': str(datos_evaluacion.get('datos_entrada', {}))
            }
            
            # Cargar feedback existente
            df_feedback = pd.read_csv(self.feedback_file)
            
            # Agregar nuevo registro
            df_feedback = pd.concat([df_feedback, pd.DataFrame([nuevo_registro])], ignore_index=True)
            
            # Guardar
            df_feedback.to_csv(self.feedback_file, index=False)
            
            logger.info(f"Feedback registrado: ID={id_evaluacion}, Correcto={correcto}")
            
            if correcto:
                print(Fore.GREEN + f"\n✅ Feedback registrado: Predicción correcta\n")
            else:
                print(Fore.YELLOW + f"\n⚠️  Feedback registrado: Predicción incorrecta\n")
                print(f"   Sistema predijo: {prediccion}")
                print(f"   Resultado real: {resultado_real}\n")
            
        except Exception as e:
            logger.error(f"Error al registrar feedback: {e}")
            print(Fore.RED + f"\n❌ Error al registrar feedback: {e}\n")
    
    def capturar_feedback_interactivo(self, resultado_evaluacion: Dict) -> Optional[str]:
       
        print("\n" + "="*60)
        print(Fore.CYAN + Style.BRIGHT + "CAPTURA DE FEEDBACK")
        print("="*60 + "\n")
        
        prediccion = resultado_evaluacion['clase']
        
        print(f"El sistema predijo: {Fore.YELLOW}{prediccion}")
        print(f"\n¿Cuál fue el resultado real del cliente?")
        print("  [1] BAJO_RIESGO (pagó correctamente)")
        print("  [2] MEDIO_RIESGO (algunos retrasos)")
        print("  [3] ALTO_RIESGO (incurrió en mora >30 días)")
        print("  [0] Cancelar\n")
        
        try:
            opcion = input("Seleccione una opción: ").strip()
            
            resultado_map = {
                '1': 'BAJO_RIESGO',
                '2': 'MEDIO_RIESGO',
                '3': 'ALTO_RIESGO'
            }
            
            if opcion == '0':
                print(Fore.YELLOW + "\nFeedback cancelado\n")
                return None
            
            resultado_real = resultado_map.get(opcion)
            
            if resultado_real:
                # Generar ID único
                id_evaluacion = f"EVAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Agregar fecha de evaluación
                resultado_evaluacion['fecha_evaluacion'] = datetime.now()
                
                # Registrar feedback
                self.registrar_feedback(
                    id_evaluacion=id_evaluacion,
                    prediccion=prediccion,
                    resultado_real=resultado_real,
                    datos_evaluacion=resultado_evaluacion
                )
                
                return resultado_real
            else:
                print(Fore.RED + "\n❌ Opción inválida\n")
                return None
                
        except KeyboardInterrupt:
            print(Fore.YELLOW + "\n\nFeedback cancelado\n")
            return None
        except Exception as e:
            print(Fore.RED + f"\n❌ Error: {e}\n")
            return None
    
    def obtener_metricas_feedback(self) -> Dict:
        
        try:
            df_feedback = pd.read_csv(self.feedback_file)
            
            if len(df_feedback) == 0:
                return {'total': 0, 'mensaje': 'No hay feedback registrado'}
            
            total = len(df_feedback)
            correctos = df_feedback['correcto'].sum()
            accuracy_real = (correctos / total) * 100
            
            # Distribución por clase
            distribucion = df_feedback['resultado_real'].value_counts().to_dict()
            
            # Matriz de confusión simplificada
            confusion = pd.crosstab(
                df_feedback['prediccion_sistema'],
                df_feedback['resultado_real'],
                margins=True
            )
            
            metricas = {
                'total': total,
                'correctos': correctos,
                'incorrectos': total - correctos,
                'accuracy_real': accuracy_real,
                'distribucion_real': distribucion,
                'confusion_matrix': confusion
            }
            
            return metricas
            
        except Exception as e:
            logger.error(f"Error al calcular métricas: {e}")
            return {'error': str(e)}
    
    def mostrar_resumen_feedback(self):
        metricas = self.obtener_metricas_feedback()
        
        if 'error' in metricas:
            print(Fore.RED + f"\n❌ Error al obtener métricas: {metricas['error']}\n")
            return
        
        if metricas.get('total', 0) == 0:
            print(Fore.YELLOW + "\n⚠️  No hay feedback registrado aún\n")
            return
        
        print("\n" + "="*60)
        print(Fore.CYAN + Style.BRIGHT + "RESUMEN DE FEEDBACK ACUMULADO")
        print("="*60 + "\n")
        
        print(f"📊 Total de evaluaciones con feedback: {metricas['total']}")
        print(f"✅ Predicciones correctas: {metricas['correctos']} ({metricas['accuracy_real']:.1f}%)")
        print(f"❌ Predicciones incorrectas: {metricas['incorrectos']}")
        
        print(f"\n🎯 Distribución de resultados reales:")
        for clase, count in metricas['distribucion_real'].items():
            porcentaje = (count / metricas['total']) * 100
            print(f"   {clase:15s}: {count:3d} ({porcentaje:5.1f}%)")
        
        print(f"\n📋 Matriz de Confusión:")
        print(metricas['confusion_matrix'])
        
        print("\n" + "="*60 + "\n")
    
    def sugerir_reentrenamiento(self) -> bool:
        
        metricas = self.obtener_metricas_feedback()
        
        if metricas.get('total', 0) < 50:
            print(Fore.YELLOW + "\n⚠️  Feedback insuficiente para reentrenamiento (mínimo 50 casos)\n")
            return False
        
        accuracy = metricas.get('accuracy_real', 100)
        
        if accuracy < 75:
            print(Fore.RED + f"\n🔄 REENTRENAMIENTO SUGERIDO")
            print(f"   Accuracy actual con feedback real: {accuracy:.1f}%")
            print(f"   Se recomienda reentrenar el modelo con los datos actualizados\n")
            return True
        else:
            print(Fore.GREEN + f"\n✅ Modelo funcionando bien (Accuracy: {accuracy:.1f}%)")
            print(f"   No es necesario reentrenar por el momento\n")
            return False
    
    def preparar_datos_reentrenamiento(self) -> Optional[pd.DataFrame]:
        try:
            df_feedback = pd.read_csv(self.feedback_file)
            
            if len(df_feedback) < 50:
                logger.warning("Datos insuficientes para reentrenamiento")
                return None
            
            logger.info(f"Datos preparados: {len(df_feedback)} registros")
            return df_feedback
            
        except Exception as e:
            logger.error(f"Error al preparar datos: {e}")
            return None
    
    def exportar_feedback(self, ruta_salida: str = "feedback_export.csv"):
        
        try:
            df_feedback = pd.read_csv(self.feedback_file)
            df_feedback.to_csv(ruta_salida, index=False)
            
            logger.info(f"Feedback exportado: {ruta_salida}")
            print(Fore.GREEN + f"\n📤 Feedback exportado a: {ruta_salida}\n")
            
        except Exception as e:
            logger.error(f"Error al exportar feedback: {e}")
            print(Fore.RED + f"\n❌ Error al exportar: {e}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    feedback_mod = FeedbackModule()

    resultado_prueba = {
        'clase': 'BAJO_RIESGO',
        'confianza': 85.0,
        'score_difuso': 30.0,
        'datos_entrada': {
            'monto': 15000.0,
            'SalarioNormalizado': 3500.0
        }
    }
    
    feedback_mod.registrar_feedback(
        id_evaluacion="TEST_001",
        prediccion="BAJO_RIESGO",
        resultado_real="BAJO_RIESGO",
        datos_evaluacion=resultado_prueba
    )
    
    feedback_mod.mostrar_resumen_feedback()
    

    feedback_mod.sugerir_reentrenamiento()