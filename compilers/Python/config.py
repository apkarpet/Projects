STUDENT_NAME = "Kandilas Giorgos"
AM = "1115510"
CSV_FILE = f"courses_{AM}.csv"

CSV_COLUMNS = [
    "title", "provider", "category", "difficulty",
    "cost", "duration_hours", "language", "source", "fetched_at"
]

CATEGORIES = ["All", "Programming", "Data Science", "Web Development",
              "Mathematics", "Business", "Languages", "Other"]
DIFFICULTIES = ["All", "Beginner", "Intermediate", "Advanced"]
LANGUAGES = ["All", "English", "Greek", "French", "Spanish", "German"]

# Varh gia ton algorithmo systaeon:
# Diarkeia paei 0.6 giati pio poli yliko = kalyteri ekpaideysi.
# Kostos paei 0.4 wste na prooimountai ta fthina/dwrean otan oi diarkies einai paromies.
W_DURATION = 0.6
W_COST = 0.4

SCHEDULER_INTERVAL_HOURS = 6


def log(source, status, detail=""):
    msg = f"[{source}] Status: {status}"
    if detail:
        msg += f" — {detail}"
    print(msg)
