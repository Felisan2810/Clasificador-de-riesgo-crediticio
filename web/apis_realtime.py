import requests
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from functools import lru_cache
from pathlib import Path
from io import StringIO
import random

# 1. Configurar el logger al inicio
logger = logging.getLogger(__name__)


DATA_PATH_BASE = Path(__file__).parent.parent / 'raw'
COVID_DATASET = DATA_PATH_BASE / 'dataset_covid.csv'
TEMP_DATASET = DATA_PATH_BASE / 'dataset_temperatura.csv'

try:
    from dotenv import load_dotenv
    dotenv_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=dotenv_path) 
    logger.info(f"✅ DOTENV: Variables de entorno cargadas.")
except ImportError:
    logger.warning("⚠️ DOTENV: Módulo python-dotenv no encontrado.")


CLASIFICACION_RIESGO_BASE = {
    'LIMA': 'ALTO_RIESGO', 'CALLAO': 'ALTO_RIESGO', 'AREQUIPA': 'MEDIO_RIESGO', 'LA LIBERTAD': 'MEDIO_RIESGO',
    'PIURA': 'MEDIO_RIESGO', 'CUSCO': 'BAJO_RIESGO', 'LAMBAYEQUE': 'MEDIO_RIESGO', 'JUNIN': 'BAJO_RIESGO',
    'PUNO': 'BAJO_RIESGO', 'LORETO': 'MEDIO_RIESGO', 'ANCASH': 'MEDIO_RIESGO', 'ICA': 'ALTO_RIESGO',
    'UCAYALI': 'MEDIO_RIESGO', 'SAN MARTIN': 'BAJO_RIESGO', 'CAJAMARCA': 'BAJO_RIESGO', 'HUANUCO': 'BAJO_RIESGO',
    'AYACUCHO': 'BAJO_RIESGO', 'TACNA': 'MEDIO_RIESGO', 'PASCO': 'BAJO_RIESGO', 'TUMBES': 'MEDIO_RIESGO',
    'APURIMAC': 'BAJO_RIESGO', 'MOQUEGUA': 'MEDIO_RIESGO', 'HUANCAVELICA': 'BAJO_RIESGO', 'AMAZONAS': 'BAJO_RIESGO',
    'MADRE DE DIOS': 'MEDIO_RIESGO'
}
# =========================================================================================

class MinisterioSaludAPI:
    
    DEPARTAMENTOS_MAP = CLASIFICACION_RIESGO_BASE.keys()

    @classmethod
    @lru_cache(maxsize=1, max_age=3600)
    def get_latest_data(cls) -> pd.DataFrame:
        """
        Lectura directa del CSV local 'dataset_covid.csv'
        """
        if COVID_DATASET.exists():
            try:
                # Lectura del archivo local
                df = pd.read_csv(COVID_DATASET)
                logger.info(f"✅ Datos COVID-19 cargados del local: {len(df):,} registros")
                return df
            except Exception as e:
                logger.error(f"❌ Error leyendo {COVID_DATASET}: {e}")
                return pd.DataFrame()
        else:
            logger.warning(f"⚠️ Archivo {COVID_DATASET.name} no encontrado. Usando simulación.")
            return pd.DataFrame() 

    @classmethod
    def get_covid_intensity_by_department(cls, departamento: str, fecha: Optional[datetime] = None) -> float:
        # Lógica para obtener intensidad real o simulada si falla el CSV
        
        df = cls.get_latest_data()
        dept_norm = departamento.upper().strip()

        if df.empty:
             return cls._get_simulated_intensity(dept_norm)
        
        # 🚨 Lógica de Conteo de Casos (asumiendo que la columna de departamento es la primera)
        try:
             # Asumimos que la columna 'location' o similar es la segunda columna, como en el CSV
             location_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
             
             # Filtrar datos (requiere una limpieza de nombres de departamento más sofisticada en un proyecto real)
             dept_data = df[df[location_col].astype(str).str.upper().str.contains(dept_norm, na=False)]
             
             if len(dept_data) == 0:
                 return cls._get_simulated_intensity(dept_norm)
             
             total_casos = len(dept_data)
             # Normalizar con el mismo umbral de 100,000 usado en el simulado
             intensity = min(total_casos / 100000, 1.0)
             logger.info(f"📊 COVID en {departamento}: {total_casos:,} registros reales → intensidad {intensity:.2f}")
             
             return intensity
             
        except Exception as e:
             logger.warning(f"⚠️ Error procesando CSV local para {departamento}: {e}. Usando simulación.")
             return cls._get_simulated_intensity(dept_norm)


    @classmethod
    # Mantenemos esta función para caer en ella si el CSV falla.
    def _get_simulated_intensity(cls, departamento: str) -> float:
        # ... (Mantener tu lógica de simulación de intensidad) ...
        intensities = {
            'LIMA': 0.85, 'CALLAO': 0.75, 'AREQUIPA': 0.45, 'LA LIBERTAD': 0.55, 'PIURA': 0.50,
            'CUSCO': 0.40, 'LAMBAYEQUE': 0.60, 'JUNIN': 0.35, 'PUNO': 0.30, 'LORETO': 0.30, 
            'ANCASH': 0.35, 'ICA': 0.40, 'UCAYALI': 0.38, 'SAN MARTIN': 0.32, 'CAJAMARCA': 0.28,
            'HUANUCO': 0.25, 'AYACUCHO': 0.22, 'TACNA': 0.35, 'PASCO': 0.20, 'TUMBES': 0.30,
            'APURIMAC': 0.18, 'MOQUEGUA': 0.25, 'HUANCAVELICA': 0.15, 'AMAZONAS': 0.18, 'MADRE DE DIOS': 0.20
        }
        return intensities.get(departamento, 0.3)

    @classmethod
    def get_all_departments_stats(cls) -> Dict[str, Dict]:
        """
        Calcula estadísticas reales agrupando el CSV local.
        """
        df = cls.get_latest_data()
        
        if df.empty:
            return cls._get_simulated_all_stats()
            
        # 🚨 Lógica de Agrupación de Casos (asumiendo que la columna de departamento es la segunda)
        try:
            # Columna 'DEPT_CODE' o la columna de ubicación real de tu CSV
            location_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            
            # Mapeo de nombres cortos a nombres estandarizados (p. ej., "LIMASUR" -> "LIMA")
            stats = df.groupby(location_col).size().to_dict()
            result = {}
            
            for location_raw, count in stats.items():
                location_upper = str(location_raw).upper().strip()
                
                # Intentamos mapear al departamento estándar (requiere lógica de limpieza)
                dept = next((d for d in cls.DEPARTAMENTOS_MAP if d in location_upper or location_upper in d), None)
                
                if dept and dept not in result:
                    intensity = min(count / 100000, 1.0)
                    result[dept] = {
                        'casos_totales': count,
                        'intensidad': intensity,
                        'impacto_riesgo': CLASIFICACION_RIESGO_BASE.get(dept, 'BAJO_RIESGO') 
                    }
            
            # Asegurar que todos los departamentos tengan datos (simulados si faltan)
            simulated = cls._get_simulated_all_stats()
            for dept in cls.DEPARTAMENTOS_MAP:
                if dept not in result:
                    result[dept] = simulated[dept]
            
            logger.info(f"📊 Estadísticas COVID: {len(result)} departamentos procesados.")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error al procesar datos agrupados de COVID: {e}. Usando simulación.")
            return cls._get_simulated_all_stats()


    @classmethod
    def _get_simulated_all_stats(cls) -> Dict[str, Dict]:
        """Estadísticas simuladas de COVID de fallback"""
        simulated_cases = {
            # ... (Tus casos simulados se mantienen) ...
            'LIMA': 950000, 'CALLAO': 180000, 'AREQUIPA': 120000, 'LA LIBERTAD': 140000, 'PIURA': 110000,
            'CUSCO': 95000, 'LAMBAYEQUE': 130000, 'JUNIN': 85000, 'PUNO': 70000, 'LORETO': 68000,
            'ANCASH': 75000, 'ICA': 82000, 'UCAYALI': 72000, 'SAN MARTIN': 65000, 'CAJAMARCA': 60000,
            'HUANUCO': 52000, 'AYACUCHO': 48000, 'TACNA': 55000, 'PASCO': 42000, 'TUMBES': 50000,
            'APURIMAC': 38000, 'MOQUEGUA': 45000, 'HUANCAVELICA': 32000, 'AMAZONAS': 35000, 'MADRE DE DIOS': 40000
        }
        
        result = {}
        for dept, cases in simulated_cases.items():
            result[dept] = {
                'casos_totales': cases,
                'intensidad': min(cases / 100000, 1.0),
                'impacto_riesgo': CLASIFICACION_RIESGO_BASE.get(dept, 'BAJO_RIESGO')
            }
        return result


class SenamhiAPI:
    """
    Integración usando datos de temperatura locales o simulación robusta.
    """
    
    # ... (COORDENADAS se mantienen) ...
    COORDENADAS = {
        'LIMA': (-12.0464, -77.0428), 'AREQUIPA': (-16.4090, -71.5375), 'CUSCO': (-13.5319, -71.9675),
        'PIURA': (-5.1945, -80.6328), 'LAMBAYEQUE': (-6.7011, -79.9061), 'LA LIBERTAD': (-8.1116, -79.0288),
        'JUNIN': (-12.0693, -75.2137), 'ICA': (-14.0678, -75.7286), 'PUNO': (-15.8402, -70.0219),
        'LORETO': (-3.7437, -73.2516), 'UCAYALI': (-8.3791, -74.5539), 'CALLAO': (-12.0553, -77.1009), 
        'ANCASH': (-9.5306, -77.5278), 'CAJAMARCA': (-7.1636, -78.513), 'TACNA': (-18.0061, -70.2464)
    }

    @classmethod
    def get_temperature_anomaly(cls, departamento: str) -> float:
        """
        Obtiene la anomalía basada en datos históricos locales (o simulación si falla).
        """
        try:
            if TEMP_DATASET.exists():
                df = pd.read_csv(TEMP_DATASET)
                # 🚨 Lógica de Extracción de Anomalía (asumiendo que la columna de anomalía es la última)
                anomalia_col = df.columns[-1]
                
                # Simplemente tomamos la última anomalía registrada para simular el tiempo real
                last_anomalia = df[anomalia_col].iloc[-1]
                
                logger.info(f"🌡️ Temp {departamento}: Usando anomalía local final ({last_anomalia:+.2f}°C)")
                return round(last_anomalia, 2)
                
            else:
                logger.warning(f"⚠️ Archivo {TEMP_DATASET.name} no encontrado. Usando simulación.")
                return cls._get_realistic_simulated_anomaly(departamento)
                
        except Exception as e:
            logger.error(f"❌ Error leyendo o procesando CSV de temperatura: {e}. Usando simulación.")
            return cls._get_realistic_simulated_anomaly(departamento)

    @classmethod
    def _get_historical_average(cls, departamento: str) -> float:
        # ... (Promedios se mantienen) ...
        promedios = {
            'LIMA': 19.0, 'AREQUIPA': 14.0, 'CUSCO': 11.5, 'PIURA': 24.0, 'LAMBAYEQUE': 22.0, 
            'LA LIBERTAD': 19.5, 'JUNIN': 11.0, 'ICA': 20.0, 'PUNO': 8.5, 'LORETO': 26.0, 
            'UCAYALI': 25.5, 'CALLAO': 20.0, 'ANCASH': 15.0, 'CAJAMARCA': 15.0, 'TACNA': 18.0
        }
        return promedios.get(departamento.upper(), 18.0)

    @classmethod
    def _get_realistic_simulated_anomaly(cls, departamento: str) -> float:
        # ... (Lógica de simulación se mantiene) ...
        dept_upper = departamento.upper()
        mes_actual = datetime.now().month
        
        base_anomalies = {
             'LIMA': 0.5, 'CALLAO': 0.5, 'AREQUIPA': 0.8, 'CUSCO': -0.3, 'PIURA': 1.2, 
             'LA LIBERTAD': 0.9, 'LAMBAYEQUE': 1.0, 'TUMBES': 1.3, 'LORETO': 1.1, 'UCAYALI': 1.0,
             'SAN MARTIN': 0.9, 'MADRE DE DIOS': 1.1, 'JUNIN': -0.2, 'PASCO': -0.4, 'HUANUCO': 0.2,
             'PUNO': -0.5, 'TACNA': 0.7, 'MOQUEGUA': 0.6, 'ICA': 0.8, 'ANCASH': 0.1, 
             'CAJAMARCA': 0.0, 'AYACUCHO': -0.1, 'HUANCAVELICA': -0.3, 'APURIMAC': -0.2, 'AMAZONAS': 0.4
         }
        
        base = base_anomalies.get(dept_upper, 0.3)
        if mes_actual in [12, 1, 2, 3]: seasonal = 0.5
        elif mes_actual in [6, 7, 8, 9]: seasonal = -0.4
        else: seasonal = 0.1
        
        random.seed(dept_upper + str(datetime.now().date()))
        variability = random.uniform(-0.3, 0.3)

        anomalia = base + seasonal + variability
        return round(max(-2.5, min(2.5, anomalia)), 2)
    
    @classmethod
    def get_temperature_map_data(cls) -> Dict[str, Dict]:
        """Obtener datos de temperatura para mapa"""
        result = {}
        departamentos_a_procesar = MinisterioSaludAPI.DEPARTAMENTOS_MAP
        
        for dept in departamentos_a_procesar:
            coords = cls.COORDENADAS.get(dept)
            anomalia = cls.get_temperature_anomaly(dept)
            temp_promedio = cls._get_historical_average(dept)
            
            result[dept] = {
                'coords': {'lat': coords[0], 'lon': coords[1]} if coords else None,
                'anomalia': anomalia,
                'temp_actual': round(temp_promedio + anomalia, 1),
                'temp_promedio': temp_promedio
            }
        return result


class GeolocalizacionService:
    """
    Servicio de geolocalización para oficinas bancarias
    """
    
    # Mapeo de oficinas a departamentos (expandir según sea necesario)
    OFICINAS_DEPARTAMENTOS = {
        1: 'LIMA',
        2: 'LIMA',
        3: 'AREQUIPA',
        4: 'CUSCO',
        5: 'PIURA',
        6: 'LA LIBERTAD',
        7: 'LAMBAYEQUE',
        8: 'JUNIN',
        9: 'CAJAMARCA',
        10: 'PUNO',
        11: 'ANCASH',
        12: 'ICA',
        13: 'LORETO',
        14: 'HUANUCO',
        15: 'UCAYALI',
        16: 'SAN MARTIN',
        17: 'TACNA',
        18: 'AYACUCHO',
        19: 'APURIMAC',
        20: 'MOQUEGUA',
        21: 'PASCO',
        22: 'TUMBES',
        23: 'HUANCAVELICA',
        24: 'AMAZONAS',
        25: 'MADRE DE DIOS',

    }
    
    @classmethod
    def get_departamento_from_oficina(cls, id_oficina: int) -> str:
        """
        Obtener departamento de una oficina
        """
        return cls.OFICINAS_DEPARTAMENTOS.get(id_oficina, 'LIMA')
    
    @classmethod
    def get_coords_from_oficina(cls, id_oficina: int) -> Tuple[float, float]:
        """
        Obtener coordenadas de una oficina
        """
        dept = cls.get_departamento_from_oficina(id_oficina)
        return SenamhiAPI.COORDENADAS.get(dept, (-12.0464, -77.0428))


# ==================== FUNCIÓN PRINCIPAL DE INTEGRACIÓN ====================

def get_realtime_external_factors(id_oficina: Optional[int] = None, 
                                  departamento: Optional[str] = None) -> Dict:
    """
    Obtener factores externos en tiempo real
    
    Args:
        id_oficina: ID de oficina de desembolso
        departamento: Nombre del departamento (alternativo)
    
    Returns:
        Dict con covid_intensity y temperatura_anomalia
    """
    try:
        # Determinar departamento
        if departamento:
            dept = departamento.upper()
        elif id_oficina:
            dept = GeolocalizacionService.get_departamento_from_oficina(id_oficina)
        else:
            dept = 'LIMA'  # Default
        
        logger.info(f"🌍 Obteniendo datos en tiempo real para {dept}...")
        
        # Obtener COVID
        covid_intensity = MinisterioSaludAPI.get_covid_intensity_by_department(dept)
        
        # Obtener Temperatura
        temp_anomalia = SenamhiAPI.get_temperature_anomaly(dept)
        
        return {
            'covid_intensity': covid_intensity,
            'temperatura_anomalia': temp_anomalia,
            'departamento': dept,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo factores externos: {e}")
        
        return {
            'covid_intensity': 0.3,
            'temperatura_anomalia': 0.0,
            'departamento': 'DESCONOCIDO',
            'timestamp': datetime.now().isoformat()
        }


# ==================== TESTING ====================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Probando integración con APIs externas...\n")
    
    # Test 1: COVID
    print("=" * 60)
    print("TEST 1: Datos COVID-19")
    print("=" * 60)
    
    intensity = MinisterioSaludAPI.get_covid_intensity_by_department('LIMA')
    print(f"Intensidad COVID en Lima: {intensity:.3f}\n")
    
    # Test 2: Temperatura
    print("=" * 60)
    print("TEST 2: Temperatura")
    print("=" * 60)
    
    anomalia = SenamhiAPI.get_temperature_anomaly('LIMA')
    print(f"Anomalía de temperatura en Lima: {anomalia:+.2f}°C\n")
    
    # Test 3: Integración completa
    print("=" * 60)
    print("TEST 3: Integración Completa")
    print("=" * 60)
    
    factores = get_realtime_external_factors(departamento='AREQUIPA')
    print(f"Factores externos para Arequipa:")
    print(f"  COVID: {factores['covid_intensity']:.3f}")
    print(f"  Temp: {factores['temperatura_anomalia']:+.2f}°C")
    print(f"  Timestamp: {factores['timestamp']}")