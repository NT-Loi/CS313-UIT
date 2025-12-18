from tensorflow.keras.models import load_model
import joblib
import pandas as pd
import numpy as np
import shap

scaler_static = joblib.load('models/scaler_static_final.pkl')
MODEL_PATH = 'models/hybrid_lstm_final_model.keras'
model = load_model(MODEL_PATH)

df_train = pd.read_csv('features/train_bertopic_full (1).csv', dtype={'arxiv_id': str})
df_test = pd.read_csv('features/test_bertopic_full (1).csv', dtype={'arxiv_id': str})
df = pd.concat([df_train, df_test])

if 'arxiv_id' in df.columns:
    df.set_index('arxiv_id', inplace=True)

STATIC_FEATURES = [col for col in df.columns if not col.startswith('citations_')]
TIME_STEPS = 12
START_YEAR_INPUT = 2013
INPUT_CITATION_COLS = [f'citations_{y}' for y in range(START_YEAR_INPUT, START_YEAR_INPUT + TIME_STEPS)]

missing_cols = [c for c in INPUT_CITATION_COLS if c not in df.columns]
if missing_cols:
    print(f"Warning: Missing columns {missing_cols}. Falling back to 2012-2023 range.")
    START_YEAR_INPUT = 2012
    INPUT_CITATION_COLS = [f'citations_{y}' for y in range(START_YEAR_INPUT, START_YEAR_INPUT + TIME_STEPS)]


def predict_next_k_years(arxiv_id: str, k: int = 4) -> dict:
    """
    Predict citations for the next k years for a specific paper.
    
    Args:
        arxiv_id (str): The ID of the paper.
        k (int): Number of years to predict.
    
    Returns:
        dict: Format {year: predicted_citation_count}
    """
    if arxiv_id not in df.index:
        raise ValueError(f"Arxiv ID '{arxiv_id}' not found in the dataset.")

    row = df.loc[[arxiv_id]]

    X_static_raw = row[STATIC_FEATURES].values
    X_static_scaled = scaler_static.transform(X_static_raw)

    current_ts = row[INPUT_CITATION_COLS].values
    current_ts = current_ts[:, :, np.newaxis]

    predictions = {}
    start_prediction_year = START_YEAR_INPUT + TIME_STEPS  # e.g., 2013 + 12 = 2025

    for i in range(k):
        predicting_year = start_prediction_year + i
        
        X_ts_input = current_ts[:, -TIME_STEPS:, :]

        # Predict
        y_pred = model.predict(
            {
                'ts_input': X_ts_input,
                'static_input': X_static_scaled
            },
            verbose=0  # Silent
        ).flatten()[0]

        y_pred = max(0, y_pred)
        
        predictions[f'citations_{predicting_year}'] = float(y_pred)

        new_point = np.array([[[y_pred]]])
        current_ts = np.concatenate([current_ts, new_point], axis=1)

    return predictions

# --- SHAP ---
explainer = None
ALL_FEATURE_NAMES = INPUT_CITATION_COLS + STATIC_FEATURES

def get_attribution(arxiv_id: str):
    """
    Calculate SHAP values for a specific paper.
    """
    global explainer
    if arxiv_id not in df.index:
        raise ValueError(f"Arxiv ID '{arxiv_id}' not found")

    row = df.loc[[arxiv_id]]
    X_static_scaled = scaler_static.transform(row[STATIC_FEATURES].values)
    X_ts = row[INPUT_CITATION_COLS].values
    combined_input = np.concatenate([X_ts, X_static_scaled], axis=1)

    if explainer is None:
        # Background: take a small representative sample
        bg_size = 10 
        bg_sample = df.sample(min(bg_size, len(df)), random_state=42)
        bg_static = scaler_static.transform(bg_sample[STATIC_FEATURES].values)
        bg_ts = bg_sample[INPUT_CITATION_COLS].values
        bg_combined = np.concatenate([bg_ts, bg_static], axis=1)

        def model_predict_flat(x):
            ts = x[:, :12].reshape(-1, 12, 1)
            static = x[:, 12:]
            return model.predict({'ts_input': ts, 'static_input': static}, verbose=0).flatten()

        explainer = shap.KernelExplainer(model_predict_flat, bg_combined)

    # Calculate SHAP values for the one target sample
    shap_vals = explainer.shap_values(combined_input, nsamples=50)
    
    # shap_vals is (1, num_features)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[0]
    
    vals = shap_vals[0]
    
    # Create list of {feature, weight}
    results = []
    for name, val in zip(ALL_FEATURE_NAMES, vals):
        if abs(val) > 1e-5: # filter tiny values
            results.append({"feature": name, "weight": float(val)})

    # Sort and take top 10 by absolute magnitude
    results = sorted(results, key=lambda x: abs(x["weight"]), reverse=True)[:10]
    return results


if __name__ == "__main__":
    example_ids = df.index[:5]
    
    for aid in example_ids:
        print(f"\nPaper: {aid}")
        try:
            preds = predict_next_k_years(aid, k=5)
            print(f"Predictions: {preds}")
        except Exception as e:
            print(f"Error: {e}")