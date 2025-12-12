import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.compose import ColumnTransformer
import joblib
import logging
from typing import Tuple, Dict
from config import ML_FEATURES, TARGET_COLUMN

logger = logging.getLogger(__name__)


class FeatureEngineer:
  
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = None
        self.numeric_features = []
        self.categorical_features = []
        
    def identify_feature_types(self, df: pd.DataFrame):
       
        self.numeric_features = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        self.categorical_features = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Remover target si está presente
        if TARGET_COLUMN in self.numeric_features:
            self.numeric_features.remove(TARGET_COLUMN)
        if TARGET_COLUMN in self.categorical_features:
            self.categorical_features.remove(TARGET_COLUMN)
        
        logger.info(f"Features numéricas: {len(self.numeric_features)}")
        logger.info(f"Features categóricas: {len(self.categorical_features)}")
        
    def encode_categorical(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        
        df = df.copy()
        
        for col in self.categorical_features:
            if col not in df.columns:
                continue
                
            if fit:
                le = LabelEncoder()
                df[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
                self.label_encoders[col] = le
            else:
                if col in self.label_encoders:
                    le = self.label_encoders[col]
                    # Manejar categorías no vistas
                    df[f'{col}_encoded'] = df[col].astype(str).map(
                        lambda x: le.transform([x])[0] if x in le.classes_ else -1
                    )
                else:
                    df[f'{col}_encoded'] = 0
        
        return df
    
    def scale_numeric(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        
        df = df.copy()
        
        numeric_cols_present = [col for col in self.numeric_features if col in df.columns]
        
        if not numeric_cols_present:
            return df
        
        if fit:
            df[numeric_cols_present] = self.scaler.fit_transform(df[numeric_cols_present])
        else:
            df[numeric_cols_present] = self.scaler.transform(df[numeric_cols_present])
        
        return df
    
    def prepare_features(self, df: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        
        logger.info("Preparando features...")
        
        if fit:
            self.identify_feature_types(df)
        
        df = self.encode_categorical(df, fit=fit)
        
        df = self.scale_numeric(df, fit=fit)
        
        logger.info("Features preparadas exitosamente")
        
        return df
    
    def select_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
          
        features_to_keep = []
        
        for feat in ML_FEATURES:
            if feat in df.columns:
                features_to_keep.append(feat)
        
        for col in self.categorical_features:
            encoded_col = f'{col}_encoded'
            if encoded_col in df.columns:
                features_to_keep.append(encoded_col)
        
        if 'score_riesgo_difuso' in df.columns and 'score_riesgo_difuso' not in features_to_keep:
            features_to_keep.append('score_riesgo_difuso')

        features_available = [f for f in features_to_keep if f in df.columns]
        
        self.feature_names = features_available
        
        logger.info(f"Features seleccionadas para ML: {len(features_available)}")
        
        return df[features_available]
    
    def save_transformers(self, path: str):
        
        transformers = {
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'numeric_features': self.numeric_features,
            'categorical_features': self.categorical_features
        }
        joblib.dump(transformers, path)
        logger.info(f"Transformers guardados en: {path}")
    
    def load_transformers(self, path: str):
        transformers = joblib.load(path)
        self.scaler = transformers['scaler']
        self.label_encoders = transformers['label_encoders']
        self.feature_names = transformers['feature_names']
        self.numeric_features = transformers['numeric_features']
        self.categorical_features = transformers['categorical_features']
        logger.info(f"Transformers cargados desde: {path}")


def prepare_train_test_split(
    df: pd.DataFrame,
    target_col: str = TARGET_COLUMN,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    
    from sklearn.model_selection import train_test_split
    
    logger.info("Preparando datos para entrenamiento...")
    
    if target_col not in df.columns:
        raise ValueError(f"Columna objetivo '{target_col}' no encontrada en el dataset")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    logger.info(f"Datos divididos: Train={len(X_train):,}, Test={len(X_test):,}")
    logger.info(f"Distribución target (train): {y_train.value_counts().to_dict()}")
    
    return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    print("Probando Feature Engineer...")
    
    df_test = pd.DataFrame({
        'score_riesgo_difuso': np.random.rand(100) * 100,
        'monto': np.random.rand(100) * 10000,
        'SalarioNormalizado': np.random.rand(100) * 5000,
        'EstadoCivil': np.random.choice(['CASADO', 'SOLTERO'], 100),
        'Sexo': np.random.choice([1, 2], 100),
        'Class_202309FM': np.random.choice([0, 1], 100)
    })
    
    fe = FeatureEngineer()
    
    df_prepared = fe.prepare_features(df_test, fit=True)
    
    print("\nDataFrame preparado:")
    print(df_prepared.head())
    
    X = fe.select_ml_features(df_prepared)
    
    print("\nFeatures para ML:")
    print(X.head())