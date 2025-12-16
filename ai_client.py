import os
from openai import OpenAI

API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com/v1"
)

def ai_summarize(prompt: str, text: str) -> str:
    if not API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY 환경 변수가 설정되어 있지 않습니다.")

    prompt = (prompt or "").strip()
    text = (text or "").strip()

    system_instruction = (
        "너는 '공지 요약/정리 도우미'다.\n"
        "사용자 추가 조건이 있으면 그 조건을 최우선으로 따른다.\n"
        "한국어로 출력한다.\n"
        "불필요한 인사말/자기소개/군더더기 설명은 금지한다.\n"
        "형식:\n"
        "요약:\n"
        "- (핵심 3~7줄)\n"
        "필수 정보:\n"
        "- 일정/마감/장소/대상/준비물/링크(있으면)\n"
    )

    # ✅ prompt는 '조건', text는 '공지 본문'
    user_content = f"""[추가 조건]
{prompt if prompt else "없음"}

[공지 본문]
{text if text else "(본문이 비어 있습니다)"}"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
