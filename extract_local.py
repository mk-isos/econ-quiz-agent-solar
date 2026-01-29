import json, re

TEXT_PATH = "clean.txt"
TERMS_PATH = "terms_100.txt"
OUT_PATH = "extract_100.json"

def normalize(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def load_terms(path: str):
    terms = []
    for line in open(path, "r", encoding="utf-8"):
        t = line.strip()
        if not t:
            continue
        # 중복 제거
        if t not in terms:
            terms.append(t)
    return terms

def build_term_regex(term: str) -> str:
    # 용어에 괄호/슬래시 등 특수문자가 많아서 escape 필요
    return re.escape(term)

def extract_definition(text: str, term: str):
    """
    규칙:
    - '용어'가 등장한 지점부터 다음 용어 등장 전까지를 잡는다.
    - 너무 길면 앞부분 위주로 적당히 자른다.
    """
    pattern = re.compile(rf"(?<!\S)({build_term_regex(term)})(?!\S)")
    m = pattern.search(text)
    if not m:
        return None

    start = m.end()

    # 다음 용어 후보: '연관검색어' 또는 'ㄱ ㄴ' 같은 구분 또는 다음 term 등장
    # 일단 '연관검색어'가 있으면 그 전까지가 정의 본문인 경우가 많아서 우선 사용
    tail = text[start:]
    cut = None

    rel = re.search(r"\s연관검색어\s*:", tail)
    if rel:
        cut = start + rel.start()
    else:
        # fallback: 다음 용어가 나오는 가장 빠른 위치 찾기
        # (모든 용어를 다 돌리면 느려질 수 있으니, "두 줄 이상 공백 + 한글/영문 시작" 같은 패턴을 사용)
        nxt = re.search(r"\s{2,}ㄱ\s|\s{2,}ㄴ\s|\s{2,}ㄷ\s", tail)
        if nxt:
            cut = start + nxt.start()

    if cut is None:
        cut = min(len(text), start + 2000)

    definition = normalize(text[start:cut])
    # 너무 짧으면 실패 취급
    if len(definition) < 40:
        return None

    # 길이 제한(너무 길면 MVP에서 다루기 힘듦)
    if len(definition) > 800:
        definition = definition[:800].rstrip() + "…"

    return definition

def guess_source_page(_text: str, _term: str):
    # clean.txt는 페이지 정보가 날아가는 경우가 많아서 MVP는 null로 두는 게 안전
    return None

def main():
    text = normalize(open(TEXT_PATH, "r", encoding="utf-8").read())
    terms = load_terms(TERMS_PATH)

    results = []
    missing = []

    for t in terms:
        d = extract_definition(text, t)
        if not d:
            missing.append(t)
            continue
        results.append({
            "term": t,
            "definition": d,
            "source_page": guess_source_page(text, t)
        })

    open(OUT_PATH, "w", encoding="utf-8").write(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"OK -> {OUT_PATH} ({len(results)} items)")
    if missing:
        print("MISSING:", len(missing))
        for t in missing[:30]:
            print(" -", t)
        if len(missing) > 30:
            print(" ...")

if __name__ == "__main__":
    main()
