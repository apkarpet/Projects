import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from normalizer import normalize_category, normalize_difficulty, normalize_language
from config import log

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def _course(title, provider, category, difficulty, cost, duration, language, source):
    return {
        "title": str(title).strip(),
        "provider": str(provider).strip(),
        "category": normalize_category(category),
        "difficulty": normalize_difficulty(difficulty),
        "cost": float(cost) if cost else 0.0,
        "duration_hours": float(duration) if duration else 0.0,
        "language": normalize_language(language),
        "source": source,
        "fetched_at": datetime.now().isoformat()
    }


def _parse_hours(text):
    # Βγάζουμε τον πρώτο αριθμό από κείμενο όπως "3-5 hours/week" ή "10 hours"
    nums = re.findall(r'\d+\.?\d*', str(text))
    return float(nums[0]) if nums else 0.0


# ======================== API 1: Coursera ========================
# Public REST API, δεν χρειάζεται authentication

_COURSERA_FALLBACK = [
    _course("Python for Everybody", "University of Michigan", "programming", "beginner", 0, 36, "English", "Coursera-API"),
    _course("Machine Learning Specialization", "Stanford University", "machine learning", "advanced", 49, 60, "English", "Coursera-API"),
    _course("IBM Data Science Professional Certificate", "IBM", "data science", "beginner", 39, 130, "English", "Coursera-API"),
    _course("Deep Learning Specialization", "DeepLearning.AI", "deep learning", "advanced", 49, 80, "English", "Coursera-API"),
]


def fetch_coursera():
    url = "https://api.coursera.org/api/courses.v1"
    params = {"fields": "name,workload,primaryLanguages", "limit": 20}
    try:
        r = requests.get(url, params=params, timeout=10, headers=HEADERS)
        r.raise_for_status()
        items = r.json().get("elements", [])
        if not items:
            raise ValueError("empty response")
        courses = []
        for item in items:
            name = item.get("name", "Unknown Course")
            workload = item.get("workload", "10")
            langs = item.get("primaryLanguages", ["en"])
            lang = "English" if not langs or langs[0] == "en" else langs[0]
            hours = _parse_hours(workload)
            courses.append(_course(name, "Coursera", "programming", "intermediate", 0, hours, lang, "Coursera-API"))
        log("Coursera-API", "Success", f"{len(courses)} μαθήματα")
        return courses
    except Exception as e:
        log("Coursera-API", "Fallback", str(e))
        return _COURSERA_FALLBACK


# ======================== API 2: iTunes Search ========================
# Δωρεάν public API, επιστρέφει educational podcasts/courses

_ITUNES_FALLBACK = [
    _course("CS50: Intro to Computer Science", "Harvard", "computer science", "beginner", 0, 25, "English", "iTunes-API"),
    _course("Swift Programming Full Course", "Apple Education", "programming", "intermediate", 0, 15, "English", "iTunes-API"),
    _course("Data Science Fundamentals", "MIT OpenLearning", "data science", "beginner", 0, 20, "English", "iTunes-API"),
    _course("Intro to Web Development", "FreeCodeCamp", "web development", "beginner", 0, 18, "English", "iTunes-API"),
]


def fetch_itunes():
    url = "https://itunes.apple.com/search"
    params = {"term": "programming tutorial course", "entity": "podcast", "limit": 20, "country": "US"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            raise ValueError("empty response")
        courses = []
        for item in results[:15]:
            title = item.get("trackName", "Unknown")
            provider = item.get("artistName", "Unknown")
            genre = item.get("primaryGenreName", "Education")
            price = float(item.get("collectionPrice") or 0)
            # Μιλισεκόντα → ώρες (proxy εκτίμηση διάρκειας podcast)
            ms = item.get("trackTimeMillis") or 0
            hours = round(ms / 3_600_000, 1) if ms else 5.0
            courses.append(_course(title, provider, genre, "beginner", price, hours, "English", "iTunes-API"))
        log("iTunes-API", "Success", f"{len(courses)} μαθήματα")
        return courses
    except Exception as e:
        log("iTunes-API", "Fallback", str(e))
        return _ITUNES_FALLBACK


# ======================== API 3: GitHub Search ========================
# 60 requests/ώρα χωρίς auth, αρκετό για demo

_GITHUB_FALLBACK = [
    _course("Python Course Repository", "trekhleb", "programming", "intermediate", 0, 40, "English", "GitHub-API"),
    _course("The Algorithms - Python", "TheAlgorithms", "algorithms", "intermediate", 0, 60, "English", "GitHub-API"),
    _course("Coding Interview University", "jwasham", "computer science", "advanced", 0, 100, "English", "GitHub-API"),
    _course("JavaScript Algorithms", "trekhleb", "javascript", "intermediate", 0, 50, "English", "GitHub-API"),
]


def fetch_github():
    url = "https://api.github.com/search/repositories"
    params = {"q": "topic:course topic:tutorial language:python", "sort": "stars", "per_page": 15}
    try:
        r = requests.get(url, params=params, timeout=10, headers=HEADERS)
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            raise ValueError("empty response")
        courses = []
        for item in items:
            title = item.get("name", "Unknown").replace("-", " ").title()
            provider = item.get("owner", {}).get("login", "GitHub")
            topics = item.get("topics", [])
            category = _github_category(topics)
            # Stars ως proxy για δημοτικότητα/μέγεθος μαθήματος, cap στα 200h
            stars = item.get("stargazers_count", 0)
            hours = min(round(stars / 500), 200)
            courses.append(_course(title, provider, category, "intermediate", 0, hours, "English", "GitHub-API"))
        log("GitHub-API", "Success", f"{len(courses)} μαθήματα")
        return courses
    except Exception as e:
        log("GitHub-API", "Fallback", str(e))
        return _GITHUB_FALLBACK


def _github_category(topics):
    # Προτεραιότητα: πιο ειδικά topics πρώτα
    priority = [
        "machine-learning", "deep-learning", "data-science",
        "web-development", "javascript", "html", "css",
        "algorithms", "mathematics", "python", "programming"
    ]
    for p in priority:
        if p in topics:
            return p.replace("-", " ")
    return "programming"


# ======================== Scraper 1: W3Schools ========================
# Static HTML, το parse είναι πολύ reliable

_W3SCHOOLS_FALLBACK = [
    _course("HTML Tutorial", "W3Schools", "html", "beginner", 0, 8, "English", "W3Schools-Scraper"),
    _course("Python Tutorial", "W3Schools", "python", "beginner", 0, 12, "English", "W3Schools-Scraper"),
    _course("JavaScript Tutorial", "W3Schools", "javascript", "beginner", 0, 15, "English", "W3Schools-Scraper"),
    _course("SQL Tutorial", "W3Schools", "data science", "beginner", 0, 10, "English", "W3Schools-Scraper"),
    _course("CSS Tutorial", "W3Schools", "css", "beginner", 0, 8, "English", "W3Schools-Scraper"),
]


def scrape_w3schools():
    url = "https://www.w3schools.com/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        courses = []
        seen = set()
        # Ψάχνουμε συνδέσμους που περιέχουν "Tutorial" στο nav
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True)
            href = link["href"]
            if "Tutorial" in text and href.startswith("/") and text not in seen:
                seen.add(text)
                cat = text.replace(" Tutorial", "").lower().strip()
                courses.append(_course(text, "W3Schools", cat, "beginner", 0, 10, "English", "W3Schools-Scraper"))
            if len(courses) >= 12:
                break
        if not courses:
            raise ValueError("δεν βρέθηκαν tutorial links")
        log("W3Schools-Scraper", "Success", f"{len(courses)} μαθήματα")
        return courses
    except Exception as e:
        log("W3Schools-Scraper", "Fallback", str(e))
        return _W3SCHOOLS_FALLBACK


# ======================== Scraper 2: Open Yale Courses ========================
# Επιλέχθηκε γιατί είναι παλιό Drupal site (server-side rendering), ακαδημαϊκή πηγή,
# χωρίς anti-scraping protection. MIT OCW και OpenLearn απορρίφθηκαν (React SPA και 403).

_YALE_FALLBACK = [
    _course("Frontiers and Controversies in Astrophysics", "Yale University", "mathematics", "intermediate", 0, 25, "English", "YaleOCW-Scraper"),
    _course("Introduction to Political Philosophy", "Yale University", "other", "beginner", 0, 25, "English", "YaleOCW-Scraper"),
    _course("Financial Theory", "Yale University", "business", "advanced", 0, 26, "English", "YaleOCW-Scraper"),
    _course("Introduction to the Old Testament", "Yale University", "other", "beginner", 0, 24, "English", "YaleOCW-Scraper"),
    _course("Fundamentals of Physics", "Yale University", "mathematics", "intermediate", 0, 24, "English", "YaleOCW-Scraper"),
]


def scrape_open_yale():
    # oyc.yale.edu: παλιό Drupal views site — η σελίδα /courses επιστρέφει πλήρες static HTML.
    # Τα course links έχουν μορφή /{department}/{course-code} (2-level path).
    url = "https://oyc.yale.edu/courses"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        courses = []
        seen = set()

        # Strategy 1: headings μέσα στο course listing
        for el in soup.find_all(["h3", "h4", "h2"]):
            text = el.get_text(strip=True)
            if len(text) > 8 and text not in seen:
                skip_words = ["yale", "open", "search", "home", "about", "contact", "menu", "login"]
                if not any(w in text.lower() for w in skip_words):
                    # Εξάγουμε dept από το parent link για καλύτερο category mapping
                    parent = el.find_parent("a") or el.find("a")
                    dept = parent["href"].strip("/").split("/")[0] if parent and parent.get("href") else "other"
                    seen.add(text)
                    courses.append(_course(text, "Yale University", dept.replace("-", " "), "intermediate", 0, 25, "English", "YaleOCW-Scraper"))
            if len(courses) >= 12:
                break

        # Strategy 2: links με 2-level path (/{dept}/{course-slug}) αν δεν βρέθηκαν headings
        if not courses:
            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)
                parts = href.strip("/").split("/")
                if len(parts) == 2 and len(text) > 8 and text not in seen:
                    if not any(x in href for x in ["#", "mailto:", "http", "login", "register"]):
                        dept = parts[0]
                        seen.add(text)
                        courses.append(_course(text, "Yale University", dept.replace("-", " "), "intermediate", 0, 25, "English", "YaleOCW-Scraper"))
                if len(courses) >= 12:
                    break

        if not courses:
            raise ValueError("δεν βρέθηκαν courses")
        log("YaleOCW-Scraper", "Success", f"{len(courses)} μαθήματα")
        return courses
    except Exception as e:
        log("YaleOCW-Scraper", "Fallback", str(e))
        return _YALE_FALLBACK


# ======================== Scraper 3: TutorialsPoint ========================

_TUTORIALSPOINT_FALLBACK = [
    _course("Data Structures & Algorithms Tutorial", "TutorialsPoint", "data structures", "intermediate", 0, 20, "English", "TutorialsPoint-Scraper"),
    _course("Python Tutorial", "TutorialsPoint", "python", "beginner", 0, 15, "English", "TutorialsPoint-Scraper"),
    _course("Machine Learning Tutorial", "TutorialsPoint", "machine learning", "intermediate", 0, 25, "English", "TutorialsPoint-Scraper"),
    _course("Web Development Tutorial", "TutorialsPoint", "web development", "beginner", 0, 18, "English", "TutorialsPoint-Scraper"),
]


def scrape_tutorialspoint():
    url = "https://www.tutorialspoint.com/tutorialslibrary.htm"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        courses = []
        seen = set()
        # Τα tutorials έχουν links με μορφή /topic/index.htm
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if "/index.htm" in href and len(text) > 3 and text not in seen:
                seen.add(text)
                cat = text.lower().strip()
                courses.append(_course(f"{text} Tutorial", "TutorialsPoint", cat, "beginner", 0, 12, "English", "TutorialsPoint-Scraper"))
            if len(courses) >= 12:
                break
        if not courses:
            raise ValueError("δεν βρέθηκαν tutorial links")
        log("TutorialsPoint-Scraper", "Success", f"{len(courses)} μαθήματα")
        return courses
    except Exception as e:
        log("TutorialsPoint-Scraper", "Fallback", str(e))
        return _TUTORIALSPOINT_FALLBACK


def collect_all():
    all_courses = []
    for fn in [fetch_coursera, fetch_itunes, fetch_github,
               scrape_w3schools, scrape_open_yale, scrape_tutorialspoint]:
        all_courses.extend(fn())
    return all_courses
