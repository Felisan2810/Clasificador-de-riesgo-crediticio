
import pandas as pd
import numpy as np
import logging
from typing import Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DataPreprocessor:
    
    def __init__(self):
        self.covid_stats = None
        self.temp_stats = None
        
    def preprocess_credito(self, df: pd.DataFrame) -> pd.DataFrame:
       
        logger.info("Preprocesando dataset de créditos...")
        df = df.copy()
        
        # 1. Eliminar duplicados
        initial_rows = len(df)
        df = df.drop_duplicates()
        logger.info(f"Duplicados eliminados: {initial_rows - len(df)}")
        
        # 2. Crear ratio deuda-ingreso
        df['ratio_deuda_ingreso'] = df['monto'] / (df['SalarioNormalizado'] + 1e-5)
        df['ratio_deuda_ingreso'] = df['ratio_deuda_ingreso'].clip(0, 10)  # Limitar valores extremos
        
        # 3. Normalizar MaxMontoInterno
        df['MaxMontoInterno_normalizado'] = (
            (df['MaxMontoInterno'] - df['MaxMontoInterno'].min()) / 
            (df['MaxMontoInterno'].max() - df['MaxMontoInterno'].min() + 1e-5)
        )
        
        # 4. Procesar fechas
        if 'fechaotorgamiento' in df.columns:
            df['fechaotorgamiento'] = pd.to_datetime(df['fechaotorgamiento'], errors='coerce')
            df['año_otorgamiento'] = df['fechaotorgamiento'].dt.year
            df['mes_otorgamiento'] = df['fechaotorgamiento'].dt.month
        
        # 5. Manejar valores faltantes en variables clave
        # Scores: rellenar con mediana
        for col in ['ScoreOriginacionMicro', 'Score_Sobreendeudamiento']:
            if col in df.columns:
                df[col].fillna(df[col].median(), inplace=True)
        
        # Antigüedad: rellenar con 0 (nuevos clientes)
        if 'iAntiguedadBancarizado' in df.columns:
            df['iAntiguedadBancarizado'].fillna(0, inplace=True)
        
        # Variables financieras: rellenar con 0
        financial_cols = [
            'Bal_TotalActivosNormalizado',
            'NetoIngresosNegocioNormalizado',
            'LiquidezDisponibleNormalizado'
        ]
        for col in financial_cols:
            if col in df.columns:
                df[col].fillna(0, inplace=True)
        
        # 6. Convertir EstadoCivil a categorías estándar
        if 'EstadoCivil' in df.columns:
            estado_civil_map = {
                'MARRIED': 'CASADO',
                'SINGLE': 'SOLTERO',
                'DIVORCED': 'DIVORCIADO',
                'COHABITING': 'CONVIVIENTE',
                'WIDOWED': 'VIUDO'
            }
            df['EstadoCivil'] = df['EstadoCivil'].map(estado_civil_map).fillna('OTRO')
        
        # 7. Limpiar variable objetivo
        if 'Class_202309FM' in df.columns:
            # Eliminar valores faltantes
            df = df.dropna(subset=['Class_202309FM'])
            # Eliminar valores anómalos (solo permitir 0 y 1)
            df = df[df['Class_202309FM'].isin([0, 1])]
            logger.info(f"Target limpiado. Registros válidos: {len(df):,}")
            logger.info(f"Distribución: {df['Class_202309FM'].value_counts().to_dict()}")
        
        logger.info(f"Dataset de créditos preprocesado: {len(df):,} filas")
        
        return df
    
    def aggregate_covid_data(self, df_covid: pd.DataFrame) -> pd.DataFrame:
       
        if df_covid.empty:
            logger.warning("No hay datos de COVID para agregar")
            return pd.DataFrame()
        
        logger.info("Agregando datos de COVID por departamento...")
        
        # Convertir fecha
        df_covid['FECHA_RESULTADO'] = pd.to_datetime(df_covid['FECHA_RESULTADO'], errors='coerce')
        
        # Extraer año-mes
        df_covid['año_mes'] = df_covid['FECHA_RESULTADO'].dt.to_period('M')
        
        # Agregar casos por departamento
        covid_agg = df_covid.groupby('DEPARTAMENTO').agg({
            'FECHA_RESULTADO': 'count'  # Contar casos totales
        }).reset_index()
        
        covid_agg.columns = ['DEPARTAMENTO', 'casos_covid_total']
        
        # Normalizar intensidad (0-1)
        max_casos = covid_agg['casos_covid_total'].max()
        covid_agg['covid_intensity'] = covid_agg['casos_covid_total'] / max_casos
        
        self.covid_stats = covid_agg
        
        logger.info(f"COVID agregado: {len(covid_agg)} departamentos")
        
        return covid_agg
    
    def aggregate_temperatura_data(self, df_temp: pd.DataFrame) -> pd.DataFrame:
      
        if df_temp.empty:
            logger.warning("No hay datos de temperatura para agregar")
            return pd.DataFrame()
        
        logger.info("Agregando datos de temperatura...")
        
        # Calcular promedio de anomalía por año-mes
        if 'AñoMes' in df_temp.columns and 'TempDiff' in df_temp.columns:
            temp_agg = df_temp.groupby('AñoMes').agg({
                'TempDiff': 'mean'
            }).reset_index()
            
            temp_agg.columns = ['año_mes', 'temperatura_anomalia']
            
            # Normalizar
            temp_agg['temperatura_anomalia'] = (
                temp_agg['temperatura_anomalia'] - temp_agg['temperatura_anomalia'].mean()
            ) / (temp_agg['temperatura_anomalia'].std() + 1e-5)
            
            self.temp_stats = temp_agg
            
            logger.info(f"Temperatura agregada: {len(temp_agg)} períodos")
            
            return temp_agg
        
        return pd.DataFrame()
    
    def integrate_external_factors(
        self,
        df_credito: pd.DataFrame,
        df_covid_agg: pd.DataFrame,
        df_temp_agg: pd.DataFrame
    ) -> pd.DataFrame:
        
        logger.info("Integrando factores externos...")
        df = df_credito.copy()
        
        # NOTA: Esta es una integración simplificada
        # En un caso real, necesitarías un mapeo de IdOficinaDesembolso -> Departamento
        
        # Por ahora, usar valores promedio como placeholder
        if not df_covid_agg.empty:
            covid_mean = df_covid_agg['covid_intensity'].mean()
            df['covid_intensity'] = covid_mean
            logger.info(f"COVID intensity promedio aplicada: {covid_mean:.4f}")
        else:
            df['covid_intensity'] = 0.0
            logger.warning("No hay datos de COVID - usando 0.0")
        
        if not df_temp_agg.empty:
            temp_mean = df_temp_agg['temperatura_anomalia'].mean()
            df['temperatura_anomalia'] = temp_mean
            logger.info(f"Temperatura anomalía promedio aplicada: {temp_mean:.4f}")
        else:
            df['temperatura_anomalia'] = 0.0
            logger.warning("No hay datos de temperatura - usando 0.0")
        
        logger.info("Integración de factores externos completada")
        
        return df
    
    def prepare_final_dataset(
        self,
        df_credito: pd.DataFrame,
        df_covid: pd.DataFrame,
        df_temp: pd.DataFrame
    ) -> pd.DataFrame:
      
        logger.info("\n" + "="*60)
        logger.info("INICIANDO PIPELINE DE PREPROCESAMIENTO")
        logger.info("="*60)
        
        # 1. Preprocesar créditos
        df = self.preprocess_credito(df_credito)
        
        # 2. Agregar datos externos
        df_covid_agg = self.aggregate_covid_data(df_covid)
        df_temp_agg = self.aggregate_temperatura_data(df_temp)
        
        # 3. Integrar factores externos
        df = self.integrate_external_factors(df, df_covid_agg, df_temp_agg)
        
        # 4. Resumen final
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DEL DATASET PREPROCESADO")
        logger.info("="*60)
        logger.info(f"Total de registros: {len(df):,}")
        logger.info(f"Total de variables: {len(df.columns)}")
        logger.info(f"Valores faltantes totales: {df.isnull().sum().sum():,}")
        logger.info("="*60 + "\n")
        
        return df


def preprocess_all_data(
    df_credito: pd.DataFrame,
    df_covid: pd.DataFrame,
    df_temp: pd.DataFrame
) -> pd.DataFrame:
   
    preprocessor = DataPreprocessor()
    return preprocessor.prepare_final_dataset(df_credito, df_covid, df_temp)


if __name__ == "__main__":
    # Prueba del preprocesador
    from data_loader import load_datasets
    
    print("Cargando datos de prueba...")
    df_credito, df_covid, df_temp = load_datasets(sample_size=5000)
    
    print("\nPreprocesando datos...")
    df_final = preprocess_all_data(df_credito, df_covid, df_temp)
    
    print("\nDataset final:")
    print(df_final.info())
    print("\nPrimeras filas:")
    print(df_final.head())