import os, json, random, re, requests
import streamlit as st

API_KEY = os.environ.get("UPSTAGE_API_KEY")
TERMS_PATH = "terms.json"

def norm(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", "", s)
    s = s.replace("(", "").replace(")", "")
    return s

def contains_answer(hint: str, term: str) -> bool:
    return norm(term) in norm(hint)

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

def make_hint(definition: str, term: str, difficulty: str) -> str:
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
    ok = first.upper().startswith("Y")
    return ok, reason

# =========================
# UI
# =========================
st.set_page_config(page_title="Econ Quiz Agent (MVP)", page_icon="📘")
st.title("📘 경제금융용어 퀴즈 Agent (MVP)")
st.caption("문제은행(JSON)에서 용어를 뽑아 Solar로 힌트를 생성하고, 규칙+Solar로 정답을 판정합니다.")

if not API_KEY:
    st.error("UPSTAGE_API_KEY 환경변수가 없어. 터미널에서 export UPSTAGE_API_KEY=... 후 다시 실행해줘.")
    st.stop()

data = json.load(open(TERMS_PATH, "r", encoding="utf-8"))

difficulty = st.selectbox("난이도", ["easy", "medium", "hard"], index=1)

if "current" not in st.session_state:
    st.session_state.current = None
if "hint" not in st.session_state:
    st.session_state.hint = None
if "result" not in st.session_state:
    st.session_state.result = None

col1, col2 = st.columns(2)

with col1:
    if st.button("문제 생성"):
        item = random.choice(data)
        term = item["term"]
        definition = item["definition"]

        hint = None
        for _ in range(3):
            h = make_hint(definition, term, difficulty)
            if not contains_answer(h, term):
                hint = h
                break
        if hint is None:
            hint = "힌트 생성 실패(정답 노출). 프롬프트 조정 필요."

        st.session_state.current = item
        st.session_state.hint = hint
        st.session_state.result = None

with col2:
    if st.button("초기화"):
        st.session_state.current = None
        st.session_state.hint = None
        st.session_state.result = None

if st.session_state.hint:
    st.subheader("💡 힌트")
    st.write(st.session_state.hint)

    user = st.text_input("정답 입력", placeholder="예: 공급사용표(SUT)")

    if st.button("정답 제출"):
        term = st.session_state.current["term"]

        if not user.strip():
            st.warning("정답을 입력해줘.")
        else:
            # 1차 완전일치
            if norm(user) == norm(term):
                st.session_state.result = ("✅ 정답!", term, None)
            else:
                # 2차 의미 판정
                ok, reason = judge_semantic(user, term)
                if ok:
                    st.session_state.result = ("🟡 부분정답(의미상 동일)!", term, reason)
                else:
                    st.session_state.result = ("❌ 오답!", term, reason)

if st.session_state.result:
    title, answer, reason = st.session_state.result
    st.subheader("📌 결과")
    st.write(title)
    st.write("**정답:**", answer)
    if reason:
        st.write("**근거:**", reason)
