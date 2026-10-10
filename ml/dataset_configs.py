DATASETS = {
    "lung": {
        "label": "Lung cancer risk",
        "csv": "lung_cancer_risk.csv",
        "target": "lung_cancer",   # use YOUR values from inspect_data.py
        "drop_cols": [],
        "positive_values": {"1", "1.0", "yes", "true", "positive", "y"},
        "n_rows": 30000,
    },
    "breast": {
        "label": "Breast cancer (Wisconsin)",
        "csv": "breast_cancer.csv",
        "target": "target",
        "drop_cols": [],
        "positive_values": {"0"},  # in scikit-learn's copy, 0 means malignant
        "n_rows": 30000,
    },
        "thyroid": {
        "label": "Thyroid cancer risk",
        "csv": "thyroid_cancer_risk.csv",         # rename your downloaded file to this
        "target": "Diagnosis",                    # check the exact name with inspect_data.py
        "drop_cols": ["Patient_ID", "Thyroid_Cancer_Risk"],
        "positive_values": {"malignant"},
        "n_rows": 30000,
    },
    "prostate": {
        "label": "Prostate cancer",
        "csv": "prostate_cancer.csv",
        "target": "diagnosis_result",
        "drop_cols": ["id"],                      # may be "Id" in the file
        "positive_values": {"m"},                 # M = malignant, B = benign
        "n_rows": 30000,
    },
}