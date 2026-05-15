"""
data_processing.py
Clase DataProcessor: Transforma datos raw al formato
esperado por el modelo final.
"""

import pandas as pd
from src.utils import COLS_DROP, TARGET_COL


class DataProcessor:
    """
    Preprocesa datos raw del UCI #697.
    El ColumnTransformer vive dentro del Pipeline del modelo
    y se aplica automáticamente en predict().
    """

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pipeline completo. Entrada: DataFrame raw.
        Salida: DataFrame con 28 features listo para el modelo.
        """
        df = df.copy()
        df = self._drop_grupo_b(df)
        df = self._drop_target(df)
        df = self._engineer_features(df)
        return df

    def _drop_grupo_b(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = [c for c in COLS_DROP if c in df.columns]
        return df.drop(columns=cols)

    def _drop_target(self, df: pd.DataFrame) -> pd.DataFrame:
        if TARGET_COL in df.columns:
            return df.drop(columns=[TARGET_COL])
        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Mother's qualification" in df.columns:
            df['parents_qualification_avg'] = (
                df["Mother's qualification"] +
                df["Father's qualification"]
            ) / 2

        if 'Debtor' in df.columns:
            df['financial_risk'] = (
                df['Debtor'] + (1 - df['Tuition fees up to date'])
            )

        if 'Age at enrollment' in df.columns:
            df['age_group'] = pd.cut(
                df['Age at enrollment'],
                bins=[0, 20, 25, 35, 100],
                labels=[0, 1, 2, 3]
            ).astype(int)

        if 'Application order' in df.columns:
            df['is_first_choice'] = (
                df['Application order'] == 1
            ).astype(int)

        return df