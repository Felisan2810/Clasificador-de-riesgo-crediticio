#MODULO 1- Modulo de entrada
import pandas as pd
from typing import Dict, Optional
import logging
from colorama import Fore, Style, init

init(autoreset=True)

logger = logging.getLogger(__name__)


class InputModule:
    
    def __init__(self):
        self.datos_capturados = None
        
    def mostrar_menu(self):
        print("\n" + "="*60)
        print(Fore.CYAN + Style.BRIGHT + "  SISTEMA DE CLASIFICACIÓN DE RIESGO CREDITICIO")
        print("="*60)
        print("\n MÓDULO DE ENTRADA DE DATOS\n")
        print("Seleccione una opción:")
        print("  [1] Ingresar solicitud individual")
        print("  [2] Cargar múltiples solicitudes desde CSV")
        print("  [3] Usar datos de ejemplo")
        print("  [0] Salir")
        print("\n" + "="*60)
        
    def capturar_solicitud_individual(self) -> Dict:
       
        print("\n" + Fore.GREEN + "=== CAPTURA DE SOLICITUD INDIVIDUAL ===\n")
        
        datos = {}
        
        try:
          
            print(Fore.YELLOW + "📋 INFORMACIÓN DEL CRÉDITO:")
            datos['monto'] = float(input("  Monto solicitado (S/.): "))
            datos['PlazoReal'] = int(input("  Plazo en meses: "))
            datos['TasaEfectiva'] = float(input("  Tasa efectiva anual (%): "))
            
    
            print(Fore.YELLOW + "\n👤 INFORMACIÓN DEL CLIENTE:")
            datos['EdadDesembolsoNormalizada'] = int(input("  Edad: "))
            datos['SalarioNormalizado'] = float(input("  Ingreso mensual (S/.): "))
            datos['Dependientes'] = int(input("  Número de dependientes: "))
            
            print(Fore.YELLOW + "\n  Nivel de Instrucción:")
            print("    [1] Sin Instrucción / Primaria Incompleta")
            print("    [2] Primaria Completa")
            print("    [3] Secundaria Incompleta")
            print("    [4] Secundaria Completa")
            print("    [5] Superior Técnica Incompleta")
            print("    [6] Superior Técnica Completa")
            print("    [7] Universitaria Incompleta")
            print("    [8] Universitaria Completa / Postgrado")
            
            try:
                nivel_input = int(input("  Seleccione nivel (1-8): "))
                # Validamos que esté en el rango correcto
                if 1 <= nivel_input <= 8:
                    datos['NivelInstruccion'] = nivel_input
                else:
                    print(Fore.RED + "  Opción fuera de rango. Se asumirá 4 (Secundaria).")
                    datos['NivelInstruccion'] = 4
            except ValueError:
                print(Fore.RED + "  Entrada inválida. Se asumirá 4 (Secundaria).")
                datos['NivelInstruccion'] = 4
                
            print("\n  Estado Civil:")
            print("    [1] Soltero  [2] Casado  [3] Divorciado  [4] Viudo  [5] Conviviente")
            estado_civil_map = {1: 'SOLTERO', 2: 'CASADO', 3: 'DIVORCIADO', 4: 'VIUDO', 5: 'CONVIVIENTE'}
            estado_civil_num = int(input("  Seleccione (1-5): "))
            datos['EstadoCivil'] = estado_civil_map.get(estado_civil_num, 'SOLTERO')
            
            print("\n  Sexo:")
            print("    [1] Masculino  [2] Femenino")
            datos['Sexo'] = int(input("  Seleccione (1-2): "))
            
            # Historial financiero
            print(Fore.YELLOW + "\n HISTORIAL FINANCIERO:")
            datos['iAntiguedadBancarizado'] = int(input("  Antigüedad en sistema financiero (meses): "))
            datos['MaxMontoInterno'] = float(input("  Deuda máxima anterior (S/.): "))
            datos['ScoreOriginacionMicro'] = int(input("  Score crediticio (0-1000): "))
            datos['Score_Sobreendeudamiento'] = int(input("  Score sobreendeudamiento (0-1000): "))
            
            # Balance financiero
            print(Fore.YELLOW + "\n BALANCE FINANCIERO:")
            datos['Bal_TotalActivosNormalizado'] = float(input("  Valor total de activos (S/.): "))
            datos['NetoIngresosNegocioNormalizado'] = float(input("  Ingresos netos del negocio (S/.): "))
            datos['LiquidezDisponibleNormalizado'] = float(input("  Liquidez disponible (S/.): "))
            
            # Información adicional
            print(Fore.YELLOW + "\n INFORMACIÓN ADICIONAL:")
            datos['SegmentoCartera'] = int(input("  Segmento de cartera (1-5): "))
            datos['apoyogobierno'] = int(input("  ¿Tiene apoyo de programa gubernamental? (0=No, 1=Sí): "))
            
            # Factores externos (valores por defecto o estimados)
            datos['covid_intensity'] = float(input("  Intensidad COVID en región (0-1): ") or "0.3")
            datos['temperatura_anomalia'] = float(input("  Anomalía de temperatura (-3 a 3): ") or "0")
            
            self.datos_capturados = datos
            
            print(Fore.GREEN + "\n Datos capturados exitosamente\n")
            
            return datos
            
        except ValueError as e:
            print(Fore.RED + f"\n Error: Entrada inválida. {e}")
            logger.error(f"Error en captura de datos: {e}")
            return None
        except Exception as e:
            print(Fore.RED + f"\n Error inesperado: {e}")
            logger.error(f"Error inesperado en captura: {e}")
            return None
    
    def cargar_desde_csv(self, ruta: str) -> pd.DataFrame:
        
        try:
            df = pd.read_csv(ruta)
            logger.info(f"Archivo CSV cargado: {len(df)} solicitudes")
            print(Fore.GREEN + f"\n Cargadas {len(df)} solicitudes desde CSV\n")
            return df
        except FileNotFoundError:
            print(Fore.RED + f"\n Error: Archivo no encontrado: {ruta}\n")
            logger.error(f"Archivo CSV no encontrado: {ruta}")
            return None
        except Exception as e:
            print(Fore.RED + f"\n Error al cargar CSV: {e}\n")
            logger.error(f"Error al cargar CSV: {e}")
            return None
    
    def generar_datos_ejemplo(self) -> Dict:
        datos_ejemplo = {
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
        
        print(Fore.CYAN + "\n Usando datos de ejemplo:")
        print(f"  Cliente: {datos_ejemplo['EdadDesembolsoNormalizada']} años, "
              f"{datos_ejemplo['EstadoCivil']}, {datos_ejemplo['Dependientes']} dependientes")
        print(f"  Monto: S/. {datos_ejemplo['monto']:,.2f}")
        print(f"  Plazo: {datos_ejemplo['PlazoReal']} meses")
        print(f"  Ingreso: S/. {datos_ejemplo['SalarioNormalizado']:,.2f}")
        print(f"  Score: {datos_ejemplo['ScoreOriginacionMicro']}")
        print()
        
        self.datos_capturados = datos_ejemplo
        return datos_ejemplo
    
    def validar_datos(self, datos: Dict) -> bool:
        validaciones = {
            'monto': lambda x: x > 0,
            'PlazoReal': lambda x: 1 <= x <= 360,
            'EdadDesembolsoNormalizada': lambda x: 18 <= x <= 100,
            'SalarioNormalizado': lambda x: x >= 0,
            'ScoreOriginacionMicro': lambda x: 0 <= x <= 1000,
            'Score_Sobreendeudamiento': lambda x: 0 <= x <= 1000
        }
        
        errores = []
        for campo, validacion in validaciones.items():
            if campo in datos:
                if not validacion(datos[campo]):
                    errores.append(f"{campo}: valor fuera de rango")
        
        if errores:
            print(Fore.RED + "\n  Errores de validación:")
            for error in errores:
                print(f"  - {error}")
            return False
        
        return True
    
    def mostrar_resumen(self, datos: Dict):
     
        print("\n" + "="*60)
        print(Fore.CYAN + "RESUMEN DE DATOS CAPTURADOS")
        print("="*60)
        
        print(f"\n💰 Crédito Solicitado:")
        print(f"   Monto: S/. {datos.get('monto', 0):,.2f}")
        print(f"   Plazo: {datos.get('PlazoReal', 0)} meses")
        print(f"   Tasa: {datos.get('TasaEfectiva', 0):.2f}%")
        
        print(f"\n👤 Cliente:")
        print(f"   Edad: {datos.get('EdadDesembolsoNormalizada', 0)} años")
        print(f"   Estado Civil: {datos.get('EstadoCivil', 'N/A')}")
        print(f"   Ingreso: S/. {datos.get('SalarioNormalizado', 0):,.2f}")
        print(f"   Dependientes: {datos.get('Dependientes', 0)}")
        
        print(f"\n📊 Historial:")
        print(f"   Antigüedad: {datos.get('iAntiguedadBancarizado', 0)} meses")
        print(f"   Score: {datos.get('ScoreOriginacionMicro', 0)}")
        
        print("\n" + "="*60)
    
    def ejecutar(self) -> Optional[Dict]:
        while True:
            self.mostrar_menu()
            
            try:
                opcion = input("\nSeleccione una opción: ").strip()
                
                if opcion == '0':
                    print(Fore.YELLOW + "\n👋 Saliendo del sistema...\n")
                    return None
                
                elif opcion == '1':
                    datos = self.capturar_solicitud_individual()
                    if datos and self.validar_datos(datos):
                        self.mostrar_resumen(datos)
                        confirmar = input("\n¿Proceder con estos datos? (s/n): ").lower()
                        if confirmar == 's':
                            return datos
                
                elif opcion == '2':
                    ruta = input("\nRuta del archivo CSV: ").strip()
                    df = self.cargar_desde_csv(ruta)
                    if df is not None:
                        return df
                
                elif opcion == '3':
                    datos = self.generar_datos_ejemplo()
                    self.mostrar_resumen(datos)
                    confirmar = input("\n¿Proceder con datos de ejemplo? (s/n): ").lower()
                    if confirmar == 's':
                        return datos
                
                else:
                    print(Fore.RED + "\n Opción inválida. Intente nuevamente.\n")
                    
            except KeyboardInterrupt:
                print(Fore.YELLOW + "\n\n Operación cancelada por el usuario.\n")
                return None
            except Exception as e:
                print(Fore.RED + f"\n Error: {e}\n")
                logger.error(f"Error en módulo de entrada: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    modulo_entrada = InputModule()
    resultado = modulo_entrada.ejecutar()
    
    if resultado:
        print("\n✅ Datos listos para procesamiento")
    else:
        print("\n❌ No se capturaron datos")