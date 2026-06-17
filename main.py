import os

from cache import load_titles_cached, load_contents_cached, load_course_titles_cached, save_cache
from ai_client import ai_summarize, ai_solve
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse


app = FastAPI(title="Tutor API")

# CORS 설정
# 배포 후에는 Railway 환경변수 CORS_ALLOW_ORIGINS에 Vercel 주소를 넣는 것을 권장.
# 예: CORS_ALLOW_ORIGINS=https://your-site.vercel.app,http://localhost:3000
allowed_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_IMAGE_MB = int(os.getenv("MAX_IMAGE_MB", "10"))
MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024


def _error_result(error: Exception) -> dict:
    """프론트가 항상 {result: ...} 형태로 받을 수 있게 에러를 정리한다."""
    message = str(error)
    lower = message.lower()

    if "insufficient balance" in lower or "402" in lower:
        explanation = "AI API 잔액 또는 크레딧이 부족합니다. OpenAI 결제/크레딧과 Railway 환경변수를 확인해주세요."
    elif "api key" in lower or "authentication" in lower or "401" in lower:
        explanation = "AI API 키 인증에 실패했습니다. Railway의 OPENAI_API_KEY 환경변수를 확인해주세요."
    elif "rate limit" in lower or "429" in lower:
        explanation = "AI API 요청 한도에 걸렸습니다. 잠시 후 다시 시도하거나 사용량 제한을 확인해주세요."
    else:
        explanation = f"서버 오류 발생\n{type(error).__name__}: {message}"

    return {"result": f"정답:\n해설: {explanation}"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/download/uploader")
def download_uploader():
    file_path = "hufsmate_uploader.exe"
    return FileResponse(
        path=file_path,
        filename="hufsmate_uploader.exe",
        media_type="application/octet-stream",
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
        "courses": courses,
    }


# -------------------------
# 3) AI 요청: 텍스트 문제
# -------------------------
@app.post("/summarize")
def summarize_api(data: dict):
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return {"result": "정답:\n해설: 프롬프트가 비어 있습니다."}

    try:
        result = ai_summarize(prompt, "")
        return {"result": result}
    except Exception as e:
        return _error_result(e)


# -------------------------
# 3-1) AI 요청: 이미지 문제
# -------------------------
@app.post("/solve-image")
async def solve_image_api(
    prompt: str = Form(""),
    image: UploadFile = File(...),
):
    if not image.content_type or not image.content_type.startswith("image/"):
        return {"result": "정답:\n해설: 이미지 파일만 업로드할 수 있습니다."}

    image_bytes = await image.read()

    if not image_bytes:
        return {"result": "정답:\n해설: 이미지 파일이 비어 있습니다."}

    if len(image_bytes) > MAX_IMAGE_BYTES:
        return {
            "result": f"정답:\n해설: 이미지 용량이 너무 큽니다. {MAX_IMAGE_MB}MB 이하로 줄여주세요."
        }

    try:
        result = ai_solve(
            prompt=prompt,
            image_bytes=image_bytes,
            mime_type=image.content_type,
        )
        return {"result": result}
    except Exception as e:
        return _error_result(e)


# -------------------------
# 4) 서버 캐시 갱신 버튼은 의미 없음
# -------------------------
@app.post("/refresh-cache")
def refresh_cache():
    return {
        "status": "local_only",
        "message": "캐시 갱신은 로컬 크롤링 후 업로드해야 합니다.",
    }


# -------------------------
# 5) 서버 실행
# -------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
