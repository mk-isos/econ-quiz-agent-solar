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
        if t and t not in terms:
            terms.append(t)
    return terms

def is_toc_like(s: str) -> bool:
    # 목차 특징: 점선/네모/많은 숫자/여러 용어가 붙어 있음
    if re.search(r"[·\.]{10,}|□{5,}|-{10,}", s):  # 점선/박스/긴 하이픈
        return True
    nums = len(re.findall(r"\b\d{1,3}\b", s))
    if nums >= 5:  # 페이지 번호가 줄줄
        return True
    return False

def find_all_positions(text: str, term: str):
    pat = re.compile(rf"(?<!\S)({re.escape(term)})(?!\S)")
    return [m.start() for m in pat.finditer(text)]

def extract_best_definition(text: str, term: str):
    positions = find_all_positions(text, term)
    if not positions:
        return None

    for pos in positions[:6]:  # 너무 많이 돌면 느리니까 앞쪽 몇 개만
        start = pos + len(term)
        tail = text[start:]

        # 기본적으로 다음 용어/구분 전까지 1500자 정도를 후보로 잡음
        cand = tail[:1500]

        # 목차 같으면 패스
        if is_toc_like(cand):
            continue

        cand = normalize(cand)

        # 너무 짧으면 패스
        if len(cand) < 60:
            continue

        # 너무 길면 잘라서 제출용으로 깔끔하게
        if len(cand) > 800:
            cand = cand[:800].rstrip() + "…"

        return cand

    return None

def main():
    text = normalize(open(TEXT_PATH, "r", encoding="utf-8").read())
    terms = load_terms(TERMS_PATH)

    results, missing = [], []

    for t in terms:
        d = extract_best_definition(text, t)
        if not d:
            missing.append(t)
            continue
        results.append({"term": t, "definition": d, "source_page": None})

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
