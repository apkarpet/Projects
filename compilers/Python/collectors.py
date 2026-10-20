import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from normalizer import normalize_category, normalize_difficulty
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
        "language": str(language).strip() if language else "English",
        "source": source,
        "fetched_at": datetime.now().isoformat()
    }


def _parse_hours(text):
    # Vgazoume ton prwto arithmo apo keimeno opws "3-5 hours/week" i "10 hours"
    nums = re.findall(r'\d+\.?\d*', str(text))
    return float(nums[0]) if nums else 0.0


# ======================== API 1: Coursera ========================
# Public REST API, den xreiazetai authentication

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
        log("Coursera-API", "Success", f"{len(courses)} mathimata")
        return courses
    except Exception as e:
        log("Coursera-API", "Fallback", str(e))
        return _COURSERA_FALLBACK


# ======================== API 2: iTunes Search ========================
# Dwrean public API, epistrefei educational podcasts/courses

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
            # Milisekonda → wres (proxy ektimisi diarkias podcast)
            ms = item.get("trackTimeMillis") or 0
            hours = round(ms / 3_600_000, 1) if ms else 5.0
            courses.append(_course(title, provider, genre, "beginner", price, hours, "English", "iTunes-API"))
        log("iTunes-API", "Success", f"{len(courses)} mathimata")
        return courses
    except Exception as e:
        log("iTunes-API", "Fallback", str(e))
        return _ITUNES_FALLBACK


# ======================== API 3: GitHub Search ========================
# 60 requests/wra xwris auth, arketo gia demo

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
            # Stars ws proxy gia dhmotikotita/megethos mathimatos, cap sta 200h
            stars = item.get("stargazers_count", 0)
            hours = min(round(stars / 500), 200)
            courses.append(_course(title, provider, category, "intermediate", 0, hours, "English", "GitHub-API"))
        log("GitHub-API", "Success", f"{len(courses)} mathimata")
        return courses
    except Exception as e:
        log("GitHub-API", "Fallback", str(e))
        return _GITHUB_FALLBACK


def _github_category(topics):
    # Proteraiothta: pio eidiki topics prwta
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
# Static HTML, to parse einai poli reliable

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
        # Psaxnoume syndesous pou periexoun "Tutorial" sti nav
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
            raise ValueError("den vrethikan tutorial links")
        log("W3Schools-Scraper", "Success", f"{len(courses)} mathimata")
        return courses
    except Exception as e:
        log("W3Schools-Scraper", "Fallback", str(e))
        return _W3SCHOOLS_FALLBACK


# ======================== Scraper 2: MIT OpenCourseWare ========================

_MIT_FALLBACK = [
    _course("Introduction to Computer Science and Programming", "MIT", "computer science", "beginner", 0, 33, "English", "MIT-OCW-Scraper"),
    _course("Mathematics for Computer Science", "MIT", "mathematics", "intermediate", 0, 40, "English", "MIT-OCW-Scraper"),
    _course("Introduction to Algorithms", "MIT", "algorithms", "advanced", 0, 45, "English", "MIT-OCW-Scraper"),
    _course("Linear Algebra", "MIT", "linear algebra", "intermediate", 0, 35, "English", "MIT-OCW-Scraper"),
]


def scrape_mit_ocw():
    url = "https://ocw.mit.edu/search/?d=Computer+Science&s=department_course_numbers.sort_coursenum"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        courses = []
        # Dokimazume na vroume course cards - an to site einai JS-rendered, tha pame se fallback
        cards = soup.find_all("div", class_=re.compile(r"course-info|card|search-result|learning-resource", re.I))
        if not cards:
            # Allh prostasi: oi titloi syxna einai se h2/h3 me sigkekrimeno class
            cards = soup.find_all(["h2", "h3"], class_=re.compile(r"title|course", re.I))
        for card in cards[:10]:
            title_el = card if card.name in ["h2", "h3"] else card.find(["h2", "h3", "h4", "a"])
            if title_el:
                title = title_el.get_text(strip=True)
                if len(title) > 5:
                    courses.append(_course(title, "MIT OpenCourseWare", "computer science", "intermediate", 0, 30, "English", "MIT-OCW-Scraper"))
        if not courses:
            raise ValueError("den vrethikan course elements (pitheanos JS rendering)")
        log("MIT-OCW-Scraper", "Success", f"{len(courses)} mathimata")
        return courses
    except Exception as e:
        log("MIT-OCW-Scraper", "Fallback", str(e))
        return _MIT_FALLBACK


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
        # Ta tutorials exoun links me morfi /topic/index.htm
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
            raise ValueError("den vrethikan tutorial links")
        log("TutorialsPoint-Scraper", "Success", f"{len(courses)} mathimata")
        return courses
    except Exception as e:
        log("TutorialsPoint-Scraper", "Fallback", str(e))
        return _TUTORIALSPOINT_FALLBACK


def collect_all():
    all_courses = []
    for fn in [fetch_coursera, fetch_itunes, fetch_github,
               scrape_w3schools, scrape_mit_ocw, scrape_tutorialspoint]:
        all_courses.extend(fn())
    return all_courses
