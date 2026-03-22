from google import genai
from dotenv import load_dotenv
from datetime import datetime
from config import MODEL_NAME, BRANDS, PROMPTS
import pandas as pd
import time
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

model_name = MODEL_NAME
allnii_competitors = BRANDS

for prompt in PROMPTS:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ถาม Gemini ครั้งที่ 1
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
    except Exception as e:
        print(f"⚠️ Error: {e}")
        print("รอ 30 วินาทีแล้วลองใหม่...")
        time.sleep(30)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

    print("---Gemini Response---")
    print(f"timestamp : {timestamp}")
    print(f"model     : {model_name}")
    print(f"prompt    : {prompt}")
    print(response.text)

    # หา brand ที่พบ
    found_brands = []
    for brand in allnii_competitors:
        if brand.lower() in response.text.lower():
            found_brands.append(brand)

    print("\n---Platform Mentioned---")
    if found_brands:
        for brand in found_brands:
            print(f"mentioned: {brand}")
    else:
        print("platform not mentioned")

     # หา position และ rank
    brand_positions = {}
    for brand in allnii_competitors:
        pos = response.text.lower().find(brand.lower())
        brand_positions[brand] = pos

    mentioned_sorted = sorted(
        [b for b in allnii_competitors if brand_positions[b] != -1],
        key=lambda b: brand_positions[b]
    )

    brand_ranks = {}
    for i, brand in enumerate(mentioned_sorted):
        brand_ranks[brand] = i + 1

    # ถาม sentiment ครั้งที่ 2
    sentiment_data = {}
    if found_brands:
        brands_list = ", ".join(found_brands)
        sentiment_prompt = f"""จากข้อความนี้:
{response.text}

สำหรับแต่ละ platform นี้: {brands_list}
ตอบในรูปแบบนี้เท่านั้น ทีละบรรทัด:
brand | sentiment | reason

เช่น:
Lazada | positive | ราคาถูก โปรโมชั่นเยอะ"""

        try:
            sentiment_response = client.models.generate_content(
                model=model_name,
                contents=sentiment_prompt
            )
        except Exception as e:
            print(f"⚠️ Sentiment error: {e} — ข้ามไป")
            continue

        print("\n---Sentiment Analysis---")
        print(sentiment_response.text)

        for line in sentiment_response.text.strip().split("\n"):
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    sentiment_data[parts[0]] = {
                        "sentiment": parts[1],
                        "reason": parts[2]
                    }

    # บันทึกลง CSV
    rows = []
    for brand in allnii_competitors:
        s = sentiment_data.get(brand, {})
        rows.append({
            "timestamp": timestamp,
            "model": model_name,
            "prompt": prompt,
            "brand": brand,
            "mentioned": brand in found_brands,
            "position": brand_positions[brand],
            "rank": brand_ranks.get(brand, 0),
            "sentiment": s.get("sentiment", "not_mentioned"),
            "reason": s.get("reason", "ไม่ถูกพูดถึง")
        })

    df = pd.DataFrame(rows)
    df.to_csv("results.csv", mode="a", header=not os.path.exists("results.csv"), index=False)
    print(f"\n✅ บันทึก prompt: {prompt}")

print("\n🎉 succeed all prompts!")