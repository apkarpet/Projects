# Xartis antistoixisis: onomata apo tis piges → enopoiimenes katigories tis efarmogis
CATEGORY_MAP = {
    "computer science": "Programming",
    "computer-science": "Programming",
    "cs": "Programming",
    "programming": "Programming",
    "python": "Programming",
    "java": "Programming",
    "c++": "Programming",
    "software engineering": "Programming",
    "software development": "Programming",
    "algorithms": "Programming",
    "data structures": "Programming",
    "machine learning": "Data Science",
    "data science": "Data Science",
    "data analysis": "Data Science",
    "data-analysis": "Data Science",
    "artificial intelligence": "Data Science",
    "ai": "Data Science",
    "deep learning": "Data Science",
    "statistics": "Data Science",
    "web development": "Web Development",
    "web design": "Web Development",
    "frontend": "Web Development",
    "backend": "Web Development",
    "back-end": "Web Development",
    "html": "Web Development",
    "css": "Web Development",
    "javascript": "Web Development",
    "js": "Web Development",
    "react": "Web Development",
    "mathematics": "Mathematics",
    "math": "Mathematics",
    "calculus": "Mathematics",
    "linear algebra": "Mathematics",
    "discrete mathematics": "Mathematics",
    "business": "Business",
    "management": "Business",
    "entrepreneurship": "Business",
    "marketing": "Business",
    "finance": "Business",
    "english": "Languages",
    "french": "Languages",
    "spanish": "Languages",
    "german": "Languages",
    "greek": "Languages",
    "language learning": "Languages",
}

DIFFICULTY_MAP = {
    "beginner": "Beginner",
    "introductory": "Beginner",
    "introductory level": "Beginner",
    "basic": "Beginner",
    "easy": "Beginner",
    "novice": "Beginner",
    "entry": "Beginner",
    "entry level": "Beginner",
    "entry-level": "Beginner",
    "starter": "Beginner",
    "introduction": "Beginner",
    "intro": "Beginner",
    "intermediate": "Intermediate",
    "medium": "Intermediate",
    "moderate": "Intermediate",
    "mixed": "Intermediate",
    "advanced": "Advanced",
    "expert": "Advanced",
    "hard": "Advanced",
    "difficult": "Advanced",
    "professional": "Advanced",
    "senior": "Advanced",
}


def normalize_category(raw):
    if not raw:
        return "Other"
    key = str(raw).lower().strip()
    if key in CATEGORY_MAP:
        return CATEGORY_MAP[key]
    # An den yparxei exact match, psaxnoume an kapoio keyword periezetai mesa sto key
    for k, v in CATEGORY_MAP.items():
        if k in key:
            return v
    return "Other"


def normalize_difficulty(raw):
    if not raw:
        return "Beginner"
    key = str(raw).lower().strip()
    if key in DIFFICULTY_MAP:
        return DIFFICULTY_MAP[key]
    for k, v in DIFFICULTY_MAP.items():
        if k in key:
            return v
    return "Beginner"
