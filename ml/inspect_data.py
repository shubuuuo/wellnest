from pathlib import Path
import sys
import pandas as pd

# df = pd.read_csv(Path(__file__).parent / "data" / "lung_cancer_risk.csv")
name = sys.argv[1] if len(sys.argv) > 1 else "lung_cancer_risk.csv"
df = pd.read_csv(Path(__file__).parent / "data" / name)
print("shape:", df.shape)
print("\ncolumn types:\n", df.dtypes)
print("\nfirst rows:\n", df.head())

missing = df.isna().sum()
print("\ncolumns with missing values:\n", missing[missing > 0])

print("\nsmall columns (likely yes/no or categories):")
for col in df.columns:
    if df[col].nunique() <= 6:
        print(" ", col, df[col].value_counts(dropna=False).to_dict())

# lung_cancer -> Target Column -> Yes/No
# Unique id -> patient_id