from cache import load_titles_cached, load_contents_cached, load_course_titles_cached, save_cache
from ai_client import ai_summarize
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 나중에 Vercel 도메인으로 좁히면 더 안전
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
# 3) AI 요청 (prompt만 사용, text는 무시)
# -------------------------
@app.post("/summarize")


@app.post("/summarize")
def summarize_api(data: dict):
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return {"result": "정답:\n해설: 프롬프트가 비어 있습니다."}

    try:
        result = ai_summarize(prompt, "")
        return {"result": result}
    except Exception as e:
        # 🔥 에러를 그대로 프론트로 내려줌
        return {
            "result": f"정답:\n해설: 서버 오류 발생\n{type(e).__name__}: {e}"
        }


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
    import os
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

