from cache import load_titles_cached, load_contents_cached, load_course_titles_cached, save_cache
from ai_client import ai_summarize
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import FileResponse


app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/download/uploader")
def download_uploader():
    file_path = "hufsmate_uploader.exe"
    return FileResponse(
        path=file_path,
        filename="hufsmate_uploader.exe",
        media_type="application/octet-stream"
    )


# -------------------------
# 1) 로컬 크롤링 JSON → 서버로 업로드
# -------------------------
@app.post("/upload-cache")
def upload_cache(data: dict):
    titles = data["titles"]
    contents = data["contents"]
    courses = data["courses"]

    # 저장
    save_cache(titles, contents, courses)

    return {"status": "ok", "message": "캐시 업로드 완료"}

# -------------------------
# 2) 공지 조회
# -------------------------
@app.get("/notices")
def get_notices():
    titles = load_titles_cached()
    contents = load_contents_cached()
    courses = load_course_titles_cached()

    return {
        "titles": titles,
        "contents": contents,
        "courses": courses
    }

# -------------------------
# 3) AI 요청
# -------------------------
@app.post("/summarize")
def summarize_api(data: dict):
    notice = data["text"]
    prompt = data.get("prompt", "요약해줘")
    result = ai_summarize(prompt, notice)
    return {"result": result}

# -------------------------
# 4) 서버 캐시 갱신 버튼은 의미 없음
# -------------------------
@app.post("/refresh-cache")
def refresh_cache():
    return {
        "status": "local_only",
        "message": "캐시 갱신은 로컬 크롤링 후 업로드해야 합니다."
    }

# -------------------------
# 5) 서버 실행
# -------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

