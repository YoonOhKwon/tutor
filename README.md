# tutor backend

## Railway 환경변수

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.5
OPENAI_REASONING_EFFORT=medium
MAX_IMAGE_MB=10
CORS_ALLOW_ORIGINS=*
```

배포 후 프론트의 `API_BASE`가 Railway 주소와 일치하는지 확인하세요.

## 엔드포인트

- `POST /summarize` : 텍스트 질문 풀이
- `POST /solve-image` : 이미지 문제 풀이
- `GET /health` : 서버 상태 확인
