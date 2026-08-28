import random
import yaml
import os
from typing import List, Dict, Any
from datetime import datetime

class QueryUniverseGenerator:
    def __init__(self, entities_path: str = "config/entities.yaml", personas_path: str = "config/thai_personas.yaml"):
        with open(entities_path, "r", encoding="utf-8") as f:
            self.entities = yaml.safe_load(f)
        with open(personas_path, "r", encoding="utf-8") as f:
            self.personas = yaml.safe_load(f).get("personas", [])

        # Query intent templates with Thai language slots
        self.templates = [
            # Recommendation & Category intent
            "{category} แพลตฟอร์มไหนดีที่สุด สำหรับคนงบ {budget}?",
            "ซื้อ {category} ของแท้ 100% ระหว่าง {brand_a} กับ {brand_b} ที่ไหนมั่นใจกว่ากัน?",
            "แคมเปญ Double Day ซื้อ {category} แพลตฟอร์มไหนแจกโค้ดลดเยอะสุด?",
            "แนะนำร้านค้า/แอพสั่ง {category} ส่งไว ได้ของภายในวัน มีเจ้าไหนบ้าง?",
            "เทียบราคาและโปรโมชั่น {category} เจ้าไหนคุ้มสุดตอนนี้?",
            "ถ้าเน้นบริการหลังการขายและเคลมง่าย ซื้อ {category} ที่ไหนดี?",
            "อยากได้ {category} แท้ มีของแถมเยอะๆ ชาวเน็ตแนะนำที่ไหน?",
            "{brand_a} กับ {brand_b} ซื้อ {category} อันไหนส่งไวกว่ากัน?",
        ]

        self.categories = [
            "สกินแคร์เคาน์เตอร์แบรนด์", "เครื่องสำอางเกาหลี", "กันแดดคุมมัน", 
            "เซรั่มลดรอยสิว", "ลิปสติก", "น้ำหอมแท้", "อาหารเสริมวิตามิน"
        ]

        self.budgets = ["ประหยัด", "ไม่เกิน 500 บาท", "ไม่เกิน 1,500 บาท", "ไม่อั้น/พรีเมียม"]

    def generate_queries(self, count: int = 20, seed: int = 42) -> List[Dict[str, Any]]:
        rng = random.Random(seed)
        queries = []

        brands = [b["name"] for b in self.entities["verticals"][0]["brands"]]

        for i in range(count):
            template = rng.choice(self.templates)
            category = rng.choice(self.categories)
            budget = rng.choice(self.budgets)
            persona = rng.choice(self.personas)
            brand_samples = rng.sample(brands, 2)

            query_text = template.format(
                category=category,
                budget=budget,
                brand_a=brand_samples[0],
                brand_b=brand_samples[1]
            )

            queries.append({
                "query_id": f"q_gen_{seed}_{i+1:03d}",
                "text_th": query_text,
                "category": category,
                "persona_id": persona["id"],
                "persona_name": persona["name"],
                "is_control_set": i < 5,  # First 5 are designated control set
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "seed": seed
            })

        return queries
