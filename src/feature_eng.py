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
        Basic preprocessing: handle missing values for the columns we load.
        """
        # Fill missing values for numerical columns with 0
        num_cols = ['duration', 'orig_bytes', 'resp_bytes', 'orig_pkts', 'resp_pkts']
        for col in num_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna(0)

        # Fill missing values for categorical columns with 'unknown'
        cat_cols = ['proto', 'conn_state', 'history']
        for col in cat_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].fillna('unknown')

        return self.df

    def extract_features(self) -> pd.DataFrame:
        """
        Extracts derived features:
        - bytes_per_session  (used ONLY for target creation, excluded from X)
        - packet_count
        - history_len

        Creates Target Variable: Attack intention
            1 = Intent-to-act, 0 = Intent-to-probe
        """
        # Derived feature — used for label definition only
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
                return 1  # Intent-to-act
            # If history indicates interaction (e.g., 'ShAdDaF')
            if 'A' in str(row['history']) and 'D' in str(row['history']):
                return 1  # Intent-to-act
            return 0  # Intent-to-probe

        self.df['target'] = self.df.apply(define_target, axis=1)

        return self.df

    # ──────────────────────────────────────────────
    # Shared helper: build the leakage-free feature matrix
    # ──────────────────────────────────────────────
    def _build_feature_matrix(self) -> pd.DataFrame:
        """
        Builds the model-ready feature matrix X, ensuring no label leakage.

        conn_state and bytes_per_session are EXCLUDED because they directly
        encode the conditions used to create the target variable.
        """
        # conn_state and bytes_per_session excluded to prevent label leakage
        # as they directly encode the target heuristic conditions
        feature_cols = [
            'duration', 'orig_bytes', 'resp_bytes',
            'orig_pkts', 'resp_pkts', 'packet_count', 'history_len',
        ]

        # Only one-hot encode 'proto' — conn_state is excluded
        categorical_cols = ['proto']

        X = self.df[feature_cols].copy()
        X = pd.get_dummies(
            X.join(self.df[categorical_cols]),
            columns=categorical_cols,
        )

        return X

    # ──────────────────────────────────────────────
    # Training path (features + target)
    # ──────────────────────────────────────────────
    def get_processed_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Returns X (features) and y (target) for model training.
        """
        self.preprocess()
        self.extract_features()

        X = self._build_feature_matrix()
        y = self.df['target']

        return X, y

    # ──────────────────────────────────────────────
    # Inference path (features only, no target)
    # ──────────────────────────────────────────────
    def get_inference_features(self) -> pd.DataFrame:
        """
        Returns X only (no target creation) for live inference.

        Used by log_watcher.py where no label exists.
        """
        self.preprocess()
        self.extract_features()  # computes derived cols; target is ignored

        X = self._build_feature_matrix()
        return X


if __name__ == "__main__":
    # Test stub
    pass
