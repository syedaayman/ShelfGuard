import math
from pathlib import Path

import joblib
import pandas as pd

MODEL_PATH = Path(__file__).with_name("pricing_model.pkl")
model = joblib.load(MODEL_PATH)


def _validate_inputs(days_to_expiry, stock_level,
                     remaining_shelf_life_pct,
                     supplier_score, is_promoted):
    values = {
        "days_to_expiry": days_to_expiry,
        "stock_level": stock_level,
        "remaining_shelf_life_pct": remaining_shelf_life_pct,
        "supplier_score": supplier_score,
    }
    if any(not math.isfinite(float(value)) for value in values.values()):
        raise ValueError("Numeric inputs must be finite")
    if days_to_expiry < 0:
        raise ValueError("days_to_expiry cannot be negative")
    if stock_level < 0:
        raise ValueError("stock_level cannot be negative")
    if not 0 <= remaining_shelf_life_pct <= 100:
        raise ValueError("remaining_shelf_life_pct must be between 0 and 100")
    if not 6 <= supplier_score <= 10:
        raise ValueError("supplier_score must be between 6 and 10")
    if is_promoted not in (0, 1):
        raise ValueError("is_promoted must be 0 or 1")


def predict_discount(days_to_expiry, stock_level,
                     remaining_shelf_life_pct,
                     supplier_score, is_promoted):

    _validate_inputs(
        days_to_expiry,
        stock_level,
        remaining_shelf_life_pct,
        supplier_score,
        is_promoted,
    )

    new_product = pd.DataFrame({
        "days_to_expiry": [days_to_expiry],
        "stock_level": [stock_level],
        "remaining_shelf_life_pct": [remaining_shelf_life_pct],
        "supplier_score": [supplier_score],
        "is_promoted": [is_promoted]
    })

    prediction = float(model.predict(new_product)[0])

    return max(0.0, min(1.0, prediction))
