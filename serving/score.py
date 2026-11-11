import mlflow.pyfunc
import pandas as pd
from logger import get_logger

logger = get_logger()

MODEL = None

FEATURE_COLUMNS = [
    "LIMIT_BAL",
    "SEX",
    "EDUCATION",
    "MARRIAGE",
    "AGE",
    "PAY_0",
    "PAY_2",
    "PAY_3",
    "PAY_4",
    "PAY_5",
    "PAY_6",
    "BILL_AMT1",
    "BILL_AMT2",
    "BILL_AMT3",
    "BILL_AMT4",
    "BILL_AMT5",
    "BILL_AMT6",
    "PAY_AMT1",
    "PAY_AMT2",
    "PAY_AMT3",
    "PAY_AMT4",
    "PAY_AMT5",
    "PAY_AMT6"
]

def load_model(model_path):

    global MODEL

    logger.info(
        "Loading MLflow model",
        extra={
            "event": "model_loading"
        }
    )

    MODEL = mlflow.pyfunc.load_model(model_path)

    logger.info(
        "Model loaded successfully",
        extra={
            "event": "model_loaded"
        }
    )

    return MODEL

def predict(features: dict) -> dict:
    """
    Score a single credit default request.
    """

    if MODEL is None:
        raise RuntimeError("Model is not loaded")

    missing_features = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in features
    ]

    if missing_features:
        raise ValueError(
            f"Missing features: {missing_features}"
        )

    df = pd.DataFrame([features])

    # Enforce training-time feature order
    df = df[FEATURE_COLUMNS]

    prediction = MODEL.predict(df)

    pred = int(prediction[0])
    logger.info(
        f"Prediction completed successfully. Prediction: {pred}",
        extra={
            "event": "prediction_completed",
            "prediction": pred
        }
    )

    return {
        "prediction": pred,
        "prediction_label": (
            "Default"
            if pred == 1
            else "No Default"
        )
    }

def is_model_ready() -> bool:
    return MODEL is not None

