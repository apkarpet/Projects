import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import pandas as pd

# Python 3.14 καλεί __del__ σε background threads κατά το GC,
# με αποτέλεσμα "main thread is not in main loop" σε Tkinter objects.
# Αυτό είναι γνωστό θέμα Python 3.14 + Tkinter — δεν επηρεάζει λειτουργικότητα.
_real_hook = sys.unraisablehook
def _unraisable_hook(args):
    if isinstance(args.exc_value, RuntimeError) and \
            "main thread is not in main loop" in str(args.exc_value):
        return
    _real_hook(args)
sys.unraisablehook = _unraisable_hook

from config import STUDENTS_NAME, AM, CATEGORIES, DIFFICULTIES, LANGUAGES
from collectors import collect_all
from storage import load_csv, save_courses, export_csv
from recommender import recommend
import charts
from scheduler import AutoRefresher


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Courses App - {STUDENTS_NAME} ({AM})")
        self.geometry("1920x1080")
        self.resizable(True, True)

        self.df = load_csv()
        self._build_ui()
        self._populate_tree(self.df)

    def _build_ui(self):
        self._build_toolbar()
        self._build_filters()
        self._build_table()
        self._build_statusbar()
        self._build_recommender()
        self.scheduler = AutoRefresher(collect_all, self._refresh_table)

    # -------- Toolbar --------

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bd=1, relief=tk.RAISED, pady=3)
        toolbar.pack(fill=tk.X, padx=5, pady=4)

        tk.Button(toolbar, text="Συλλογή Δεδομένων", command=self._collect,
                  bg="#2196F3", fg="white", padx=8).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Ανανέωση Πίνακα", command=self._refresh_table,
                  padx=8).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Εξαγωγή CSV", command=self._export,
                  padx=8).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y, pady=2)

        tk.Button(toolbar, text="Bar Chart", command=self._show_bar, padx=8).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Pie Chart", command=self._show_pie, padx=8).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Line Chart", command=self._show_line, padx=8).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=8, fill=tk.Y, pady=2)

        self.sched_var = tk.BooleanVar(value=False)
        tk.Checkbutton(toolbar, text="Αυτόματη ανανέωση (6h)", variable=self.sched_var,
                       command=self._toggle_scheduler).pack(side=tk.LEFT, padx=4)

    # -------- Filters --------

    def _build_filters(self):
        f = tk.LabelFrame(self, text="Φίλτρα")
        f.pack(fill=tk.X, padx=5, pady=2)

        tk.Label(f, text="Κατηγορία:").grid(row=0, column=0, padx=6, pady=6)
        self.cat_var = tk.StringVar(value="All")
        ttk.Combobox(f, textvariable=self.cat_var, values=CATEGORIES,
                     state="readonly", width=18).grid(row=0, column=1, padx=4)

        tk.Label(f, text="Δυσκολία:").grid(row=0, column=2, padx=6)
        self.diff_var = tk.StringVar(value="All")
        ttk.Combobox(f, textvariable=self.diff_var, values=DIFFICULTIES,
                     state="readonly", width=14).grid(row=0, column=3, padx=4)

        tk.Label(f, text="Μέγιστο Κόστος (€):").grid(row=0, column=4, padx=6)
        self.cost_filter_var = tk.StringVar()
        tk.Entry(f, textvariable=self.cost_filter_var, width=8).grid(row=0, column=5, padx=4)

        tk.Button(f, text="Φιλτράρισε", command=self._apply_filter).grid(row=0, column=6, padx=6)
        tk.Button(f, text="Επαναφορά", command=self._reset_filter).grid(row=0, column=7, padx=4)

    # -------- Table --------

    def _build_table(self):
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=3)

        cols = ["title", "provider", "category", "difficulty", "cost", "duration_hours", "language", "source"]
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=16)

        widths = {"title": 230, "provider": 140, "category": 120, "difficulty": 90,
                  "cost": 65, "duration_hours": 95, "language": 80, "source": 140}
        for col in cols:
            label = col.replace("_", " ").title()
            self.tree.heading(col, text=label)
            self.tree.column(col, width=widths.get(col, 100), anchor=tk.W)

        sy = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        sx = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=sy.set, xscroll=sx.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

    # -------- Status bar --------

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Έτοιμο.")
        tk.Label(self, textvariable=self.status_var, anchor=tk.W,
                 relief=tk.SUNKEN, bd=1).pack(fill=tk.X, padx=5, pady=2)

    # -------- Recommender --------

    def _build_recommender(self):
        rec = tk.LabelFrame(self, text="Μηχανή Συστάσεων - Top 3 Μαθήματα")
        rec.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(rec, text="Κατηγορία:").grid(row=0, column=0, padx=5, pady=5)
        self.rec_cat = tk.StringVar(value="All")
        ttk.Combobox(rec, textvariable=self.rec_cat, values=CATEGORIES,
                     state="readonly", width=16).grid(row=0, column=1, padx=4)

        tk.Label(rec, text="Δυσκολία:").grid(row=0, column=2, padx=5)
        self.rec_diff = tk.StringVar(value="All")
        ttk.Combobox(rec, textvariable=self.rec_diff, values=DIFFICULTIES,
                     state="readonly", width=13).grid(row=0, column=3, padx=4)

        tk.Label(rec, text="Γλώσσα:").grid(row=0, column=4, padx=5)
        self.rec_lang = tk.StringVar(value="All")
        ttk.Combobox(rec, textvariable=self.rec_lang, values=LANGUAGES,
                     state="readonly", width=12).grid(row=0, column=5, padx=4)

        tk.Label(rec, text="Μέγιστο Κόστος:").grid(row=0, column=6, padx=5)
        self.rec_cost = tk.StringVar()
        tk.Entry(rec, textvariable=self.rec_cost, width=7).grid(row=0, column=7, padx=4)

        tk.Button(rec, text="Βρες Top 3", command=self._recommend,
                  bg="#4CAF50", fg="white", padx=8).grid(row=0, column=8, padx=8)

        self.rec_result = tk.Text(rec, height=4, state=tk.DISABLED,
                                  wrap=tk.WORD, font=("Courier", 9))
        self.rec_result.grid(row=1, column=0, columnspan=9, padx=5, pady=5, sticky="ew")
        rec.grid_columnconfigure(9, weight=1)

    # -------- Actions --------

    def _collect(self):
        self.status_var.set("Συλλογή δεδομένων σε εξέλιξη... παρακαλώ περίμενε.")
        self.update_idletasks()
        # Τρέχουμε σε background thread ώστε το GUI να μην παγώνει κατά τη συλλογή
        def worker():
            courses = collect_all()
            save_courses(courses)
            self.after(0, self._refresh_table)

            def update_status():
                self.status_var.set(f"Συλλέχθηκαν {len(courses)} μαθήματα και αποθηκεύτηκαν.")
            self.after(0, update_status)

        threading.Thread(target=worker, daemon=True).start()

    def _refresh_table(self):
        self.df = load_csv()
        self._populate_tree(self.df)
        self.status_var.set(f"Σύνολο {len(self.df)} μαθήματα στο {self.title().split('-')[0].strip()}.")

    def _populate_tree(self, df):
        for row in self.tree.get_children():
            self.tree.delete(row)
        cols = ["title", "provider", "category", "difficulty", "cost", "duration_hours", "language", "source"]
        for _, row in df.iterrows():
            vals = [str(row.get(c, ""))[:60] for c in cols]
            self.tree.insert("", tk.END, values=vals)

    def _apply_filter(self):
        filtered = self.df.copy()
        cat = self.cat_var.get()
        diff = self.diff_var.get()
        cost_str = self.cost_filter_var.get().strip()

        if cat != "All":
            filtered = filtered[filtered["category"] == cat]
        if diff != "All":
            filtered = filtered[filtered["difficulty"] == diff]
        if cost_str:
            try:
                max_c = float(cost_str)
                filtered = filtered[pd.to_numeric(filtered["cost"], errors="coerce").fillna(0) <= max_c]
            except ValueError:
                messagebox.showerror("Λάθος", "Το κόστος πρέπει να είναι αριθμός (π.χ. 49.99)")
                return
        self._populate_tree(filtered)
        self.status_var.set(f"{len(filtered)} μαθήματα μετά το φιλτράρισμα.")

    def _reset_filter(self):
        self.cat_var.set("All")
        self.diff_var.set("All")
        self.cost_filter_var.set("")
        self._populate_tree(self.df)
        self.status_var.set(f"Σύνολο {len(self.df)} μαθήματα.")

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Αποθήκευση CSV"
        )
        if path:
            export_csv(path)
            messagebox.showinfo("Export", f"Αποθηκεύτηκε: {path}")

    def _show_bar(self):
        if self.df.empty:
            messagebox.showwarning("Προσοχή", "Δεν υπάρχουν δεδομένα. Κάντε πρώτα 'Συλλογή Δεδομένων'.")
            return
        charts.bar_top_duration(self.df)

    def _show_pie(self):
        if self.df.empty:
            messagebox.showwarning("Προσοχή", "Δεν υπάρχουν δεδομένα. Κάντε πρώτα 'Συλλογή Δεδομένων'.")
            return
        charts.pie_difficulty(self.df)

    def _show_line(self):
        if self.df.empty:
            messagebox.showwarning("Προσοχή", "Δεν υπάρχουν δεδομένα. Κάντε πρώτα 'Συλλογή Δεδομένων'.")
            return
        charts.line_cost_duration(self.df)

    def _recommend(self):
        if self.df.empty:
            self._set_rec_result("Δεν υπάρχουν δεδομένα. Το CSV είναι κενό - κάντε πρώτα Συλλογή.")
            return
        max_cost = None
        cost_str = self.rec_cost.get().strip()
        if cost_str:
            try:
                max_cost = float(cost_str)
            except ValueError:
                messagebox.showerror("Λάθος", "Εισάγετε αριθμό για το μέγιστο κόστος")
                return
        results = recommend(self.df, self.rec_cat.get(), self.rec_diff.get(), self.rec_lang.get(), max_cost)
        if not results:
            self._set_rec_result("Δεν βρέθηκαν μαθήματα για τα επιλεγμένα κριτήρια.")
        else:
            lines = []
            for i, r in enumerate(results, 1):
                line = (f"#{i}: {r['title']} | {r['provider']} | "
                        f"{r['category']} | {r['difficulty']} | "
                        f"€{r['cost']} | {r['duration_hours']}h | "
                        f"Score: {r['score']:.2f}")
                lines.append(line)
            self._set_rec_result("\n".join(lines))

    def _set_rec_result(self, text):
        self.rec_result.config(state=tk.NORMAL)
        self.rec_result.delete("1.0", tk.END)
        self.rec_result.insert(tk.END, text)
        self.rec_result.config(state=tk.DISABLED)

    def _toggle_scheduler(self):
        if self.sched_var.get():
            self.scheduler.start()
        else:
            self.scheduler.stop()


if __name__ == "__main__":
    app = App()
    app.mainloop()
