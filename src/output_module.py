#MODULO 3- Modulo de salida
import pandas as pd
from typing import Dict
import logging
from colorama import Fore, Style, init
from datetime import datetime
from config import COLORS, MESSAGES

init(autoreset=True)
logger = logging.getLogger(__name__)


class OutputModule:
    
    def __init__(self):
        self.ultimo_resultado = None
        
    def mostrar_resultado_detallado(self, resultado: Dict):
    
        self.ultimo_resultado = resultado
        
        clase = resultado['clase']
        confianza = resultado['confianza']
        score_difuso = resultado['score_difuso']
        probabilidades = resultado['probabilidades']
        
        if clase == 'BAJO_RIESGO':
            color = Fore.GREEN
            icono = "✅"
        elif clase == 'MEDIO_RIESGO':
            color = Fore.YELLOW
            icono = "⚠️"
        else:
            color = Fore.RED
            icono = "❌"
        
        print("\n" + "="*60)
        print(color + Style.BRIGHT + "     RESULTADO DE EVALUACIÓN DE RIESGO CREDITICIO")
        print("="*60 + "\n")
        
        print(f"{icono} {color + Style.BRIGHT}CLASIFICACIÓN: {clase}")
        print(f"   Confianza del modelo: {confianza:.1f}%")
        print(f"   Score Sistema Difuso: {score_difuso:.2f}/100")
        print(f"   Interpretación Difusa: {resultado['interpretacion_difusa']}")

        print(f"\n Nivel de Confianza:")
        self._mostrar_barra_progreso(confianza, 100, color)
        

        print(f"\n Desglose de Probabilidades:")
        for categoria, prob in probabilidades.items():
            color_cat = self._get_color_categoria(categoria)
            self._mostrar_barra_progreso(prob, 100, color_cat, label=categoria)
        
        print(f"\n Recomendación:")
        mensaje = MESSAGES.get(clase, "Requiere evaluación manual")
        print(f"   {mensaje}")
        
        # Factores clave
        print(f"\n Análisis de Factores Clave:")
        self._mostrar_factores_clave(resultado)
        
        # Timestamp
        print(f"\n Fecha de evaluación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "="*60 + "\n")
        
    def _mostrar_barra_progreso(self, valor: float, maximo: float, color: str, label: str = None):
       
        porcentaje = (valor / maximo) * 100
        barra_longitud = 40
        bloques_llenos = int((porcentaje / 100) * barra_longitud)
        barra = "█" * bloques_llenos + "░" * (barra_longitud - bloques_llenos)
        
        if label:
            print(f"   {label:20s} {color}[{barra}] {porcentaje:5.1f}%")
        else:
            print(f"   {color}[{barra}] {porcentaje:5.1f}%")
    
    def _get_color_categoria(self, categoria: str) -> str:

        if 'BAJO' in categoria:
            return Fore.GREEN
        elif 'MEDIO' in categoria:
            return Fore.YELLOW
        else:
            return Fore.RED
    
    def _mostrar_factores_clave(self, resultado: Dict):

        datos = resultado['datos_entrada']
        score_difuso = resultado['score_difuso']
        
        factores = []
        
        # Analizar ratio deuda-ingreso
        ratio = datos.get('monto', 0) / (datos.get('SalarioNormalizado', 1) + 1e-5)
        if ratio > 5:
            factores.append(("⚠️  Ratio deuda-ingreso alto", ratio, "NEGATIVO"))
        elif ratio < 2:
            factores.append(("✅ Ratio deuda-ingreso bajo", ratio, "POSITIVO"))
        
        # Analizar antigüedad
        antiguedad = datos.get('iAntiguedadBancarizado', 0)
        if antiguedad < 12:
            factores.append(("⚠️  Poca antigüedad en sistema financiero", antiguedad, "NEGATIVO"))
        elif antiguedad > 36:
            factores.append(("✅ Buena antigüedad en sistema financiero", antiguedad, "POSITIVO"))
        
        # Analizar score
        score = datos.get('ScoreOriginacionMicro', 0)
        if score < 500:
            factores.append(("⚠️  Score crediticio bajo", score, "NEGATIVO"))
        elif score > 700:
            factores.append(("✅ Buen score crediticio", score, "POSITIVO"))
        

        covid = datos.get('covid_intensity', 0)
        if covid > 0.6:
            factores.append(("⚠️  Alta exposición a COVID en región", covid, "NEGATIVO"))
        
    
        if factores:
            for factor, valor, tipo in factores[:5]:  # Top 5 factores
                color = Fore.GREEN if tipo == "POSITIVO" else Fore.YELLOW
                print(f"   {color}{factor}: {valor:.2f}")
        else:
            print("   Sin factores destacables")
    
    def mostrar_resultado_simple(self, resultado: Dict):
       
        clase = resultado['clase']
        confianza = resultado['confianza']
        
        if clase == 'BAJO_RIESGO':
            print(f"{Fore.GREEN}✅ BAJO RIESGO ({confianza:.1f}% confianza)")
        elif clase == 'MEDIO_RIESGO':
            print(f"{Fore.YELLOW}⚠️  MEDIO RIESGO ({confianza:.1f}% confianza)")
        else:
            print(f"{Fore.RED}❌ ALTO RIESGO ({confianza:.1f}% confianza)")
    
    def generar_reporte_pdf(self, resultado: Dict, ruta_salida: str = "reporte_riesgo.txt"):
       
        try:
            with open(ruta_salida, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("REPORTE DE EVALUACIÓN DE RIESGO CREDITICIO\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write(f"CLASIFICACIÓN: {resultado['clase']}\n")
                f.write(f"Confianza: {resultado['confianza']:.1f}%\n")
                f.write(f"Score Difuso: {resultado['score_difuso']:.2f}/100\n\n")
                
                f.write("PROBABILIDADES:\n")
                for cat, prob in resultado['probabilidades'].items():
                    f.write(f"  {cat}: {prob:.1f}%\n")
                
                f.write("\nRECOMENDACIÓN:\n")
                mensaje = MESSAGES.get(resultado['clase'], "Requiere evaluación manual")
                f.write(f"  {mensaje}\n")
                
                f.write("\n" + "="*60 + "\n")
            
            logger.info(f"Reporte generado: {ruta_salida}")
            print(Fore.GREEN + f"\n📄 Reporte guardado en: {ruta_salida}\n")
            
        except Exception as e:
            logger.error(f"Error al generar reporte: {e}")
            print(Fore.RED + f"\n❌ Error al generar reporte: {e}\n")
    
    def exportar_csv(self, resultados: list, ruta_salida: str = "resultados_evaluacion.csv"):
     
        try:
            df_resultados = pd.DataFrame([
                {
                    'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'clase': r['clase'],
                    'confianza': r['confianza'],
                    'score_difuso': r['score_difuso'],
                    'monto': r['datos_entrada'].get('monto'),
                    'ingreso': r['datos_entrada'].get('SalarioNormalizado'),
                    'score_crediticio': r['datos_entrada'].get('ScoreOriginacionMicro')
                }
                for r in resultados
            ])
            
            df_resultados.to_csv(ruta_salida, index=False)
            
            logger.info(f"Resultados exportados: {ruta_salida}")
            print(Fore.GREEN + f"\n Resultados exportados a: {ruta_salida}\n")
            
        except Exception as e:
            logger.error(f"Error al exportar CSV: {e}")
            print(Fore.RED + f"\n Error al exportar: {e}\n")
    
    def mostrar_estadisticas_batch(self, resultados: list):
       
        if not resultados:
            print(Fore.YELLOW + "\n  No hay resultados para mostrar\n")
            return
        
        df = pd.DataFrame(resultados)
        
        print("\n" + "="*60)
        print(Fore.CYAN + Style.BRIGHT + "ESTADÍSTICAS DE EVALUACIÓN BATCH")
        print("="*60 + "\n")
        
        print(f" Total de evaluaciones: {len(resultados)}")
        

        print(f"\n Distribución de riesgo:")
        for clase in ['BAJO_RIESGO', 'MEDIO_RIESGO', 'ALTO_RIESGO']:
            count = df['clase'].value_counts().get(clase, 0)
            porcentaje = (count / len(resultados)) * 100
            print(f"   {clase:15s}: {count:4d} ({porcentaje:5.1f}%)")

        print(f"\n Confianza promedio: {df['confianza'].mean():.1f}%")
        print(f"   Mínima: {df['confianza'].min():.1f}%")
        print(f"   Máxima: {df['confianza'].max():.1f}%")
        

        print(f"\n Score difuso promedio: {df['score_difuso'].mean():.2f}/100")
        
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    resultado_prueba = {
        'clase': 'BAJO_RIESGO',
        'prediccion_numerica': 1,
        'probabilidades': {
            'ALTO_RIESGO': 15.5,
            'BAJO_RIESGO': 84.5
        },
        'confianza': 84.5,
        'score_difuso': 32.8,
        'interpretacion_difusa': 'BAJO',
        'datos_entrada': {
            'monto': 15000.0,
            'SalarioNormalizado': 3500.0,
            'iAntiguedadBancarizado': 36,
            'ScoreOriginacionMicro': 720,
            'covid_intensity': 0.3
        }
    }
    
    output = OutputModule()
    output.mostrar_resultado_detallado(resultado_prueba)
    output.generar_reporte_pdf(resultado_prueba)