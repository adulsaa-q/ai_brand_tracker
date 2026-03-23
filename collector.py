from google import genai
from dotenv import load_dotenv
from datetime import datetime
from config import MODEL_NAME, BRANDS, PROMPTS
from tqdm import tqdm
import pandas as pd
import sqlite3
import time
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---- Functions ----

def get_ai_response(prompt):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"⚠️ Error: {e}")
        print("รอ 30 วินาทีแล้วลองใหม่...")
        time.sleep(30)
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        ).text

def find_mentioned_brands(response_text, brands):
    found_brands = []
    for brand in brands:
        if brand.lower() in response_text.lower():
            found_brands.append(brand)
    return found_brands


def calculate_ranks(response_text, brands):
    brand_positions = {}
    for brand in brands:
        pos = response_text.lower().find(brand.lower())
        brand_positions[brand] = pos

    mentioned_sorted = sorted(
        [b for b in brands if brand_positions[b] != -1],
        key=lambda b: brand_positions[b]
    )

    brand_ranks = {}
    for i, brand in enumerate(mentioned_sorted):
        brand_ranks[brand] = i + 1

    return brand_positions, brand_ranks


def analyze_sentiment(response_text, found_brands):
    if not found_brands:
        return {}

    brands_list = ", ".join(found_brands)
    sentiment_prompt = f"""จากข้อความนี้:
{response_text}

สำหรับแต่ละ platform นี้: {brands_list}
ตอบในรูปแบบนี้เท่านั้น ทีละบรรทัด:
brand | sentiment | reason

เช่น:
Lazada | positive | ราคาถูก โปรโมชั่นเยอะ"""

    try:
        sentiment_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=sentiment_prompt
        )
    except Exception as e:
        print(f"⚠️ Sentiment error: {e} — ข้ามไป")
        return {}

    sentiment_data = {}
    for line in sentiment_response.text.strip().split("\n"):
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:
                sentiment_data[parts[0]] = {
                    "sentiment": parts[1],
                    "reason": parts[2]
                }
    return sentiment_data


def save_results(rows):
    df = pd.DataFrame(rows)
    conn = sqlite3.connect("results.db")
    df.to_sql("results", conn, if_exists="append", index=False)
    conn.close()


def export_sample_csv():
    limit = len(PROMPTS) * len(BRANDS)
    conn = sqlite3.connect("results.db")
    df_sample = pd.read_sql(
        f"SELECT * FROM results ORDER BY timestamp DESC LIMIT {limit}",
        conn
    )
    conn.close()
    df_sample.to_csv("sample_output/results_sample.csv", index=False)
    print("✅ อัพเดท sample_output แล้ว!")


# ---- Main ----
for prompt in tqdm(PROMPTS, desc="Processing Prompts"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    response_text = get_ai_response(prompt)
    print(f"\n---Gemini Response---\n{response_text}")

    found_brands = find_mentioned_brands(response_text, BRANDS)
    print(f"\n---Platform Mentioned---\n{found_brands}")

    brand_positions, brand_ranks = calculate_ranks(response_text, BRANDS)

    sentiment_data = analyze_sentiment(response_text, found_brands)
    print(f"\n---Sentiment Analysis---\n{sentiment_data}")

    rows = []
    for brand in BRANDS:
        s = sentiment_data.get(brand, {})
        rows.append({
            "timestamp": timestamp,
            "model": MODEL_NAME,
            "prompt": prompt,
            "brand": brand,
            "mentioned": brand in found_brands,
            "position": brand_positions[brand],
            "rank": brand_ranks.get(brand, 0),
            "sentiment": s.get("sentiment", "not_mentioned"),
            "reason": s.get("reason", "ไม่ถูกพูดถึง")
        })

    save_results(rows)
    print(f"\n✅ บันทึก prompt: {prompt}")

export_sample_csv()
print("\n🎉 succeed all prompts!")