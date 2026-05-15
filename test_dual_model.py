"""Dual Model Test: DeepSeek (analysis) vs Kimi (generation)"""
import asyncio
import json
import os
import httpx

DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
KIMI_KEY = os.environ.get("KIMI_API_KEY", "")

DS_URL = "https://api.deepseek.com/v1/chat/completions"
KIMI_URL = "https://api.moonshot.cn/v1/chat/completions"


async def call_deepseek(prompt: str, max_tokens: int = 200) -> str:
    """DeepSeek - logical analysis tasks"""
    print(f"  [DeepSeek] calling...")
    async with httpx.AsyncClient(timeout=30) as c:
        resp = await c.post(
            DS_URL,
            headers={"Authorization": f"Bearer {DS_KEY}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are an audit assistant. Be concise, under 50 words."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": max_tokens,
            },
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"API Error: {resp.status_code} - {resp.text[:200]}"


async def call_kimi(prompt: str, max_tokens: int = 500) -> str:
    """Kimi - creative generation tasks"""
    print(f"  [Kimi] calling...")
    async with httpx.AsyncClient(timeout=60) as c:
        resp = await c.post(
            KIMI_URL,
            headers={"Authorization": f"Bearer {KIMI_KEY}", "Content-Type": "application/json"},
            json={
                "model": "moonshot-v1-auto",
                "messages": [
                    {"role": "system", "content": "You are a frontend design assistant, skilled in Flat Design."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": max_tokens,
            },
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        return f"API Error: {resp.status_code} - {resp.text[:200]}"


async def main():
    print(f"\n{'='*60}")
    print("  DUAL MODEL ROUTING TEST")
    print(f"{'='*60}")
    print(f"  DeepSeek Key: {'SET' if DS_KEY else 'MISSING'}")
    print(f"  Kimi Key:     {'SET' if KIMI_KEY else 'MISSING'}")

    # -- Scenario 1: Approval Review (DeepSeek) --
    print(f"\n{'-'*60}")
    print("  [1/4] Smart Approval Review")
    print(f"{'-'*60}")
    print("  Model: DeepSeek (Logic & Reasoning)")

    result1 = await call_deepseek(
        "Review this borrow request: User Zhang borrowed a MacBook Pro worth 12000 CNY, "
        "expected 7 days. Is this reasonable? Give a short audit opinion."
    )
    print(f"  Result: {result1}")

    # -- Scenario 2: Anomaly Detection (DeepSeek) --
    print(f"\n{'-'*60}")
    print("  [2/4] Anomaly Pattern Detection")
    print(f"{'-'*60}")
    print("  Model: DeepSeek (Data Analysis)")

    records = [
        {"id": 1, "user": "Zhang", "item": "Projector", "status": "borrowed", "days": 3},
        {"id": 2, "user": "Zhang", "item": "Camera", "status": "borrowed", "days": 2},
        {"id": 3, "user": "Zhang", "item": "Microphone", "status": "borrowed", "days": 1},
        {"id": 4, "user": "Li", "item": "iPad", "status": "overdue", "days": 30},
    ]
    result2 = await call_deepseek(
        f"Find anomaly IDs in JSON array format: {json.dumps(records)}"
    )
    print(f"  Result: {result2}")

    # -- Scenario 3: Page Generation (Kimi) --
    print(f"\n{'-'*60}")
    print("  [3/4] Frontend Page Generation")
    print(f"{'-'*60}")
    print("  Model: Kimi (Creative Generation)")

    result3 = await call_kimi(
        "Generate an HTML/CSS card for an item detail view. "
        "Requirements: Flat Design, dark mode support via prefers-color-scheme, "
        "show item name, stock count, status badge. No CDN dependencies. "
        "Return ONLY the HTML/CSS code, no markdown fences."
    )
    print(f"  Result (first 400 chars): {result3[:400]}...")

    # -- Scenario 4: SVG Image Generation (Kimi) --
    print(f"\n{'-'*60}")
    print("  [4/4] SVG Image Generation")
    print(f"{'-'*60}")
    print("  Model: Kimi (Visual Creation)")

    result4 = await call_kimi(
        "Generate a Flat Design SVG icon for a warehouse/inventory box. "
        "Simple colors, no external fonts. Return ONLY the SVG code."
    )
    print(f"  Result (first 400 chars): {result4[:400]}...")

    # -- Summary --
    print(f"\n{'='*60}")
    print("  ROUTING SUMMARY")
    print(f"{'='*60}")
    print(f"""
    +---------------------+------------------+
    | Task                | Model            |
    +---------------------+------------------+
    | Approval Review     | DeepSeek         |
    | Anomaly Detection   | DeepSeek         |
    | Page Generation     | Kimi             |
    | Image Generation    | Kimi             |
    +---------------------+------------------+
    """)


if __name__ == "__main__":
    asyncio.run(main())
