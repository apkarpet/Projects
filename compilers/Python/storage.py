import pandas as pd
import os
from config import CSV_FILE, CSV_COLUMNS, log


def load_csv():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=CSV_COLUMNS)
    try:
        df = pd.read_csv(CSV_FILE)
        # Diasfalyzoume oti exoume oles tis aparaithtes sthles, akoma kai an to arxeio einai palaio
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[CSV_COLUMNS]
    except Exception as e:
        log("Storage", "Error", str(e))
        return pd.DataFrame(columns=CSV_COLUMNS)


def save_courses(new_courses):
    if not new_courses:
        return
    # Fortwnw ta palia kai prosthetw ta nea se append mode, xwris na xanw palia dedomena
    df_old = load_csv()
    df_new = pd.DataFrame(new_courses)
    for col in CSV_COLUMNS:
        if col not in df_new.columns:
            df_new[col] = ""
    df_new = df_new[CSV_COLUMNS]
    df_combined = pd.concat([df_old, df_new], ignore_index=True).infer_objects(copy=False)
    # Afairoume diplotypa me vasi titlo + paro3o, kratame to pio prosfato
    df_combined = df_combined.drop_duplicates(subset=["title", "provider"], keep="last")
    df_combined.to_csv(CSV_FILE, index=False)
    log("Storage", "Success", f"{len(df_new)} nea, {len(df_combined)} synola sto {CSV_FILE}")


def export_csv(filepath):
    df = load_csv()
    df.to_csv(filepath, index=False)
    log("Export", "Success", filepath)
