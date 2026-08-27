# ShelfGuard

ShelfGuard is a perishable-goods management project with a machine-learning model that recommends discounts based on expiry time, stock level, remaining shelf life, supplier score, and promotion status.

## Machine Learning

The final model is a tuned XGBoost regressor. The target column is `discount_pct`, stored as a fraction: `0.36` represents a `36%` discount.

Evaluation results on the fixed 20% test split:

- MAE: `0.0952` (about 9.52 percentage points)
- RMSE: `0.1343`
- R2: `0.4392`

Repeated 5-fold cross-validation with 3 repeats gave:

- MAE: `0.0951 +/- 0.0005` (fraction)
- RMSE: `0.1342 +/- 0.0006`
- R2: `0.4412 +/- 0.0073`

The repeated cross-validation results show that performance is stable across
different data splits. Since this is a regression model, accuracy is reported
with MAE, RMSE, and R2 rather than classification accuracy.

## Setup

Create or activate the project virtual environment, then install the dependencies:

```cmd
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Train the Model

Open `train_model.ipynb` and run all cells. The notebook loads `perishable_goods_management.csv`, engineers the model features, tunes XGBoost, evaluates the model, and saves `pricing_model.pkl`.

`Dynamic_Pricing.ipynb` is intended for exploratory analysis and model comparison. Use `train_model.ipynb` as the authoritative training notebook.

## Run the Prediction App

Run the command-line prediction app with values in the training ranges:

```cmd
.venv\Scripts\python.exe app.py --days-to-expiry 2 --stock-level 20 --remaining-shelf-life 25 --supplier-score 8 --promoted 0
```

The app displays the predicted fraction as a percentage, for example:

```text
Recommended discount: 38.50%
```

Input rules:

- `days-to-expiry`: zero or greater
- `stock-level`: zero or greater
- `remaining-shelf-life`: `0` to `100`
- `supplier-score`: `6` to `10`
- `promoted`: `0` or `1`

## Run Tests

```cmd
.venv\Scripts\python.exe -m unittest discover -v
```

## Project Files

- `Dynamic_Pricing.ipynb`: exploratory analysis and model comparison
- `train_model.ipynb`: final XGBoost training and evaluation
- `pricing_model.pkl`: saved trained model
- `pricing_model.py`: validated prediction function
- `app.py`: command-line prediction interface
- `test_model.py`: prediction and input-validation tests
- `database.py`: SQLite inventory database functions
- `seed_database.py`: database seeding utility
- `requirements.txt`: Python dependencies