import sys
sys.path.append('src')

import logging
from colorama import Fore, Style, init
from pathlib import Path

from input_module import InputModule
from processing_module import ProcessingModule
from output_module import OutputModule
from feedback_module import FeedbackModule
from config import MODEL_FILE, ENCODERS_FILE

init(autoreset=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sistema.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SistemaRiesgoCrediticio:
    
    def __init__(self):
        self.modulo_entrada = None
        self.modulo_procesamiento = None
        self.modulo_salida = None
        self.modulo_feedback = None
        
        self._inicializar_modulos()
    
    def _inicializar_modulos(self):
        print("\n" + "="*70)
        print(Fore.CYAN + Style.BRIGHT + "   SISTEMA HÍBRIDO DIFUSO-NEURONAL DE CLASIFICACIÓN DE RIESGO")
        print("="*70)
        
        try:
            if not MODEL_FILE.exists():
                print(Fore.RED + "\n ERROR: Modelo no encontrado")
                print(Fore.YELLOW + "\nPrimero debes entrenar el modelo:")
                print("   python train_model.py\n")
                sys.exit(1)

            print(Fore.YELLOW + "\n Inicializando módulos del sistema...")
            
            self.modulo_entrada = InputModule()
            logger.info(" Módulo de Entrada inicializado")
            
            self.modulo_procesamiento = ProcessingModule(
                modelo_path=MODEL_FILE,
                encoders_path=ENCODERS_FILE
            )
            logger.info(" Módulo de Procesamiento inicializado")
            
            self.modulo_salida = OutputModule()
            logger.info(" Módulo de Salida inicializado")
            
            self.modulo_feedback = FeedbackModule()
            logger.info(" Módulo de Feedback inicializado")
            
            print(Fore.GREEN + " Sistema inicializado correctamente\n")
            
        except Exception as e:
            logger.error(f"Error al inicializar sistema: {e}")
            print(Fore.RED + f"\n❌ Error fatal: {e}\n")
            sys.exit(1)
    
    def mostrar_menu_principal(self):
        """Muestra el menú principal del sistema"""
        print("\n" + "="*70)
        print(Fore.CYAN + Style.BRIGHT + "MENÚ PRINCIPAL")
        print("="*70)
        print("\n Opciones disponibles:\n")
        print("  [1]  Evaluar nueva solicitud de crédito")
        print("  [2]  Evaluar múltiples solicitudes (batch)")
        print("  [3]  Registrar feedback de evaluación anterior")
        print("  [4]  Ver estadísticas de feedback")
        print("  [5]  Verificar necesidad de reentrenamiento")
        print("  [0]  Salir")
        print("\n" + "="*70)
    
    def evaluar_solicitud_individual(self):
        print("\n" + Fore.CYAN + Style.BRIGHT + "=== EVALUACIÓN DE SOLICITUD INDIVIDUAL ===\n")
        
        try:
            datos = self.modulo_entrada.ejecutar()
            
            if datos is None:
                print(Fore.YELLOW + "\nOperación cancelada\n")
                return None

            resultado = self.modulo_procesamiento.procesar(datos)

            self.modulo_salida.mostrar_resultado_detallado(resultado)
 
            generar_reporte = input("\n¿Desea generar un reporte? (s/n): ").lower()
            if generar_reporte == 's':
                self.modulo_salida.generar_reporte_pdf(resultado)

            capturar_feedback = input("\n¿Desea registrar el resultado real (feedback)? (s/n): ").lower()
            if capturar_feedback == 's':
                self.modulo_feedback.capturar_feedback_interactivo(resultado)
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en evaluación individual: {e}")
            print(Fore.RED + f"\n❌ Error: {e}\n")
            return None
    
    def evaluar_solicitudes_batch(self):
        print("\n" + Fore.CYAN + Style.BRIGHT + "=== EVALUACIÓN BATCH ===\n")
        
        try:
            ruta = input("Ruta del archivo CSV: ").strip()
            
            df = self.modulo_entrada.cargar_desde_csv(ruta)
            
            if df is None:
                return
            
            print(Fore.YELLOW + f"\n🔄 Procesando {len(df)} solicitudes...\n")
            

            df_resultados = self.modulo_procesamiento.procesar_batch(df)
        
            print(Fore.GREEN + "\n Procesamiento completado\n")
            
            resultados_lista = []
            for idx, row in df_resultados.iterrows():
                resultado = {
                    'clase': row['prediccion'],
                    'confianza': row['confianza'],
                    'score_difuso': row['score_difuso']
                }
                resultados_lista.append(resultado)
            
            # Mostrar estadísticas
            self.modulo_salida.mostrar_estadisticas_batch(resultados_lista)
            
            # Ofrecer exportar
            exportar = input("\n¿Desea exportar resultados a CSV? (s/n): ").lower()
            if exportar == 's':
                ruta_salida = input("Nombre del archivo de salida (default: resultados.csv): ").strip()
                if not ruta_salida:
                    ruta_salida = "resultados.csv"
                
                self.modulo_salida.exportar_csv(resultados_lista, ruta_salida)
            
        except Exception as e:
            logger.error(f"Error en evaluación batch: {e}")
            print(Fore.RED + f"\n❌ Error: {e}\n")
    
    def registrar_feedback_manual(self):
        print("\n" + Fore.CYAN + Style.BRIGHT + "=== REGISTRO DE FEEDBACK ===\n")
        
        print("Esta función permite registrar el resultado real de una")
        print("evaluación realizada anteriormente.\n")
        
        try:
            id_eval = input("ID de evaluación (dejar vacío para generar automático): ").strip()
            if not id_eval:
                from datetime import datetime
                id_eval = f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            print("\nPredicción del sistema:")
            print("  [1] BAJO_RIESGO")
            print("  [2] MEDIO_RIESGO")
            print("  [3] ALTO_RIESGO")
            pred_num = input("Seleccione: ").strip()
            
            print("\nResultado real:")
            print("  [1] BAJO_RIESGO")
            print("  [2] MEDIO_RIESGO")
            print("  [3] ALTO_RIESGO")
            real_num = input("Seleccione: ").strip()
            
            pred_map = {'1': 'BAJO_RIESGO', '2': 'MEDIO_RIESGO', '3': 'ALTO_RIESGO'}
            prediccion = pred_map.get(pred_num, 'BAJO_RIESGO')
            resultado_real = pred_map.get(real_num, 'BAJO_RIESGO')
            
            # Datos mínimos para el registro
            datos_eval = {
                'clase': prediccion,
                'confianza': 0,
                'score_difuso': 0,
                'datos_entrada': {}
            }
            
            self.modulo_feedback.registrar_feedback(
                id_evaluacion=id_eval,
                prediccion=prediccion,
                resultado_real=resultado_real,
                datos_evaluacion=datos_eval
            )
            
        except Exception as e:
            print(Fore.RED + f"\n❌ Error: {e}\n")
    
    def ver_estadisticas_feedback(self):
        self.modulo_feedback.mostrar_resumen_feedback()
        
        input("\nPresione Enter para continuar...")
    
    def verificar_reentrenamiento(self):

        print("\n" + Fore.CYAN + Style.BRIGHT + "=== VERIFICACIÓN DE REENTRENAMIENTO ===\n")
        
        necesita_reentrenar = self.modulo_feedback.sugerir_reentrenamiento()
        
        if necesita_reentrenar:
            reentrenar = input("\n¿Desea ejecutar el reentrenamiento ahora? (s/n): ").lower()
            if reentrenar == 's':
                print(Fore.YELLOW + "\n Ejecutando reentrenamiento...")
                print("   Comando: python train_model.py\n")
                # Aquí se podría llamar al script de entrenamiento
                print(Fore.YELLOW + "   Por favor ejecute manualmente: python train_model.py\n")
        
        input("\nPresione Enter para continuar...")
    
    def ejecutar(self):
        while True:
            try:
                self.mostrar_menu_principal()
                
                opcion = input("\nSeleccione una opción: ").strip()
                
                if opcion == '0':
                    print(Fore.CYAN + "\n👋 Gracias por usar el sistema. ¡Hasta pronto!\n")
                    break
                
                elif opcion == '1':
                    self.evaluar_solicitud_individual()
                
                elif opcion == '2':
                    self.evaluar_solicitudes_batch()
                
                elif opcion == '3':
                    self.registrar_feedback_manual()
                
                elif opcion == '4':
                    self.ver_estadisticas_feedback()
                
                elif opcion == '5':
                    self.verificar_reentrenamiento()
                
                else:
                    print(Fore.RED + "\n Opción inválida. Intente nuevamente.\n")
                
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n  Operación interrumpida por el usuario\n")
                confirmar = input("¿Desea salir del sistema? (s/n): ").lower()
                if confirmar == 's':
                    print(Fore.CYAN + "\n Hasta pronto!\n")
                    break
            
            except Exception as e:
                logger.error(f"Error en bucle principal: {e}")
                print(Fore.RED + f"\n❌ Error inesperado: {e}\n")
                print("El sistema continuará funcionando.\n")


def main():

    try:
        Path('logs').mkdir(exist_ok=True)
        sistema = SistemaRiesgoCrediticio()
        sistema.ejecutar()
        
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        print(Fore.RED + f"\n❌ Error fatal: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()