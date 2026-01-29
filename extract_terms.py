import os, json, requests

API_KEY = os.environ.get("UPSTAGE_API_KEY")
if not API_KEY:
    raise SystemExit("UPSTAGE_API_KEY 환경변수가 없어. 터미널에서 export 했는지 확인해줘.")

# clean.txt를 우선 사용 (없으면 parsed_part1.md 사용)
src = "clean.txt" if os.path.exists("clean.txt") else "parsed_part1.md"
text = open(src, "r", encoding="utf-8").read()

url = "https://api.upstage.ai/v1/information-extract"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "schema": {
        "term": "string",
        "definition": "string",
        "source_page": "number"
    },
    "text": text,
    "instructions": (
        "Extract glossary entries from the given Korean economics text.\n"
        "Return ONLY a JSON array of objects with fields: term, definition, source_page.\n"
        "term: the glossary term (short, no extra punctuation).\n"
        "definition: concise definition in Korean (1-3 sentences).\n"
        "source_page: if the page number is clearly available, use it; otherwise null.\n"
        "Do not hallucinate page numbers.\n"
        "Extract up to 120 items maximum.\n"
        "If the same term appears multiple times, keep only one best definition."
    )
}

resp = requests.post(url, headers=headers, data=json.dumps(payload))
print("status:", resp.status_code)
print("using source:", src)
resp.raise_for_status()

data = resp.json()
open("extract_raw.json", "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
print("Saved -> extract_raw.json")
