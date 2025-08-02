import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import logging
from typing import Tuple, Dict
from .feature_engineering import FeatureEngineer

class DealScoreModel:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.feature_engineer = FeatureEngineer(config)
        self.model = None
        self.scaler = None
        self.feature_columns = None
        
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for training"""
        df_features = self.feature_engineer.create_features(df)
        
        if 'deal_score' not in df_features.columns:
            df_features = self._create_synthetic_labels(df_features)
        
        exclude_cols = [
            'id', 'platform', 'title', 'description', 'url', 'seller_name',
            'scraped_at', 'is_active', 'deal_score', 'is_hot_deal',
            'condition_keywords', 'condition_keywords_parsed', 'image_urls'
        ]
        
        feature_cols = [col for col in df_features.columns if col not in exclude_cols]
        
        X = df_features[feature_cols].fillna(0)
        y = df_features['deal_score']
        
        valid_mask = ~y.isna() & (y >= 0) & (y <= 1)
        X = X[valid_mask]
        y = y[valid_mask]
        
        self.feature_columns = feature_cols
        
        return X, y
    
    def train_model(self, df: pd.DataFrame) -> Dict:
        """Train the deal scoring model"""
        self.logger.info("Preparing training data...")
        X, y = self.prepare_training_data(df)
        
        if len(X) < 10:
            self.logger.warning("Not enough training data. Creating synthetic data for initial model.")
            X, y = self._create_synthetic_training_data()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.logger.info("Training model...")
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'mae': mean_absolute_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='r2')
        metrics['cv_r2_mean'] = cv_scores.mean()
        metrics['cv_r2_std'] = cv_scores.std()
        
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        self.logger.info(f"Model trained. R² score: {metrics['r2']:.3f}")
        self.logger.info("Top 10 most important features:")
        for _, row in feature_importance.head(10).iterrows():
            self.logger.info(f"  {row['feature']}: {row['importance']:.3f}")
        
        return metrics
    
    def predict_deal_scores(self, df: pd.DataFrame) -> np.ndarray:
        """Predict deal scores for new listings"""
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained yet. Call train_model() first.")
        
        df_features = self.feature_engineer.create_features(df)
        
        X = df_features[self.feature_columns].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        scores = self.model.predict(X_scaled)
        
        scores = np.clip(scores, 0, 1)
        
        return scores
    
    def save_model(self):
        """Save trained model and scaler"""
        if self.model is None:
            raise ValueError("No model to save. Train model first.")
        
        joblib.dump(self.model, self.config.MODEL_PATH)
        joblib.dump(self.scaler, self.config.FEATURE_SCALER_PATH)
        
        feature_info = {
            'feature_columns': self.feature_columns,
            'model_type': type(self.model).__name__
        }
        joblib.dump(feature_info, self.config.MODEL_PATH.replace('.pkl', '_info.pkl'))
        
        self.logger.info(f"Model saved to {self.config.MODEL_PATH}")
    
    def load_model(self):
        """Load trained model and scaler"""
        try:
            self.model = joblib.load(self.config.MODEL_PATH)
            self.scaler = joblib.load(self.config.FEATURE_SCALER_PATH)
            
            feature_info = joblib.load(self.config.MODEL_PATH.replace('.pkl', '_info.pkl'))
            self.feature_columns = feature_info['feature_columns']
            
            self.logger.info("Model loaded successfully")
            return True
        except FileNotFoundError:
            self.logger.warning("No saved model found")
            return False
    
    def _create_synthetic_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create synthetic deal scores based on heuristics"""
        df = df.copy()
        
        df['deal_score'] = 0.5
        
        if 'price' in df.columns and df['price'].notna().any():
            for platform in df['platform'].unique():
                mask = df['platform'] == platform
                prices = df.loc[mask, 'price']
                if len(prices) > 1 and prices.std() > 0:
                    price_percentiles = prices.rank(pct=True)
                    df.loc[mask, 'deal_score'] += 0.3 * (1 - price_percentiles)
        
        if 'condition_score' in df.columns:
            condition_norm = (df['condition_score'] - df['condition_score'].min()) / \
                           (df['condition_score'].max() - df['condition_score'].min() + 1e-8)
            df['deal_score'] += 0.2 * condition_norm
        
        if 'lq4_priority_score' in df.columns:
            lq4_norm = df['lq4_priority_score'] / (df['lq4_priority_score'].max() + 1e-8)
            df['deal_score'] += 0.3 * lq4_norm
        
        if 'estimated_distance' in df.columns:
            distance_penalty = np.clip(df['estimated_distance'] / 1000, 0, 0.2)
            df['deal_score'] -= distance_penalty
        
        if 'platform_reliability' in df.columns:
            df['deal_score'] += 0.1 * df['platform_reliability']
        
        df['deal_score'] = np.clip(df['deal_score'], 0, 1)
        
        return df
    
    def _create_synthetic_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Create synthetic training data for initial model"""
        np.random.seed(42)
        n_samples = 1000
        
        data = {
            'price': np.random.lognormal(7, 1, n_samples),  # Prices around $1000-$5000
            'log_price': np.random.normal(7, 1, n_samples),
            'title_length': np.random.randint(20, 100, n_samples),
            'title_word_count': np.random.randint(3, 15, n_samples),
            'description_length': np.random.randint(0, 500, n_samples),
            'has_description': np.random.binomial(1, 0.7, n_samples),
            'good_condition_count': np.random.poisson(1, n_samples),
            'bad_condition_count': np.random.poisson(0.3, n_samples),
            'condition_score': np.random.normal(0, 2, n_samples),
            'is_rebuilt': np.random.binomial(1, 0.2, n_samples),
            'is_new': np.random.binomial(1, 0.1, n_samples),
            'needs_work': np.random.binomial(1, 0.15, n_samples),
            'estimated_distance': np.random.exponential(200, n_samples),
            'is_local': np.random.binomial(1, 0.3, n_samples),
            'platform_reliability': np.random.uniform(0.5, 0.9, n_samples),
            'is_lq4': np.random.binomial(1, 0.3, n_samples),
            'is_ls_engine': np.random.binomial(1, 0.5, n_samples),
            'is_chevy': np.random.binomial(1, 0.6, n_samples),
            'is_v8': np.random.binomial(1, 0.7, n_samples),
            'lq4_priority_score': np.random.randint(0, 8, n_samples),
            'is_complete_engine': np.random.binomial(1, 0.4, n_samples),
        }
        
        df = pd.DataFrame(data)
        
        deal_score = (
            0.3 * (1 - (df['price'] - df['price'].min()) / (df['price'].max() - df['price'].min())) +
            0.2 * np.clip(df['condition_score'] / 5, 0, 1) +
            0.2 * df['lq4_priority_score'] / 8 +
            0.1 * df['is_rebuilt'] +
            0.1 * df['platform_reliability'] +
            0.1 * (1 - np.clip(df['estimated_distance'] / 1000, 0, 1))
        )
        
        deal_score += np.random.normal(0, 0.1, n_samples)
        deal_score = np.clip(deal_score, 0, 1)
        
        self.feature_columns = list(df.columns)
        
        return df, deal_score
