import pandas as pd
from config import W_DURATION, W_COST


def recommend(df, category="All", difficulty="All", language="All", max_cost=None):
    # Έλεγχος: αν το CSV είναι κενό
    if df.empty:
        return []

    filtered = df.copy()

    if category and category != "All":
        # Κράτησε μόνο όσα είναι στο σωστό category
        filtered = filtered[filtered["category"] == category]
    if difficulty and difficulty != "All":
        filtered = filtered[filtered["difficulty"] == difficulty]
    if language and language != "All":
        filtered = filtered[filtered["language"].str.lower() == language.lower()]
    if max_cost is not None:
        # Αν δεν υπάρχει κόστος επιστρέφει NaN, και επιλέγεται
        filtered = filtered[pd.to_numeric(filtered["cost"], errors="coerce").fillna(0) <= max_cost]

    if filtered.empty:
        return []

    filtered = filtered.copy()
    filtered["cost_num"] = pd.to_numeric(filtered["cost"], errors="coerce").fillna(0)
    filtered["dur_num"] = pd.to_numeric(filtered["duration_hours"], errors="coerce")

    # Για ελλιπείς τιμές διάρκειας, χρησιμοποιούμε το median
    median_dur = filtered["dur_num"].median()
    filtered["dur_num"] = filtered["dur_num"].fillna(median_dur if not pd.isna(median_dur) else 0)

    dur_max = filtered["dur_num"].max()
    dur_min = filtered["dur_num"].min()
    cost_max = filtered["cost_num"].max()
    cost_min = filtered["cost_num"].min()

    def norm(val, mn, mx):
        # Min-max normalization: βάζει όλες τις τιμές στο [0, 1]
        if mx == mn:
            return 0.5
        return (val - mn) / (mx - mn)

    # Composite score: μεγαλύτερο βάρος στη διάρκεια (W_DURATION=0.6), χαμηλότερο στο κόστος (W_COST=0.4)
    # Το κόστος: (1 - norm_cost) ώστε τα φθηνά να παίρνουν υψηλό score
    if dur_max != dur_min:
        norm_dur = (filtered["dur_num"] - dur_min) / (dur_max - dur_min)
    else:
        norm_dur = 0.5
    
    if cost_max != cost_min:
        norm_cost = (filtered["cost_num"] - cost_min) / (cost_max - cost_min)
    else:
        norm_cost = 0.5
    filtered["score"] = W_DURATION * norm_dur + W_COST * (1 - norm_cost)

    # Παίρνουμε τα 3 πρώτα με βάση το score 
    top3 = filtered.nlargest(3, "score")
    result_cols = ["title", "provider", "category", "difficulty", "cost", "duration_hours", "language", "score"]
    return top3[result_cols].to_dict("records")
