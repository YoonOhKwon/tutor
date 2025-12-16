import os
from openai import OpenAI

API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com/v1"
)

def ai_summarize(prompt: str, text: str) -> str:
    """
    prompt: 사용자가 입력한 문제/질문 (이것만 사용)
    text: (공지 본문 등) 무시됨
    """
    if not API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY 환경 변수가 설정되어 있지 않습니다.")

    system_instruction = (
        "너는 'AI 문제 풀이 및 해설 도우미'다.\n"
        "사용자가 제시한 문제(질문)에 대해 정답을 먼저 제시하고, 이어서 핵심 근거/풀이를 간결하게 설명한다.\n"
        "객관식이면 정답 번호/문자를, 주관식이면 결론을 한 문장으로 먼저 말한다.\n"
        "사용자 추가 조건(prompt)이 있으면 그 조건을 최우선으로 따른다.\n"
        "불확실하면 지어내지 말고, 부족한 정보가 무엇인지 말한 뒤 가능한 범위에서 설명한다.\n"
        "출력 형식:\n"
        "정답: ...\n"
        "해설: ...\n"
        "단, 사용자가 '정답만'을 요구하면 해설을 생략한다.\n"
        "불필요한 인사말/자기소개는 금지한다.\n"
    )

    # ✅ 공지본문(text) 무시하고 prompt만 보냄
    user_content = prompt

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
