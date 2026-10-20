import matplotlib.pyplot as plt
import pandas as pd


def bar_top_duration(df):
    df_copy = df.copy()
    df_copy["duration_hours"] = pd.to_numeric(df_copy["duration_hours"], errors="coerce").fillna(0)
    top5 = df_copy.nlargest(5, "duration_hours")

    fig, ax = plt.subplots(figsize=(9, 5))
    # Kovoume tous titlous gia na xwrane ston axona
    labels = [t[:30] + "..." if len(str(t)) > 30 else str(t) for t in top5["title"]]
    ax.bar(labels, top5["duration_hours"], color="steelblue")
    ax.set_xlabel("Mathima")
    ax.set_ylabel("Diarkeia (wres)")
    ax.set_title("Top 5 Mathimata me Megalyteri Diarkeia")
    plt.xticks(rotation=20, ha="right", fontsize=9)
    plt.tight_layout()
    plt.show()


def pie_difficulty(df):
    counts = df["difficulty"].value_counts()

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=140,
           colors=["#4CAF50", "#FF9800", "#F44336"])
    ax.set_title("Katanomi Epipedou Dyskolias")
    plt.tight_layout()
    plt.show()


def line_cost_duration(df):
    df_copy = df.copy()
    df_copy["duration_hours"] = pd.to_numeric(df_copy["duration_hours"], errors="coerce").fillna(0)
    df_copy["cost"] = pd.to_numeric(df_copy["cost"], errors="coerce").fillna(0)
    # Top 5 se diarkeia, taksinomimena kata auksousa diarkeia gia swsth apartiisi grammi
    top5 = df_copy.nlargest(5, "duration_hours").sort_values("duration_hours")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(top5["duration_hours"], top5["cost"], marker="o", color="darkorange", linewidth=2, label="Kostos")
    for _, row in top5.iterrows():
        short = str(row["title"])[:20]
        ax.annotate(short, (row["duration_hours"], row["cost"]),
                    textcoords="offset points", xytext=(5, 5), fontsize=8)
    ax.set_xlabel("Diarkeia (wres)")
    ax.set_ylabel("Kostos (€)")
    ax.set_title("Sxesi Kostous kai Diarkias — Top 5 Mathimata")
    ax.legend()
    plt.tight_layout()
    plt.show()
