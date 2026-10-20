import matplotlib.pyplot as plt
import pandas as pd


def bar_top_duration(df):
    df_copy = df.copy()
    df_copy["duration_hours"] = pd.to_numeric(df_copy["duration_hours"], errors="coerce").fillna(0)
    top5 = df_copy.nlargest(5, "duration_hours")

    fig, ax = plt.subplots(figsize=(9, 5))
    # Κόβουμε τους τίτλους
    labels = []
    for t in top5["title"]:
        text = str(t)
        if len(text) > 30:
            labels.append(text[:30] + "...")
        else:
            labels.append(text)
    ax.bar(labels, top5["duration_hours"], color="steelblue")
    ax.set_xlabel("Μάθημα")
    ax.set_ylabel("Διάρκεια (ώρες)")
    ax.set_title("Top 5 Μαθήματα με Μεγαλύτερη Διάρκεια")

    # Βάζουμε κλήση στα ονόματα για να μπορούμε να τα διαβάσουμε
    plt.xticks(rotation=20, ha="right", fontsize=9)
    plt.tight_layout()
    plt.show()


def pie_difficulty(df):
    counts = df["difficulty"].value_counts()

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=140,
           colors=["#4CAF50", "#FF9800", "#F44336"])
    ax.set_title("Κατανομή Επιπέδου Δυσκολίας")
    plt.tight_layout()
    plt.show()


def line_cost_duration(df):
    df_copy = df.copy()
    df_copy["duration_hours"] = pd.to_numeric(df_copy["duration_hours"], errors="coerce").fillna(0)
    df_copy["cost"] = pd.to_numeric(df_copy["cost"], errors="coerce").fillna(0)
    # Top 5 σε διάρκεια, ταξινομημένα κατά αύξουσα διάρκεια
    top5 = df_copy.nlargest(5, "duration_hours").sort_values("duration_hours")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(top5["duration_hours"], top5["cost"], marker="o", color="darkorange", linewidth=2, label="Κόστος")
    for _, row in top5.iterrows():
        ax.annotate(str(row["title"])[:20], (row["duration_hours"], row["cost"]),
                    textcoords="offset points", xytext=(5, 5), fontsize=8)
    ax.set_xlabel("Διάρκεια (ώρες)")
    ax.set_ylabel("Κόστος (€)")
    ax.set_title("Σχέση Κόστους και Διάρκειας — Top 5 Μαθήματα")
    ax.legend()
    plt.tight_layout()
    plt.show()
