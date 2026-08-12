import joblib

model = joblib.load("router_model.pkl")

test_cases = [
    ("search my gmail for invoices", "search_gmail"),
    ("what's on my calendar tomorrow", "get_calendar_events"),
    ("search the web for bitcoin price", "web_search"),
    ("hey what's up", "none"),
]

for msg, expected in test_cases:
    proba = model.predict_proba([msg])[0]
    classes = model.classes_
    ranked = sorted(zip(classes, proba), key=lambda x: -x[1])
    top_label, top_conf = ranked[0]
    correct = "✓" if top_label == expected else "✗"
    print(f"{correct} '{msg}'")
    print(f"   expected: {expected}")
    for label, conf in ranked[:3]:
        print(f"   {label}: {conf:.3f}")
    print()
