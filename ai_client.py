import base64
import os
from typing import Optional

from openai import OpenAI


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")
OPENAI_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "medium")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

SYSTEM_INSTRUCTION = """
너는 'AI 문제 풀이 및 해설 도우미'다.

사용자는 텍스트만 보낼 수도 있고, 이미지 문제만 보낼 수도 있고,
텍스트 지시문과 이미지 문제를 함께 보낼 수도 있다.

가장 중요한 규칙:
- 텍스트와 이미지가 함께 제공되면, 둘 중 하나만 보고 답하지 말고 반드시 함께 해석한다.
- 사용자의 텍스트는 이미지 문제를 해석하기 위한 조건, 범위, 풀이 방식, 추가 지시문이다.
- 사용자가 "3번만", "이 부분만", "오류 찾아줘", "라그랑주 승수로", "정답만"처럼 지시하면 그 지시를 최우선으로 따른다.
- 이미지에 여러 문제가 있어도, 사용자가 특정 번호나 범위를 지정했다면 지정된 것만 푼다.
- 사용자가 특정 번호나 범위를 지정하지 않았을 때만 이미지 속 여러 문제를 번호별로 푼다.
- 이미지 속 글자가 흐리거나 일부가 보이지 않으면 추측하지 말고, 보이지 않는 부분을 말한 뒤 가능한 범위에서 풀이한다.

반드시 아래 형식으로만 답한다.
정답: ...
해설: ...

규칙:
- 객관식이면 정답 번호/문자를 먼저 쓴다.
- 주관식이면 결론을 한 문장으로 먼저 쓴다.
- 수학/과학/언어/철학/코딩 문제는 핵심 풀이 과정을 간결하게 설명한다.
- 사용자가 '정답만'을 요구하면 해설을 생략한다.
- 불필요한 인사말, 자기소개, 사족은 금지한다.
- 정답을 확신할 수 없으면 '추정 정답'이라고 표시하고 이유를 설명한다.
""".strip()


def _ensure_client() -> OpenAI:
    if client is None or not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
    return client


def _image_to_data_url(image_bytes: bytes, mime_type: Optional[str]) -> str:
    mime = mime_type or "image/png"
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _extract_output_text(response) -> str:
    """OpenAI SDK 버전에 따라 output_text가 없을 수 있어 보수적으로 추출한다."""
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text.strip()

    chunks = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    return "\n".join(chunks).strip()


def ai_solve(
    prompt: str = "",
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
) -> str:
    """
    텍스트 문제와 선택적 이미지 문제를 OpenAI Responses API로 풀이한다.
    """
    openai_client = _ensure_client()

    prompt = (prompt or "").strip()
    if not prompt and not image_bytes:
        return "정답:\n해설: 프롬프트나 이미지가 비어 있습니다."

    if not prompt:
        prompt = "이미지 속 문제를 읽고 정답과 해설 형식으로 풀어줘."

    fusion_prompt = f"""
    아래에는 사용자의 텍스트 지시문과 첨부 이미지가 함께 제공된다.
    
    반드시 다음 순서로 처리해라.
    1. 첨부 이미지 속 문제를 읽는다.
    2. 사용자 텍스트 지시문이 이미지의 어느 부분을 가리키는지 해석한다.
    3. 사용자 텍스트가 지정한 번호, 범위, 조건, 풀이 방식만 적용한다.
    4. 이미지와 텍스트를 결합한 최종 문제에 대해서만 정답과 해설을 출력한다.
    
    중요:
    - 텍스트 지시문을 무시하지 마라.
    - 이미지 전체를 무조건 다 풀지 마라.
    - 사용자가 특정 번호를 말했으면 그 번호만 풀어라.
    - 사용자가 풀이 방식을 지정했으면 그 방식으로 풀어라.
    
    [사용자 텍스트 지시문]
    {prompt}
    """.strip()
    
    content = [{"type": "input_text", "text": fusion_prompt}]

    if image_bytes:
        content.append(
            {
                "type": "input_image",
                "image_url": _image_to_data_url(image_bytes, mime_type),
                "detail": "auto",
            }
        )

    request_kwargs = {
        "model": OPENAI_MODEL,
        "instructions": SYSTEM_INSTRUCTION,
        "input": [
            {
                "role": "user",
                "content": content,
            }
        ],
    }

    # GPT-5 계열은 reasoning effort를 지원한다. 다른 모델로 바꿔도 실패하면 reasoning 없이 재시도한다.
    if OPENAI_REASONING_EFFORT:
        request_kwargs["reasoning"] = {"effort": OPENAI_REASONING_EFFORT}

    try:
        response = openai_client.responses.create(**request_kwargs)
    except TypeError:
        # 구버전 SDK가 reasoning 인자를 모르는 경우
        request_kwargs.pop("reasoning", None)
        response = openai_client.responses.create(**request_kwargs)
    except Exception as error:
        # 다른 모델로 바꿨을 때 reasoning 파라미터를 거부하면 reasoning 없이 한 번 재시도
        if "reasoning" in str(error).lower() and "reasoning" in request_kwargs:
            request_kwargs.pop("reasoning", None)
            response = openai_client.responses.create(**request_kwargs)
        else:
            raise

    result = _extract_output_text(response)
    if not result:
        return "정답:\n해설: AI 응답이 비어 있습니다."

    if not result.lstrip().startswith("정답:"):
        result = "정답:\n해설: " + result

    return result


def ai_summarize(prompt: str, text: str = "") -> str:
    """
    기존 /summarize 엔드포인트와 호환되는 함수.
    text는 현재 서비스 구조상 사용하지 않는다.
    """
    return ai_solve(prompt=prompt)
