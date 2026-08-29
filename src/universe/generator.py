# src/universe/generator.py
import random
import yaml
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class QueryUniverseGenerator:
    def __init__(
        self,
        entities_path: str = "config/entities.yaml",
        personas_path: str = "config/thai_personas.yaml",
        control_set_path: str = "config/control_benchmark_set.yaml"
    ):
        with open(entities_path, "r", encoding="utf-8") as f:
            self.entities = yaml.safe_load(f)
        with open(personas_path, "r", encoding="utf-8") as f:
            self.personas = yaml.safe_load(f).get("personas", [])

        self.control_set_path = control_set_path
        self.control_queries = []
        if os.path.exists(control_set_path):
            with open(control_set_path, "r", encoding="utf-8") as f:
                self.control_queries = yaml.safe_load(f).get("queries", [])

        # Query intent templates with Thai language slots
        self.templates = [
            "{category} แพลตฟอร์มไหนดีที่สุด สำหรับคนงบ {budget}?",
            "ซื้อ {category} ของแท้ 100% ระหว่าง {brand_a} กับ {brand_b} ที่ไหนมั่นใจกว่ากัน?",
            "แคมเปญ Double Day ซื้อ {category} แพลตฟอร์มไหนแจกโค้ดลดเยอะสุด?",
            "แนะนำร้านค้า/แอพสั่ง {category} ส่งไว ได้ของภายในวัน มีเจ้าไหนบ้าง?",
            "เทียบราคาและโปรโมชั่น {category} เจ้าไหนคุ้มสุดตอนนี้?",
            "ถ้าเน้นบริการหลังการขายและเคลมง่าย ซื้อ {category} ที่ไหนดี?",
            "อยากได้ {category} แท้ มีของแถมเยอะๆ ชาวเน็ตแนะนำที่ไหน?",
            "{brand_a} กับ {brand_b} ซื้อ {category} อันไหนส่งไวกว่ากัน?",
            "สกินแคร์ {category} ใน TikTok Shop กับ Shopee Mall สั่งที่ไหนดี?",
            "รีวิวสั่ง {category} จาก {brand_a} vs {brand_b} เรื่องแพ็คของกันกระแทก"
        ]

        self.categories = [
            "สกินแคร์เคาน์เตอร์แบรนด์", "เครื่องสำอางเกาหลี", "กันแดดคุมมัน", 
            "เซรั่มลดรอยสิว", "ลิปสติก", "น้ำหอมแท้", "อาหารเสริมวิตามิน", "มอยส์เจอไรเซอร์ผิวแพ้ง่าย"
        ]

        self.budgets = ["ประหยัด", "ไม่เกิน 500 บาท", "ไม่เกิน 1,500 บาท", "ไม่อั้น/พรีเมียม"]

    def get_control_benchmark_set(self) -> List[Dict[str, Any]]:
        """Returns the 30 invariant benchmark queries for longitudinal stability."""
        return [
            {
                "query_id": q.get("query_id", f"q_ctrl_{i+1:02d}"),
                "text_th": q.get("text_th", ""),
                "category": q.get("category", "discovery"),
                "persona_id": "standard_shopper",
                "persona_name": "Standard Thai Online Shopper",
                "is_control_set": True,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            for i, q in enumerate(self.control_queries)
        ]

    def generate_exploratory_queries(self, count: int = 10, seed: int = 42) -> List[Dict[str, Any]]:
        """Generates randomized queries with seeded reproducibility across Persona x Intent."""
        rng = random.Random(seed)
        queries = []
        brands = [b["name"] for b in self.entities["verticals"][0]["brands"]]

        for i in range(count):
            template = rng.choice(self.templates)
            category = rng.choice(self.categories)
            budget = rng.choice(self.budgets)
            persona = rng.choice(self.personas) if self.personas else {"id": "p_genz", "name": "Gen-Z"}
            brand_samples = rng.sample(brands, min(2, len(brands)))
            brand_a = brand_samples[0]
            brand_b = brand_samples[1] if len(brand_samples) > 1 else brands[0]

            query_text = template.format(
                category=category,
                budget=budget,
                brand_a=brand_a,
                brand_b=brand_b
            )

            queries.append({
                "query_id": f"q_exp_{seed}_{i+1:03d}",
                "text_th": query_text,
                "category": category,
                "persona_id": persona["id"],
                "persona_name": persona["name"],
                "is_control_set": False,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "seed": seed
            })

        return queries

    def generate_queries(self, count: int = 20, seed: int = 42, include_control: bool = False) -> List[Dict[str, Any]]:
        if include_control:
            ctrl = self.get_control_benchmark_set()
            if count <= len(ctrl):
                return ctrl[:count]
            exp = self.generate_exploratory_queries(count=count - len(ctrl), seed=seed)
            return ctrl + exp
        return self.generate_exploratory_queries(count=count, seed=seed)
