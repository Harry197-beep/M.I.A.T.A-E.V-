import sqlite3
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


def load_training_data(db_path="miata.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT user_message, tool_used FROM logs")
    rows = cur.fetchall()
    conn.close()

    X = [r[0] for r in rows]
    # Treat missing/empty tool_used as its own class: "none"
    y = [r[1] if r[1] else "none" for r in rows]
    return X, y


def train():
    X, y = load_training_data()

    class_counts = {}
    for label in y:
        class_counts[label] = class_counts.get(label, 0) + 1

    print(f"Training on {len(X)} examples")
    print("Class distribution:", class_counts)

    for label, count in class_counts.items():
        if count < 3:
            print(f"  WARNING: '{label}' only has {count} example(s) - router will be unreliable for this class until more data is collected.")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

    pipeline.fit(X, y)

    joblib.dump(pipeline, "router_model.pkl")
    print("Saved router_model.pkl")

    # Sanity check: predict on the training data itself (not a real eval,
    # just confirms the model learned SOMETHING, not held-out accuracy)
    train_preds = pipeline.predict(X)
    correct = sum(p == actual for p, actual in zip(train_preds, y))
    print(f"Training-set accuracy (not a real generalization metric with this little data): {correct}/{len(y)}")


if __name__ == "__main__":
    train()
