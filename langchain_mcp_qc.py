# langchain_mcp_qc.py  (fixed, interactive, MCP-safe, JSON-fence handling)
import warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", module="importlib")

import os
import sys
import json
import argparse
import random
import pandas as pd
import requests
from dotenv import load_dotenv
from typing import Optional

# LangChain Gemini client
from langchain_google_genai import ChatGoogleGenerativeAI

# ----------------- load env -----------------
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise SystemExit("ERROR: Set GOOGLE_API_KEY in your environment before running.")

# Model (override with GEMINI_MODEL env var if needed)
LLM_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
llm = ChatGoogleGenerativeAI(model=LLM_MODEL_NAME, temperature=0.0)

# ----------------- helpers -----------------
def clean_markdown_json(text: str) -> str:
    """
    Remove common markdown fences like ```json ... ``` or ``` ... ```
    and return cleaned text.
    """
    if not isinstance(text, str):
        text = str(text)
    t = text.strip()
    # remove leading/trailing fenced blocks
    if t.startswith("```json"):
        t = t[len("```json"):].strip()
    if t.startswith("```"):
        t = t[3:].strip()
    if t.endswith("```"):
        t = t[:-3].strip()
    return t

def try_parse_json_from_text(text: str) -> Optional[dict]:
    cleaned = clean_markdown_json(text)
    try:
        return json.loads(cleaned)
    except Exception:
        return None

# ----------------- simple QA -----------------
def simple_qa(question: str) -> str:
    prompt = f"You are a helpful assistant. Answer concisely.\nQuestion: {question}\nAnswer:"
    try:
        resp = llm.invoke(prompt)
        if hasattr(resp, "content"):
            return resp.content.strip()
        return str(resp).strip()
    except Exception as e:
        return f"LLM call failed: {e}"

# ----------------- sample data -----------------
def make_sample_data(n=20) -> pd.DataFrame:
    random.seed(42)
    rows = []
    for i in range(1, n+1):
        name = random.choice(["Aarav","Riya","Karan","Sneha","Rahul"])
        if i == 5:
            name = "123456"
        if i == 12:
            name = "007"
        age = 151 if i == 7 else random.choice([25,34,45,29,55])
        amount = round(random.uniform(100,5000), 2)
        order_date = pd.Timestamp("2024-01-01") + pd.Timedelta(days=random.randint(0,30))
        rows.append({"order_id": i, "name": name, "age": age, "amount": amount, "order_date": str(order_date.date())})
    return pd.DataFrame(rows)

# ----------------- file loader -----------------
def load_file_to_df(path: str) -> pd.DataFrame:
    p = path.strip()
    if p.lower().endswith(".csv"):
        return pd.read_csv(p)
    if p.lower().endswith(".json"):
        return pd.read_json(p)
    raise ValueError("Unsupported file type. Use .csv or .json")

# ----------------- MCP helpers -----------------
def mcp_is_healthy(base_url: str) -> bool:
    try:
        url = base_url.rstrip("/") + "/health"
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def send_to_mcp(base_url: str, endpoint: str, payload: dict, api_key: Optional[str] = None):
    url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

# ----------------- LLM QC -----------------
def llm_data_qc(df: pd.DataFrame, max_sample_rows: int = 20) -> dict:
    sample = df.head(max_sample_rows).to_dict(orient="records")
    prompt_text = f"""
You are a strict data-quality analyst. You will receive a JSON array of up to {max_sample_rows} rows.
Return exactly one JSON object (no text) with keys:
- summary: one-line summary
- anomalies: array of {{row_index, column, value, issue, severity}} (severity: low/medium/high)
- suggested_actions: array of short recommendations

Rules:
- Check numeric ranges (e.g., 'age' > 150 is an error).
- Check name-like fields that are only digits.
- Check inconsistent types or obvious format errors.
- Use column headers to infer meaning.
- Return only valid JSON, nothing else.

Data:
{json.dumps(sample, indent=2)}
"""
    try:
        resp = llm.invoke(prompt_text)
        text = resp.content if hasattr(resp, "content") else str(resp)
        parsed = try_parse_json_from_text(text)
        if parsed is not None:
            return parsed
        # last resort: return raw for debugging
        return {"error": "LLM response not valid JSON", "raw": text}
    except Exception as e:
        return {"error": "LLM call failed", "raw_exception": str(e)}

# ----------------- CLI & main flow -----------------
def main(argv):
    parser = argparse.ArgumentParser(description="LangChain MCP QC demo (Gemini).")
    parser.add_argument("--ask", action="store_true", help="Interactive: ask a question to the LLM")
    parser.add_argument("--file", type=str, help="Path to CSV/JSON file to validate (optional).")
    parser.add_argument("--send-mcp", action="store_true", help="If set, attempt to POST sample to MCP (requires MCP running).")
    parser.add_argument("--mcp-base", type=str, default=os.getenv("MCP_BASE_URL", "http://127.0.0.1:5001"), help="MCP base URL")
    args = parser.parse_args(argv[1:])

    # Step A: optional interactive QA
    if args.ask:
        question = input("Type your question: ").strip()
        if question:
            print("\nLLM answer:")
            print(simple_qa(question))
            print()
        else:
            print("No question typed. Continuing...\n")

    # Step B: choose data source
    if args.file:
        try:
            df = load_file_to_df(args.file)
            print(f"Loaded file: {args.file} rows={len(df)} cols={len(df.columns)}")
        except Exception as e:
            print("Failed to load file:", e)
            return 1
    else:
        df = make_sample_data(20)
        print("Using generated sample data (20 rows):")

    print(df.to_string(index=False))
    print()

    # Step C: optional MCP send (health-check first)
    if args.send_mcp:
        base = args.mcp_base
        print(f"Checking MCP health at {base}/health ...")
        if mcp_is_healthy(base):
            try:
                resp = send_to_mcp(base, "ingest/sample", {"rows": df.head(20).to_dict(orient='records')}, api_key=os.getenv("MCP_API_KEY", None))
                print("MCP response:", resp)
            except Exception as e:
                print("Error sending to MCP:", e)
        else:
            print("MCP health check failed. Please start MCP server or correct MCP_BASE URL.")
    else:
        print("MCP send skipped (use --send-mcp to enable).")
    print()

    # Step D: run LLM QC
    print("Running LLM-based data quality checks (Gemini)...")
    result = llm_data_qc(df)
    print(json.dumps(result, indent=2))
    print("\nDone.")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
