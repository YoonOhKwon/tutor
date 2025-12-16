import json
import os


# ---------------------------
# 캐시 저장 함수
# ---------------------------
def save_cache(titles, contents, course_titles):
    with open("cache_titles.json", "w", encoding="utf-8") as f:
        json.dump(titles, f, ensure_ascii=False, indent=2)

    with open("cache_contents.json", "w", encoding="utf-8") as f:
        json.dump(contents, f, ensure_ascii=False, indent=2)

    with open("cache_course_titles.json", "w", encoding="utf-8") as f:
        json.dump(course_titles, f, ensure_ascii=False, indent=2)


# ---------------------------
# 캐시 로드 (파일이 있을 때만)
# ---------------------------
def load_titles_cached():
    if os.path.exists("cache_titles.json"):
        with open("cache_titles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_contents_cached():
    if os.path.exists("cache_contents.json"):
        with open("cache_contents.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_course_titles_cached():
    if os.path.exists("cache_course_titles.json"):
        with open("cache_course_titles.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []
