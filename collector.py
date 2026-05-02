"""
collector.py — Data Collection Pipeline
========================================
สคริปต์หลักที่รันการเก็บข้อมูลทั้งหมด

วิธีรัน:
    python collector.py

ลำดับการทำงาน:
    1. วน loop ทีละ prompt (จาก settings.yaml)
    2. ส่ง prompt ให้ Gemini API (พร้อม Google Search grounding)
    3. ตรวจว่าแบรนด์ไหนถูกพูดถึงในคำตอบ
    4. คำนวณ rank ของแต่ละแบรนด์ (แบรนด์ไหนถูกพูดถึงก่อน = rank ดีกว่า)
    5. เรียก Gemini อีกครั้งเพื่อวิเคราะห์ sentiment ของแต่ละแบรนด์
    6. บันทึกผลลง results.db (SQLite) → 1 row ต่อ 1 แบรนด์ต่อ 1 prompt

หมายเหตุ: API quota หมดแล้ว ดูผลใน analysis.ipynb แทนได้เลย
"""

from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
from config import MODEL_NAME, BRANDS, PROMPTS
from tqdm import tqdm
import pandas as pd
import logging
import sqlite3
import time
import os

# ---- Logging Setup ----
# mode="w" = เขียนทับ log เก่าทุกครั้งที่รัน (ไม่เก็บ history)
# ถ้าอยากเก็บ history ของหลาย run ให้เปลี่ยนเป็น mode="a"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s — %(message)s",
    handlers=[
        logging.FileHandler("tracker.log", mode="w"),
        logging.StreamHandler()
    ]
)

# ---- API Client ----
# โหลด GEMINI_API_KEY จากไฟล์ .env
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ---- Functions ----

def get_ai_response(prompt):
    """
    ส่ง prompt ให้ Gemini และรับคำตอบกลับมา

    พิเศษ: เปิด Google Search grounding ไว้ด้วย
    → Gemini จะค้นเว็บจริงก่อนตอบ (ไม่ได้ตอบจาก training data อย่างเดียว)
    → ทำให้คำตอบ reflect สถานการณ์ตลาดปัจจุบันได้แม่นกว่า

    Returns:
        response_text (str): คำตอบจาก Gemini
        sources (list[str]): ชื่อเว็บที่ Gemini ใช้อ้างอิง (อาจเป็น [] ถ้า retry)
    """
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(
                    # google_search = ให้ Gemini ค้นเว็บก่อนตอบ
                    # ทำให้ได้ข้อมูลล่าสุด + รู้ว่าดึงข้อมูลมาจากไหน
                    google_search=types.GoogleSearch()
                )]
            )
        )

        # ดึงชื่อแหล่งอ้างอิง (grounding sources) จาก metadata
        # grounding_chunks = list ของเว็บที่ Gemini ค้นมา
        sources = []
        if response.candidates[0].grounding_metadata:
            for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                if chunk.web:
                    title = chunk.web.title or ""
                    if title not in sources:
                        sources.append(title)

        return response.text, sources

    except Exception as e:
        # ถ้า API error (เช่น rate limit, timeout) → รอ 30 วิแล้ว retry 1 ครั้ง
        # หมายเหตุ: retry call นี้ไม่มี google_search → คำตอบจะมาจาก training data ล้วนๆ
        # และ sources จะเป็น [] เสมอ (ไม่มีแหล่งอ้างอิง)
        logging.error(f"⚠️ Error: {e}")
        logging.info("รอ 30 วินาทีแล้วลองใหม่...")
        time.sleep(30)
        return client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        ).text, []


def find_mentioned_brands(response_text, brands):
    """
    ตรวจว่าแบรนด์ไหนถูกพูดถึงในคำตอบของ Gemini บ้าง

    วิธี: simple case-insensitive string search
    เช่น ถ้าคำตอบมีคำว่า "shopee" (ตัวเล็กหรือใหญ่ก็ได้) → Shopee ถูก mention

    Returns:
        found_brands (list[str]): แบรนด์ที่พบในคำตอบ
    """
    found_brands = []
    for brand in brands:
        if brand.lower() in response_text.lower():
            found_brands.append(brand)
    return found_brands


def calculate_ranks(response_text, brands):
    """
    คำนวณ rank ของแต่ละแบรนด์ตาม "ลำดับที่ถูกพูดถึง" ในคำตอบ

    วิธีวัด rank: ใช้ character position (index) ในคำตอบ
    → แบรนด์ที่ปรากฏก่อน (index น้อยกว่า) = rank ดีกว่า
    → rank 1 = ถูกพูดถึงเป็นคนแรกสุด

    ข้อจำกัด: character position ≠ prominence จริงๆ
    ตัวอย่าง: ถ้า Allnii ปรากฏใน disclaimer ที่ตัวหน้าสุด
    Allnii จะได้ rank 1 ทั้งที่จริงๆ ไม่ได้ถูก recommend

    Returns:
        brand_positions (dict): {brand: character_index} (-1 ถ้าไม่ถูกพูดถึง)
        brand_ranks    (dict): {brand: rank_number}     (เฉพาะแบรนด์ที่ถูกพูดถึง)
    """
    brand_positions = {}
    for brand in brands:
        pos = response_text.lower().find(brand.lower())
        brand_positions[brand] = pos

    # เรียง เฉพาะแบรนด์ที่ถูกพูดถึง (pos != -1) จากตัวหน้าไปหลัง
    mentioned_sorted = sorted(
        [b for b in brands if brand_positions[b] != -1],
        key=lambda b: brand_positions[b]
    )

    brand_ranks = {}
    for i, brand in enumerate(mentioned_sorted):
        brand_ranks[brand] = i + 1  # rank เริ่มจาก 1

    return brand_positions, brand_ranks


def analyze_sentiment(response_text, found_brands):
    """
    วิเคราะห์ sentiment ของแต่ละแบรนด์โดยเรียก Gemini อีกครั้ง (2nd API call)

    เหตุผลที่ต้องเรียกแยก: Gemini ตอบ sentiment ได้แม่นกว่าถ้าให้ focus ทีละเรื่อง
    แทนที่จะใส่ทุกอย่างใน prompt เดียว

    Output format ที่ขอจาก Gemini:
        brand | sentiment | reason
        Shopee | positive | มีโปรโมชั่นเยอะ

    Returns:
        sentiment_data (dict): {brand: {"sentiment": "positive/neutral/negative", "reason": "..."}}
        คืน {} ถ้า API error หรือไม่มีแบรนด์ที่ถูกพูดถึง
    """
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
        # หมายเหตุ: call นี้ไม่เปิด google_search เพราะวิเคราะห์จาก response_text ที่มีอยู่แล้ว
        sentiment_response = client.models.generate_content(
            model=MODEL_NAME,
            contents=sentiment_prompt
        )
    except Exception as e:
        logging.error(f"⚠️ Sentiment error: {e} — ข้ามไป")
        return {}

    # Parse คำตอบ: แต่ละบรรทัดที่มี "|" = 1 แบรนด์
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
    """
    บันทึก rows ลง SQLite database (results.db)

    if_exists="append" = ต่อท้ายข้อมูลเก่า ไม่ลบทิ้ง
    → ถ้ารันหลายครั้ง ข้อมูลจะสะสมทับกัน (ไม่มี deduplication)
    → ใช้ run_id เพื่อแยกแต่ละ run ได้ในอนาคต
    """
    df = pd.DataFrame(rows)
    conn = sqlite3.connect("results.db")
    df.to_sql("results", conn, if_exists="append", index=False)
    conn.close()


def export_sample_csv():
    """
    Export ผลลัพธ์ล่าสุดออกมาเป็น CSV ไว้ใน sample_output/

    จำนวน rows ที่ export = len(PROMPTS) × len(BRANDS)
    = 1 run เต็มๆ พอดี (ไม่ export ทุก run ที่เคยรัน)
    """
    limit = len(PROMPTS) * len(BRANDS)
    conn = sqlite3.connect("results.db")
    df_sample = pd.read_sql(
        f"SELECT * FROM results ORDER BY timestamp DESC LIMIT {limit}",
        conn
    )
    conn.close()
    df_sample.to_csv("sample_output/results_sample.csv", index=False)
    logging.info("✅ อัพเดท sample_output แล้ว!")


# ---- Main Pipeline ----
# หมายเหตุ: ถ้า import collector.py จากที่อื่น block นี้จะรันด้วย (bug)
# แก้โดยใส่ if __name__ == "__main__": ครอบไว้
if __name__ == "__main__":
    for prompt in tqdm(PROMPTS, desc="Processing Prompts"):
        # timestamp เดียวกันสำหรับทุกแบรนด์ใน prompt นี้
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Step 1: ถามคำถามหลัก → ได้คำตอบ + แหล่งอ้างอิง
        response_text, sources = get_ai_response(prompt["text"])
        logging.info(f"\n---Gemini Response---\n{response_text}")

        # Step 2: ตรวจว่าแบรนด์ไหนถูกพูดถึง
        found_brands = find_mentioned_brands(response_text, BRANDS)
        logging.info(f"\n---Platform Mentioned---\n{found_brands}")

        # Step 3: คำนวณ rank ตาม character position
        brand_positions, brand_ranks = calculate_ranks(response_text, BRANDS)

        # Step 4: วิเคราะห์ sentiment (API call ที่ 2)
        sentiment_data = analyze_sentiment(response_text, found_brands)
        logging.info(f"\n---Sentiment Analysis---\n{sentiment_data}")

        # Step 5: สร้าง rows — 1 row ต่อแบรนด์ (รวม brand ที่ไม่ถูกพูดถึงด้วย)
        rows = []
        for brand in BRANDS:
            s = sentiment_data.get(brand, {})
            rows.append({
                "timestamp": timestamp,
                "model": MODEL_NAME,
                "prompt": prompt["text"],
                "brand": brand,
                "mentioned": brand in found_brands,         # True/False
                "position": brand_positions[brand] if brand in found_brands else None,  # char index
                "rank": brand_ranks.get(brand) or None,     # 1, 2, 3... หรือ None
                "sentiment": s.get("sentiment") or None,
                "reason": s.get("reason") or None,
                # sources = แหล่งอ้างอิงของทั้ง response (ไม่ใช่เฉพาะแบรนด์นั้น)
                "sources": ", ".join(sources) if (sources and brand in found_brands) else None,
                "prompt_category": prompt.get("category")
            })

        # Step 6: บันทึกลง DB
        save_results(rows)
        logging.info(f"\n✅ บันทึก prompt: {prompt}")

    export_sample_csv()
    logging.info("\n🎉 succeed all prompts!")
