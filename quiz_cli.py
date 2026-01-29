import os
import json
import random
import re
import requests

API_KEY = os.environ.get("UPSTAGE_API_KEY")
if not API_KEY:
    raise SystemExit(
        "UPSTAGE_API_KEY가 설정되지 않았어.\n"
        "export UPSTAGE_API_KEY=발급받은_키"
    )

TERMS_PATH = "terms.json"

def norm_answer(s: str) -> str:
    # 사용자 입력/정답 비교용 정규화
    s = s.strip().lower()
    s = re.sub(r"\s+", "", s)
    s = s.replace("(", "").replace(")", "")
    return s

def contains_answer(hint: str, term: str) -> bool:
    # 힌트에 정답이 새는지 검사
    return norm_answer(term) in norm_answer(hint)

def solar_chat(prompt: str, temperature: float = 0.2) -> str:
    url = "https://api.upstage.ai/v1/solar/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "solar-1-mini-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def make_hint(definition: str, term: str, difficulty: str = "medium") -> str:
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
    return solar_chat(prompt, temperature=0.7)

def judge_semantic(user_input: str, term: str) -> tuple[bool, str]:
    # 의미 기반 판정: Yes/No + 근거 1줄
    prompt = f"""
너는 퀴즈 채점기다. 사용자의 답이 정답 용어와 의미적으로 같은지 판정해라.

규칙:
- 출력은 딱 두 줄만.
- 1줄째: YES 또는 NO
- 2줄째: 근거 한 줄(짧게)

정답 용어: {term}
사용자 입력: {user_input}
""".strip()

    out = solar_chat(prompt, temperature=0.0)
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    first = lines[0] if lines else "NO"
    reason = lines[1] if len(lines) >= 2 else "판정 근거를 생성하지 못함"
    ok = (first.upper().startswith("Y"))
    return ok, reason

def main():
    data = json.load(open(TERMS_PATH, "r", encoding="utf-8"))
    item = random.choice(data)

    term = item["term"]
    definition = item["definition"]

    # 1) 힌트 생성 (정답 노출 방지: 최대 3번 재시도)
    hint = None
    for _ in range(3):
        h = make_hint(definition, term, difficulty="medium")
        if not contains_answer(h, term):
            hint = h
            break
    if hint is None:
        hint = "힌트 생성 실패(정답 노출)."

    print("=== QUIZ ===")
    print("HINT:", hint)

    # 2) 사용자 입력 받기
    user = input("\nYOUR ANSWER: ").strip()

    # 3) 1차: 완전일치 판정
    if norm_answer(user) == norm_answer(term):
        print("\n✅ 정답!")
        print("ANSWER:", term)
        return

    # 4) 2차: Solar 의미 판정(애매할 때만)
    ok, reason = judge_semantic(user, term)

    if ok:
        print("\n🟡 부분정답(의미상 동일)!")
        print("ANSWER:", term)
        print("REASON:", reason)
    else:
        print("\n❌ 오답!")
        print("ANSWER:", term)
        print("REASON:", reason)

if __name__ == "__main__":
    main()
