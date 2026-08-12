import joblib
import os

MODEL_PATH = "router_model.pkl"

_model = None


def load_router():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            return None
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_tool(message, confidence_threshold=0.35):
    """Returns (predicted_tool, confidence) or (None, 0) if router unavailable or unsure."""
    model = load_router()
    if model is None:
        return None, 0.0

    proba = model.predict_proba([message])[0]
    classes = model.classes_
    best_idx = proba.argmax()
    best_label = classes[best_idx]
    best_confidence = proba[best_idx]

    if best_confidence < confidence_threshold:
        return None, best_confidence

    return (best_label if best_label != "none" else None), best_confidence


if __name__ == "__main__":
    test_messages = [
        "search my gmail for invoices",
        "what's on my calendar tomorrow",
        "search the web for bitcoin price",
        "hey what's up",
    ]
    for msg in test_messages:
        tool, conf = predict_tool(msg)
        print(f"'{msg}' -> {tool} (confidence: {conf:.2f})")
