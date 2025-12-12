"""
Script de entrenamiento del modelo híbrido difuso-neuronal
Ejecutar: python train_model.py
"""
import sys
sys.path.append('src')

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from colorama import Fore, Style, init

# Importar módulos del proyecto
from data_loader import load_datasets
from data_preprocessing import preprocess_all_data
from fuzzy_system import FuzzyCreditRiskSystem
from feature_engineering import FeatureEngineer, prepare_train_test_split
from ml_model import CreditRiskMLModel
from config import (
    MODEL_FILE, ENCODERS_FILE, INTEGRATED_FILE,
    TARGET_COLUMN, PROCESSED_DATA_DIR
)

init(autoreset=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def entrenar_modelo_completo(sample_size=None, guardar_datos=True):
    
    print("\n" + "="*70)
    print(Fore.CYAN + Style.BRIGHT + "   SISTEMA HÍBRIDO DIFUSO-NEURONAL - ENTRENAMIENTO DEL MODELO")
    print("="*70 + "\n")
    
    try:
        # ============= PASO 1: CARGAR DATOS =============
        print(Fore.YELLOW + Style.BRIGHT + "PASO 1: CARGANDO DATOS")
        print("-" * 70)
        
        df_credito, df_covid, df_temp = load_datasets(sample_size=sample_size, explore=False)
        
        # ============= PASO 2: PREPROCESAR DATOS =============
        print(Fore.YELLOW + Style.BRIGHT + "\nPASO 2: PREPROCESANDO DATOS")
        print("-" * 70)
        
        df_procesado = preprocess_all_data(df_credito, df_covid, df_temp)
        
        # Verificar que existe la variable objetivo
        if TARGET_COLUMN not in df_procesado.columns:
            raise ValueError(f"Variable objetivo '{TARGET_COLUMN}' no encontrada")
        
        # Eliminar filas con target faltante
        df_procesado = df_procesado.dropna(subset=[TARGET_COLUMN])
        
        logger.info(f"Dataset final: {len(df_procesado):,} registros")
        
        # Guardar dataset procesado
        if guardar_datos:
            PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
            df_procesado.to_csv(INTEGRATED_FILE, index=False)
            logger.info(f"Dataset procesado guardado en: {INTEGRATED_FILE}")
        
        # ============= PASO 3: SISTEMA DIFUSO =============
        print(Fore.YELLOW + Style.BRIGHT + "\nPASO 3: EVALUANDO SISTEMA DIFUSO")
        print("-" * 70)
        
        fuzzy_system = FuzzyCreditRiskSystem()
        
        # Evaluar sistema difuso en batch
        scores_difusos = fuzzy_system.evaluate_batch(df_procesado)
        df_procesado['score_riesgo_difuso'] = scores_difusos
        
        print(Fore.GREEN + f"✅ Sistema difuso evaluado")
        print(f"   Score promedio: {scores_difusos.mean():.2f}/100")
        print(f"   Score mínimo: {scores_difusos.min():.2f}")
        print(f"   Score máximo: {scores_difusos.max():.2f}")
        
        # ============= PASO 4: PREPARAR FEATURES =============
        print(Fore.YELLOW + Style.BRIGHT + "\nPASO 4: PREPARANDO FEATURES PARA ML")
        print("-" * 70)
        
        feature_engineer = FeatureEngineer()
        
        # Preparar features
        df_preparado = feature_engineer.prepare_features(df_procesado, fit=True)
        
        X_completo = feature_engineer.select_ml_features(df_preparado)
        
        # Agregar target
        X_completo[TARGET_COLUMN] = df_procesado[TARGET_COLUMN]
        
       
        # ==============================================================================
        from sklearn.preprocessing import LabelEncoder
        
        cols_texto = X_completo.select_dtypes(include=['object']).columns
        
        if len(cols_texto) > 0:
            print(Fore.CYAN + f"\nℹ️  Detectadas {len(cols_texto)} columnas de texto. Codificando automáticamente...")
            
            for col in cols_texto:
                # No tocamos la columna objetivo
                if col == TARGET_COLUMN:
                    continue
                    
                print(f"   🔧 Convirtiendo '{col}' de Texto -> Números...")
                le_cat = LabelEncoder()
                X_completo[col] = X_completo[col].fillna('DESCONOCIDO').astype(str)
                X_completo[col] = le_cat.fit_transform(X_completo[col])
        # ==============================================================================

        logger.info(f"Features preparadas: {len(X_completo.columns)-1} variables")

        feature_engineer.save_transformers(str(ENCODERS_FILE))
        
        # ============= PASO 5: DIVIDIR DATOS =============
        print(Fore.YELLOW + Style.BRIGHT + "\nPASO 5: DIVIDIENDO DATOS (TRAIN/TEST)")
        print("-" * 70)
        
        X_train, X_test, y_train, y_test = prepare_train_test_split(X_completo)
        
        # ============= PASO 6: ENTRENAR MODELO ML =============
        print(Fore.YELLOW + Style.BRIGHT + "\nPASO 6: ENTRENANDO MODELO XGBOOST")
        print("-" * 70)
        
        modelo = CreditRiskMLModel()
        modelo.train(X_train, y_train, X_val=X_test, y_val=y_test)
        
        print(Fore.GREEN + "✅ Modelo entrenado exitosamente")
        
        # ============= PASO 7: EVALUAR MODELO =============
        print(Fore.YELLOW + Style.BRIGHT + "\nPASO 7: EVALUANDO MODELO")
        print("-" * 70)
        
        metrics = modelo.evaluate(X_test, y_test)
        modelo.print_evaluation(metrics)
        
        # Mostrar top features
        print(Fore.CYAN + "\n📊 TOP 10 FEATURES MÁS IMPORTANTES:")
        print("-" * 70)
        top_features = modelo.get_top_features(10)
        for idx, row in top_features.iterrows():
            print(f"   {row['feature']:30s}: {row['importance']:.4f}")
        
        # ============= PASO 8: GUARDAR MODELO =============
        print(Fore.YELLOW + Style.BRIGHT + "\nPASO 8: GUARDANDO MODELO")
        print("-" * 70)
        
        modelo.save_model(str(MODEL_FILE))
        
        print(Fore.GREEN + f"\n✅ Modelo guardado en: {MODEL_FILE}")
        print(Fore.GREEN + f"✅ Encoders guardados en: {ENCODERS_FILE}")
        
        # ============= RESUMEN FINAL =============
        print("\n" + "="*70)
        print(Fore.GREEN + Style.BRIGHT + "✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        print("="*70)
        
        print(f"\n📊 Resumen:")
        print(f"   • Registros procesados: {len(df_procesado):,}")
        print(f"   • Features utilizadas: {len(X_completo.columns)-1}")
        print(f"   • Accuracy en test: {metrics['accuracy']:.4f}")
        print(f"   • F1-Score: {metrics['f1_score']:.4f}")
        
        if 'roc_auc' in metrics:
            print(f"   • ROC-AUC: {metrics['roc_auc']:.4f}")
        
        print(f"\n💡 Siguiente paso:")
        print(f"   Ejecuta el sistema con: python main.py")
        print("\n" + "="*70 + "\n")
        
        return modelo, metrics
        
    except Exception as e:
        logger.error(f"Error durante el entrenamiento: {e}")
        print(Fore.RED + f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return None, None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Entrenar el modelo híbrido de riesgo crediticio')
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='Número de filas a cargar (None = todas, útil para pruebas rápidas)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='No guardar el dataset procesado'
    )
    
    args = parser.parse_args()
    
    if args.sample:
        print(Fore.YELLOW + f"\n⚠️  MODO DE PRUEBA: Usando solo {args.sample:,} registros\n")
    
    modelo, metrics = entrenar_modelo_completo(
        sample_size=args.sample,
        guardar_datos=not args.no_save
    )
    
    if modelo:
        print(Fore.GREEN + "✅ Entrenamiento exitoso")
    else:
        print(Fore.RED + "❌ Entrenamiento falló")
        sys.exit(1)