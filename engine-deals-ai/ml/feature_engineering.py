import pandas as pd
import numpy as np
from typing import List, Dict
import re
from geopy.distance import geodesic
import json

class FeatureEngineer:
    def __init__(self, config):
        self.config = config
        
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features for ML model training"""
        df = df.copy()
        
        df['log_price'] = np.log1p(df['price'].fillna(0))
        df['price_per_word'] = df['price'] / (df['title'].str.split().str.len() + 1)
        
        df = self._create_text_features(df)
        
        df = self._create_condition_features(df)
        
        df = self._create_location_features(df)
        
        df = self._create_platform_features(df)
        
        df = self._create_temporal_features(df)
        
        df = self._create_engine_features(df)
        
        return df
    
    def _create_text_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features from title and description text"""
        df['title_length'] = df['title'].str.len()
        df['title_word_count'] = df['title'].str.split().str.len()
        df['description_length'] = df['description'].fillna('').str.len()
        df['description_word_count'] = df['description'].fillna('').str.split().str.len()
        
        df['has_description'] = (df['description_length'] > 0).astype(int)
        df['title_caps_ratio'] = df['title'].apply(self._caps_ratio)
        df['description_caps_ratio'] = df['description'].fillna('').apply(self._caps_ratio)
        
        df['has_part_number'] = df['title'].str.contains(r'\b\d{4,}\b', case=False, na=False).astype(int)
        df['has_year'] = df['title'].str.contains(r'\b(?:19|20)\d{2}\b', case=False, na=False).astype(int)
        df['has_mileage'] = df['title'].str.contains(r'\b\d+k?\s*(?:miles?|mi)\b', case=False, na=False).astype(int)
        
        return df
    
    def _create_condition_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create features from condition keywords"""
        df['condition_keywords_parsed'] = df['condition_keywords'].apply(
            lambda x: json.loads(x) if isinstance(x, str) else (x if isinstance(x, list) else [])
        )
        
        df['good_condition_count'] = df['condition_keywords_parsed'].apply(
            lambda keywords: sum(1 for k in keywords if k.startswith('good_'))
        )
        df['bad_condition_count'] = df['condition_keywords_parsed'].apply(
            lambda keywords: sum(1 for k in keywords if k.startswith('bad_'))
        )
        
        df['condition_score'] = df['good_condition_count'] - df['bad_condition_count']
        
        text_combined = df['title'] + ' ' + df['description'].fillna('')
        df['is_rebuilt'] = text_combined.str.contains('rebuilt|remanufactured', case=False, na=False).astype(int)
        df['is_new'] = text_combined.str.contains(r'\bnew\b', case=False, na=False).astype(int)
        df['needs_work'] = text_combined.str.contains('needs work|for parts|repair', case=False, na=False).astype(int)
        df['low_miles'] = text_combined.str.contains('low miles|zero miles', case=False, na=False).astype(int)
        
        return df
    
    def _create_location_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create location-based features"""
        df['estimated_distance'] = df['location'].apply(self._estimate_distance)
        df['is_local'] = (df['estimated_distance'] < 100).astype(int)
        df['is_regional'] = (df['estimated_distance'] < 300).astype(int)
        
        df['has_specific_location'] = df['location'].str.len() > 5
        df['location_word_count'] = df['location'].str.split().str.len()
        
        return df
    
    def _create_platform_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create platform-specific features"""
        platforms = df['platform'].unique()
        for platform in platforms:
            df[f'platform_{platform}'] = (df['platform'] == platform).astype(int)
        
        platform_scores = {
            'ebay': 0.8,
            'craigslist': 0.6,
            'facebook': 0.7,
            'offerup': 0.6
        }
        df['platform_reliability'] = df['platform'].map(platform_scores).fillna(0.5)
        
        return df
    
    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features"""
        if 'scraped_at' not in df.columns:
            df['scraped_at'] = pd.Timestamp.now()
        
        df['scraped_at'] = pd.to_datetime(df['scraped_at'])
        df['hour_scraped'] = df['scraped_at'].dt.hour
        df['day_of_week'] = df['scraped_at'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        now = pd.Timestamp.now()
        df['hours_since_scraped'] = (now - df['scraped_at']).dt.total_seconds() / 3600
        
        return df
    
    def _create_engine_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create engine-specific features"""
        text_combined = df['title'] + ' ' + df['description'].fillna('')
        
        df['is_lq4'] = text_combined.str.contains(r'\blq4\b', case=False, na=False).astype(int)
        df['is_ls_engine'] = text_combined.str.contains(r'\bls[0-9]?\b', case=False, na=False).astype(int)
        df['is_vortec'] = text_combined.str.contains('vortec', case=False, na=False).astype(int)
        df['is_chevy'] = text_combined.str.contains('chevy|chevrolet', case=False, na=False).astype(int)
        df['is_v8'] = text_combined.str.contains(r'\bv8\b', case=False, na=False).astype(int)
        
        df['has_53_displacement'] = text_combined.str.contains(r'5\.3|5300', case=False, na=False).astype(int)
        df['has_60_displacement'] = text_combined.str.contains(r'6\.0|6000', case=False, na=False).astype(int)
        df['has_48_displacement'] = text_combined.str.contains(r'4\.8|4800', case=False, na=False).astype(int)
        
        df['is_complete_engine'] = text_combined.str.contains('complete engine|long block', case=False, na=False).astype(int)
        df['is_short_block'] = text_combined.str.contains('short block', case=False, na=False).astype(int)
        df['is_heads'] = text_combined.str.contains('heads|cylinder head', case=False, na=False).astype(int)
        df['is_intake'] = text_combined.str.contains('intake', case=False, na=False).astype(int)
        df['is_block'] = text_combined.str.contains(r'\bblock\b', case=False, na=False).astype(int)
        
        df['lq4_priority_score'] = (
            df['is_lq4'] * 3 +
            df['is_ls_engine'] * 2 +
            df['is_chevy'] * 1 +
            df['is_v8'] * 1 +
            df['has_60_displacement'] * 2  # LQ4 is 6.0L
        )
        
        return df
    
    def _caps_ratio(self, text: str) -> float:
        """Calculate ratio of capital letters in text"""
        if not text or len(text) == 0:
            return 0.0
        return sum(1 for c in text if c.isupper()) / len(text)
    
    def _estimate_distance(self, location: str) -> float:
        """Estimate distance from user location (simplified)"""
        if not location:
            return 500  # Default to max distance
        
        location_lower = location.lower()
        
        city_distances = {
            'new york': 0, 'nyc': 0, 'manhattan': 0, 'brooklyn': 10,
            'philadelphia': 95, 'boston': 215, 'washington': 225,
            'chicago': 790, 'detroit': 640, 'atlanta': 870,
            'miami': 1280, 'houston': 1630, 'dallas': 1550,
            'los angeles': 2800, 'san francisco': 2900, 'seattle': 2900
        }
        
        for city, distance in city_distances.items():
            if city in location_lower:
                return distance
        
        state_distances = {
            'ny': 100, 'nj': 50, 'ct': 100, 'pa': 150, 'ma': 200,
            'md': 250, 'va': 350, 'nc': 500, 'sc': 650, 'ga': 850,
            'fl': 1200, 'oh': 500, 'mi': 650, 'il': 800, 'in': 700,
            'tx': 1600, 'ca': 2800, 'wa': 2900, 'or': 2800
        }
        
        for state, distance in state_distances.items():
            if state in location_lower:
                return distance
        
        return 300  # Default moderate distance
