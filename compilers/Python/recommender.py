import pandas as pd
from config import W_DURATION, W_COST


def recommend(df, category="All", difficulty="All", language="All", max_cost=None):
    # Elegxos: an to CSV einai keno, den mporoume na kanoume protaseis
    if df.empty:
        return []

    filtered = df.copy()

    if category and category != "All":
        filtered = filtered[filtered["category"] == category]
    if difficulty and difficulty != "All":
        filtered = filtered[filtered["difficulty"] == difficulty]
    if language and language != "All":
        filtered = filtered[filtered["language"].str.lower() == language.lower()]
    if max_cost is not None:
        filtered = filtered[pd.to_numeric(filtered["cost"], errors="coerce").fillna(0) <= max_cost]

    if filtered.empty:
        return []

    filtered = filtered.copy()
    filtered["cost_num"] = pd.to_numeric(filtered["cost"], errors="coerce").fillna(0)
    filtered["dur_num"] = pd.to_numeric(filtered["duration_hours"], errors="coerce")

    # Gia elleipes times diarkias, xrisimopoioume to median wste na min timwrountai ta mathimata
    median_dur = filtered["dur_num"].median()
    filtered["dur_num"] = filtered["dur_num"].fillna(median_dur if not pd.isna(median_dur) else 0)

    dur_max = filtered["dur_num"].max()
    dur_min = filtered["dur_num"].min()
    cost_max = filtered["cost_num"].max()
    cost_min = filtered["cost_num"].min()

    def norm(val, mn, mx):
        # Min-max normalization: vazei oles tis times sto [0, 1]
        if mx == mn:
            return 0.5
        return (val - mn) / (mx - mn)

    # Composite score: megalytero varos sti diarkeia (W_DURATION=0.6), xamilotero sto kostos (W_COST=0.4)
    # To kostos paizetai antistrefa: (1 - norm_cost) wste ta fthina na pairnoune ipsilo score
    filtered["score"] = filtered.apply(
        lambda row: W_DURATION * norm(row["dur_num"], dur_min, dur_max)
                  + W_COST * (1 - norm(row["cost_num"], cost_min, cost_max)),
        axis=1
    )

    top3 = filtered.nlargest(3, "score")
    result_cols = ["title", "provider", "category", "difficulty", "cost", "duration_hours", "language", "score"]
    return top3[result_cols].to_dict("records")
