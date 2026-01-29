import os
import json
import random
import re
import requests

API_KEY = os.environ.get("UPSTAGE_API_KEY")
if not API_KEY:
    raise SystemExit(
        "UPSTAGE_API_KEY가 설정되지 않았어.\n"
        "터미널에서 아래처럼 먼저 실행해줘:\n"
        "export UPSTAGE_API_KEY=발급받은_키"
    )

TERMS_PATH = "terms.json"

def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    s = s.replace("(", "").replace(")", "")
    return s

def contains_answer(hint: str, term: str) -> bool:
    return normalize(term) in normalize(hint)

def solar_hint(definition: str, term: str, difficulty: str = "medium") -> str:
    diff_guide = {
        "easy": "정의의 핵심을 거의 유지하되 정답 단어만 숨겨라.",
        "medium": "직접적인 표현을 피하고 맥락이나 기능 중심으로 설명해라.",
        "hard": "핵심 단서 2~3개만 제공하고 매우 추상적으로 설명해라."
    }[difficulty]

    prompt = f"""
너는 경제금융 용어 퀴즈의 힌트 생성기다.

[절대 규칙]
- 정답 용어와 그 변형(띄어쓰기, 괄호 제거, 영문 약칭 포함)을 절대 힌트에 포함하지 마라.
- 정의 문장을 그대로 복사하지 마라.
- 힌트는 한국어 한 문장, 40자 이내로 출력해라.
- 힌트 외의 다른 말은 절대 출력하지 마라.

[난이도]
{difficulty.upper()} : {diff_guide}

[정답 용어]
{term}

[정의]
{definition}
""".strip()

    url = "https://api.upstage.ai/v1/solar/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "solar-1-mini-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def main():
    data = json.load(open(TERMS_PATH, "r", encoding="utf-8"))
    item = random.choice(data)

    term = item["term"]
    definition = item["definition"]

    hint = None
    for _ in range(3):
        h = solar_hint(definition, term, difficulty="medium")
        if not contains_answer(h, term):
            hint = h
            break

    if hint is None:
        hint = "힌트 생성 실패(정답 노출)."

    print("=== QUIZ ===")
    print("HINT:", hint)
    print("\nANSWER:", term)

if __name__ == "__main__":
    main()
