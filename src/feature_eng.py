import pandas as pd
import numpy as np
from typing import Tuple

class FeatureEngineer:
    """
    Handles feature engineering for the honeypot log data.
    Extracts features relevant to attack classification.
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with the raw dataframe.
        Args:
            df (pd.DataFrame): Raw honeypot logs.
        """
        self.df = df.copy()

    def preprocess(self) -> pd.DataFrame:
        """
        Basic preprocessing: handle missing values, convert timestamps, etc.
        """
        # Fill missing values for numerical columns with 0
        num_cols = ['duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts', 'orig_ip_bytes', 'resp_ip_bytes']
        for col in num_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna(0)
        
        # Fill missing values for categorical columns with 'unknown'
        cat_cols = ['proto', 'service', 'conn_state', 'history']
        for col in cat_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna('unknown')
                
        return self.df

    def extract_features(self) -> pd.DataFrame:
        """
        Extracts features:
        - Session duration
        - Packet counts
        - Protocol flags
        - Payload size
        - Bytes per session
        - Command frequency
        
        Creates Target Variable: Attack intention (Intent-to-act vs. Intent-to-probe)
        """
        # Feature Engineering
        if 'orig_bytes' in self.df.columns and 'resp_bytes' in self.df.columns:
            self.df['bytes_per_session'] = self.df['orig_bytes'] + self.df['resp_bytes']
        else:
            self.df['bytes_per_session'] = 0
            
        if 'orig_pkts' in self.df.columns and 'resp_pkts' in self.df.columns:
            self.df['packet_count'] = self.df['orig_pkts'] + self.df['resp_pkts']
        else:
            self.df['packet_count'] = 0
            
        # Command frequency proxy (using history length)
        if 'history' in self.df.columns:
            self.df['history_len'] = self.df['history'].astype(str).apply(len)
        else:
            self.df['history_len'] = 0

        # Target Variable Creation (Heuristic based on research context)
        # Intent-to-act: Successful connection (SF) and significant data transfer or interaction
        # Intent-to-probe: Failed connection, scanning (S0, REJ), or negligible data transfer
        
        def define_target(row):
            # If connection state is 'SF' (Normal establishment) and data was transferred
            if row['conn_state'] == 'SF' and row['bytes_per_session'] > 100:
                return 1 # Intent-to-act
            # If history indicates interaction (e.g., 'ShAdDaF')
            if 'A' in str(row['history']) and 'D' in str(row['history']):
                 return 1 # Intent-to-act
            return 0 # Intent-to-probe

        self.df['target'] = self.df.apply(define_target, axis=1)
        
        return self.df

    def get_processed_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Returns X (features) and y (target).
        """
        self.preprocess()
        self.extract_features()
        
        # Select features for training
        feature_cols = [
            'duration', 'orig_bytes', 'resp_bytes', 'bytes_per_session', 
            'orig_pkts', 'resp_pkts', 'packet_count', 'history_len'
        ]
        
        # One-hot encoding for categorical features
        # Note: In a real pipeline, use OneHotEncoder to handle unseen categories during inference
        categorical_cols = ['proto', 'conn_state']
        
        X = self.df[feature_cols].copy()
        
        # Simple one-hot encoding for demonstration
        X = pd.get_dummies(X.join(self.df[categorical_cols]), columns=categorical_cols)
        
        y = self.df['target']
        
        return X, y

if __name__ == "__main__":
    # Test stub
    pass
