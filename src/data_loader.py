import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging
from config import (
    CREDITO_FILE, COVID_FILE, TEMPERATURA_FILE,
    COLUMNAS_CREDITO, RAW_DATA_DIR
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataLoader:
    
    def __init__(self, sample_size: Optional[int] = None):
    
        self.sample_size = sample_size
        
    def load_credito_data(self) -> pd.DataFrame:

        logger.info("Cargando dataset de créditos...")
        
        if not CREDITO_FILE.exists():
            raise FileNotFoundError(
                f"Dataset de créditos no encontrado en: {CREDITO_FILE}\n"
                f"Por favor coloca el archivo en: {RAW_DATA_DIR}"
            )
        
        try:
            # Cargar solo las columnas necesarias
            df = pd.read_csv(
                CREDITO_FILE,
                usecols=COLUMNAS_CREDITO,
                nrows=self.sample_size,
                sep=';',              
                encoding='utf-8-sig', 
                low_memory=False
            )
            
            logger.info(f"Dataset de créditos cargado: {df.shape[0]:,} filas, {df.shape[1]} columnas")
            logger.info(f"Memoria utilizada: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar dataset de créditos: {e}")
            raise
    
    def load_covid_data(self) -> pd.DataFrame:

        logger.info("Cargando dataset de COVID-19...")
        
        if not COVID_FILE.exists():
            logger.warning(f"Dataset de COVID no encontrado en: {COVID_FILE}")
            logger.warning("Se continuará sin datos de COVID")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(COVID_FILE, low_memory=False)
            
            # columnas 
            columnas_necesarias = ['DEPARTAMENTO', 'FECHA_RESULTADO', 'EDAD', 'SEXO']
            columnas_disponibles = [col for col in columnas_necesarias if col in df.columns]
            df = df[columnas_disponibles]
            
            logger.info(f"Dataset de COVID cargado: {df.shape[0]:,} filas")
            
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar dataset de COVID: {e}")
            return pd.DataFrame()
    
    def load_temperatura_data(self) -> pd.DataFrame:
        logger.info("Cargando dataset de temperatura...")
        
        if not TEMPERATURA_FILE.exists():
            logger.warning(f"Dataset de temperatura no encontrado en: {TEMPERATURA_FILE}")
            logger.warning("Se continuará sin datos de temperatura")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(TEMPERATURA_FILE)
            
            logger.info(f"Dataset de temperatura cargado: {df.shape[0]:,} filas")
            
            return df
            
        except Exception as e:
            logger.error(f"Error al cargar dataset de temperatura: {e}")
            return pd.DataFrame()
    
    def load_all_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    
        logger.info("INICIANDO CARGA DE DATOS")
        
        df_credito = self.load_credito_data()
        df_covid = self.load_covid_data()
        df_temperatura = self.load_temperatura_data()
        
        logger.info("\n" + "="*60)
        logger.info("RESUMEN DE DATOS CARGADOS")
        logger.info("="*60)
        logger.info(f"Créditos: {df_credito.shape[0]:,} registros")
        logger.info(f"COVID: {df_covid.shape[0]:,} registros")
        logger.info(f"Temperatura: {df_temperatura.shape[0]:,} registros")
        logger.info("="*60 + "\n")
        
        return df_credito, df_covid, df_temperatura
    
    def validate_data(self, df: pd.DataFrame, dataset_name: str) -> bool:
      
        if df.empty:
            logger.warning(f"Dataset {dataset_name} está vacío")
            return False
        
        # Verificar valores faltantes
        null_counts = df.isnull().sum()
        if null_counts.any():
            logger.info(f"\nValores faltantes en {dataset_name}:")
            logger.info(null_counts[null_counts > 0])
        
        return True


def quick_data_exploration(df: pd.DataFrame, name: str = "Dataset"):
    
    print(f"\n{'='*60}")
    print(f"EXPLORACIÓN DE {name.upper()}")
    print(f"{'='*60}")
    
    print(f"\n📊 Dimensiones: {df.shape[0]:,} filas × {df.shape[1]} columnas")
    
    print(f"\n📋 Primeras filas:")
    print(df.head(3))
    
    print(f"\n🔢 Tipos de datos:")
    print(df.dtypes.value_counts())
    
    print(f"\n❓ Valores faltantes:")
    missing = df.isnull().sum()
    if missing.any():
        missing_pct = (missing / len(df) * 100).round(2)
        missing_df = pd.DataFrame({
            'Columna': missing.index,
            'Faltantes': missing.values,
            'Porcentaje': missing_pct.values
        })
        print(missing_df[missing_df['Faltantes'] > 0].to_string(index=False))
    else:
        print(" No hay valores faltantes")
    
    print(f"\n Estadísticas numéricas:")
    print(df.describe())


def load_datasets(sample_size: Optional[int] = None, 
                 explore: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    
    loader = DataLoader(sample_size=sample_size)
    df_credito, df_covid, df_temperatura = loader.load_all_data()
    
    if explore:
        quick_data_exploration(df_credito, "Crédito")
        if not df_covid.empty:
            quick_data_exploration(df_covid, "COVID-19")
        if not df_temperatura.empty:
            quick_data_exploration(df_temperatura, "Temperatura")
    
    return df_credito, df_covid, df_temperatura


if __name__ == "__main__":
    print("Probando carga de datos con muestra de 10,000 registros...")
    df_credito, df_covid, df_temp = load_datasets(sample_size=10000, explore=True)