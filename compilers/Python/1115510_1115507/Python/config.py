STUDENTS_NAME = "Κανδήλας Γιώργος, Καρπέτας Απόστολος"
AM = "1115510, 1115507"
CSV_FILE = f"courses_115510_1115507.csv"

CSV_COLUMNS = [
    "title", "provider", "category", "difficulty",
    "cost", "duration_hours", "language", "source", "fetched_at"
]

CATEGORIES = ["All", "Programming", "Data Science", "Web Development",
              "Mathematics", "Business", "Languages", "Other"]
DIFFICULTIES = ["All", "Beginner", "Intermediate", "Advanced", "Other"]
LANGUAGES = ["All", "English", "Greek", "French", "Spanish", "German", "Other"]

# Βάρη για τον αλγόριθμο συστάσεων:
# Διάρκεια πάει 0.6 γιατί πιο πολύ υλικό = καλύτερη εκπαίδευση.
# Κόστος πάει 0.4 ώστε να προτιμούνται τα φθηνά/δωρεάν όταν οι διάρκειες είναι παρόμοιες.
W_DURATION = 0.6
W_COST = 0.4

SCHEDULER_INTERVAL_HOURS = 6


def log(source, status, detail=""):
    msg = f"[{source}] Status: {status}"
    if detail:
        msg += f" - {detail}"
    print(msg)
