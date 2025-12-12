import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    accuracy_score, precision_score, recall_score, f1_score
)
import joblib
import logging
from typing import Dict, Tuple
from config import ML_PARAMS, TARGET_MAPPING

logger = logging.getLogger(__name__)


class CreditRiskMLModel:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.feature_importance = None
        self.training_metrics = {}
        
    def build_model(self):

        logger.info("Construyendo modelo XGBoost...")
        
        self.model = XGBClassifier(**ML_PARAMS['xgboost'])
        
        logger.info("Modelo XGBoost construido")
        
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
              X_val: pd.DataFrame = None, y_val: pd.Series = None):

        logger.info("Iniciando entrenamiento del modelo...")
        logger.info(f"Datos de entrenamiento: {X_train.shape}")
        
        if self.model is None:
            self.build_model()

        eval_set = None
        if X_val is not None and y_val is not None:
            eval_set = [(X_val, y_val)]

        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False
        )
        
        self.is_trained = True
        
        self.feature_importance = pd.DataFrame({
            'feature': X_train.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        logger.info("Entrenamiento completado")
        
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        return self.model.predict_proba(X)
    
    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        logger.info("Evaluando modelo...")
        
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)
        
        # Calcular métricas
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_test, y_pred, average='weighted', zero_division=0)
        }
        
        # ROC AUC
        if len(np.unique(y_test)) == 2:
            metrics['roc_auc'] = roc_auc_score(y_test, y_proba[:, 1])
        
        # Matriz de confusión
        metrics['confusion_matrix'] = confusion_matrix(y_test, y_pred)
        
        # Reporte de clasificación
        metrics['classification_report'] = classification_report(
            y_test, y_pred,
            target_names=[TARGET_MAPPING.get(i, str(i)) for i in sorted(np.unique(y_test))],
            zero_division=0
        )
        
        self.training_metrics = metrics
        
        logger.info("Evaluación completada")
        
        return metrics
    
    def print_evaluation(self, metrics: Dict = None):
        if metrics is None:
            metrics = self.training_metrics
        
        print("EVALUACIÓN DEL MODELO")

        
        print(f"\n Métricas Generales:")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1-Score:  {metrics['f1_score']:.4f}")
        
        if 'roc_auc' in metrics:
            print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
        
        print(f"\n Reporte de Clasificación:")
        print(metrics['classification_report'])
        
        print(f"\n Matriz de Confusión:")
        print(metrics['confusion_matrix'])
        
        print("\n" + "="*60)
    
    def get_top_features(self, n: int = 10) -> pd.DataFrame:
        
        if self.feature_importance is None:
            raise ValueError("No hay información de importancia de features")
        
        return self.feature_importance.head(n)
    
    def save_model(self, path: str):
        
        if not self.is_trained:
            raise ValueError("El modelo no ha sido entrenado")
        
        model_data = {
            'model': self.model,
            'feature_importance': self.feature_importance,
            'training_metrics': self.training_metrics
        }
        
        joblib.dump(model_data, path)
        logger.info(f"Modelo guardado en: {path}")
    
    def load_model(self, path: str):
        
        model_data = joblib.load(path)
        
        self.model = model_data['model']
        self.feature_importance = model_data.get('feature_importance')
        self.training_metrics = model_data.get('training_metrics', {})
        self.is_trained = True
        
        logger.info(f"Modelo cargado desde: {path}")


def compare_with_baseline(y_test: pd.Series, y_pred: np.ndarray) -> Dict:
    
    baseline_pred = np.full_like(y_test, y_test.mode()[0])
    
    baseline_acc = accuracy_score(y_test, baseline_pred)
    model_acc = accuracy_score(y_test, y_pred)
    
    improvement = ((model_acc - baseline_acc) / baseline_acc) * 100
    
    comparison = {
        'baseline_accuracy': baseline_acc,
        'model_accuracy': model_acc,
        'improvement_pct': improvement
    }
    
    logger.info(f"Baseline accuracy: {baseline_acc:.4f}")
    logger.info(f"Model accuracy: {model_acc:.4f}")
    logger.info(f"Mejora: {improvement:.2f}%")
    
    return comparison


if __name__ == "__main__":
    # Prueba del modelo
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    
    print("Probando modelo de ML...")
    
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        n_redundant=5,
        random_state=42
    )
    
    X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(20)])
    y = pd.Series(y)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = CreditRiskMLModel()
    model.train(X_train, y_train)

    metrics = model.evaluate(X_test, y_test)
    model.print_evaluation()
    
    print("\nTop 5 Features:")
    print(model.get_top_features(5))