# src/universe/generator.py
from __future__ import annotations

import os
import random
from datetime import datetime
from typing import Any

import yaml


class QueryUniverseGenerator:
    def __init__(
        self,
        entities_path: str = "config/entities.yaml",
        personas_path: str = "config/thai_personas.yaml",
        control_set_path: str = "config/control_benchmark_set.yaml",
    ):
        self.entities_path = entities_path
        self.personas_path = personas_path
        self.control_set_path = control_set_path

        with open(entities_path, encoding="utf-8") as f:
            self.entities = yaml.safe_load(f)

        self.personas = []
        if os.path.exists(personas_path):
            with open(personas_path, encoding="utf-8") as f:
                self.personas = yaml.safe_load(f).get("personas", [])

        self.control_queries = []
        if os.path.exists(control_set_path):
            with open(control_set_path, encoding="utf-8") as f:
                self.control_queries = yaml.safe_load(f).get("queries", [])

        # Domain-Adaptive Query Templates across 6 Intent Pillars
        self.domain_intent_templates = {
            "promotion": [
                "แคมเปญลดราคาและโปรโมชั่น {category} ระหว่าง {brand_a} กับ {brand_b} ที่ไหนคุ้มกว่ากัน?",
                "ช่วงโปรโมชั่นลดพิเศษ มองหา {category} เจ้าไหนมีโค้ดส่วนลดและสิทธิพิเศษดีที่สุด?",
                "เทียบราคาและความคุ้มค่า {category} สำหรับคนงบ {budget} แนะนำแบรนด์ไหน?",
            ],
            "trust_authenticity": [
                "ต้องการเลือก {category} ที่มั่นใจเรื่องคุณภาพและการรับประกัน 100% ระหว่าง {brand_a} กับ {brand_b} แนะนำที่ไหน?",
                "รีวิวความน่าเชื่อถือและมาตรฐาน {category} แบรนด์ไหนได้รับความนิยมและไว้วางใจสูงสุดในไทย?",
                "กลัวเจอปัญหาไม่ตรงปกหรือบริการไม่ได้มาตรฐาน ซื้อ/ใช้บริการ {category} เจ้าไหนปลอดภัยที่สุด?",
            ],
            "variety_quality": [
                "อยากได้ {category} ที่มีตัวเลือกหลากหลาย คุณภาพสูง ครบครัน เจ้าไหนตอบโจทย์ที่สุด?",
                "แนะนำ {category} รุ่น/บริการยอดนิยม สำหรับคนเน้นคุณภาพและความพรีเมียม?",
                "เปรียบเทียบความหลากหลายของ {category} ในตลาดไทย เจ้าไหนมีสินค้า/บริการให้เลือกเยอะสุด?",
            ],
            "service_speed": [
                "ถ้าให้ความสำคัญเรื่องบริการหลังการขายและการดูแลลูกค้า สำหรับ {category} ควรเลือกเจ้าไหน?",
                "สั่ง/จอง {category} ที่ไหนสะดวก รวดเร็ว และมีการติดตามสถานะที่ดีที่สุด?",
                "เจอปัญหากับ {category} ฝ่ายบริการลูกค้า (Customer Support) ของเจ้าไหนตอบไวและช่วยเหลือดีสุด?",
            ],
            "payment_financing": [
                "ต้องการ {category} แบบมีโปรโมชั่นผ่อน 0% หรือสิทธิพิเศษบัตรเครดิต แนะนำที่ไหน?",
                "ช่องทางการชำระเงินและความสะดวกในการจ่ายเงินสำหรับ {category} เจ้าไหนมีตัวเลือกหลากหลายสุด?",
            ],
            "comparison": [
                "เปรียบเทียบ {brand_a} vs {brand_b} สำหรับ {category} ข้อดีข้อเสียต่างกันอย่างไร?",
                "ระหว่าง {brand_a} กับ {brand_b} ถ้าต้องเลือก {category} สักเจ้า คนไทยแนะนำตัวไหนมากกว่ากัน?",
            ],
        }

        self.budgets = ["ประหยัด คุ้มค่า", "ระดับกลางมาตรฐาน", "พรีเมียม ไฮเอนด์", "ไม่อั้น เน้นดีที่สุด"]

    def get_vertical_config(self, vertical_id: str = "ecommerce_retail_th") -> dict[str, Any]:
        """Fetches the target vertical configuration from entities registry."""
        for v in self.entities.get("verticals", []):
            if v["vertical_id"] == vertical_id:
                return v
        return self.entities["verticals"][0]

    def get_control_benchmark_set(self, vertical_id: str = "ecommerce_retail_th") -> list[dict[str, Any]]:
        """Returns benchmark queries. For e-commerce uses 30 invariant queries; for others creates deterministic seed."""
        if vertical_id == "ecommerce_retail_th" and self.control_queries:
            return [
                {
                    "query_id": q.get("query_id", f"q_ctrl_{i + 1:02d}"),
                    "text_th": q.get("text_th", ""),
                    "category": q.get("category", "โปรโมชั่น"),
                    "intent": q.get("intent", "recommendation"),
                    "persona_id": "standard_shopper",
                    "persona_name": "Standard Thai Consumer",
                    "is_control_set": True,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                for i, q in enumerate(self.control_queries)
            ]
        # Deterministic control set for any vertical
        return self.generate_exploratory_queries(vertical_id=vertical_id, count=30, seed=1000, is_control=True)

    def generate_exploratory_queries(
        self, vertical_id: str = "ecommerce_retail_th", count: int = 15, seed: int = 42, is_control: bool = False
    ) -> list[dict[str, Any]]:
        """Domain-adaptive query generation across 6 Intent Pillars with seeded reproducibility."""
        rng = random.Random(seed)
        v_config = self.get_vertical_config(vertical_id)
        brands = [b["name"] for b in v_config.get("brands", [])]
        categories = v_config.get("categories", ["สินค้าและบริการยอดนิยม", "ตัวเลือกมาตรฐาน", "แพ็กเกจยอดนิยม", "รุ่นแนะนำ"])

        queries = []
        intents = list(self.domain_intent_templates.keys())

        for i in range(count):
            intent = intents[i % len(intents)]
            templates = self.domain_intent_templates[intent]
            template = rng.choice(templates)
            category = rng.choice(categories)
            budget = rng.choice(self.budgets)
            persona = (
                rng.choice(self.personas)
                if self.personas
                else {"id": "standard_shopper", "name": "Thai Digital Consumer"}
            )

            if len(brands) >= 2:
                brand_samples = rng.sample(brands, 2)
                brand_a, brand_b = brand_samples[0], brand_samples[1]
            elif len(brands) == 1:
                brand_a = brands[0]
                brand_b = "แบรนด์คู่แข่งในตลาด"
            else:
                brand_a, brand_b = "เจ้าตลาด A", "เจ้าตลาด B"

            query_text = template.format(category=category, budget=budget, brand_a=brand_a, brand_b=brand_b)

            queries.append(
                {
                    "query_id": f"q_{'ctrl' if is_control else 'exp'}_{vertical_id[:6]}_{seed}_{i + 1:03d}",
                    "text_th": query_text,
                    "vertical_id": vertical_id,
                    "category": category,
                    "intent": intent,
                    "persona_id": persona.get("id", "standard_shopper"),
                    "persona_name": persona.get("name", "Standard Thai Consumer"),
                    "is_control_set": is_control,
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "seed": seed,
                }
            )

        return queries

    def generate_queries(
        self, vertical_id: str = "ecommerce_retail_th", count: int = 30, seed: int = 42, include_control: bool = False
    ) -> list[dict[str, Any]]:
        """Generates query suite. If include_control=False, creates exploratory queries with is_control_set=False."""
        queries = []
        if include_control:
            ctrl = self.get_control_benchmark_set(vertical_id=vertical_id)
            queries.extend(ctrl)

        rem = max(0, count - len(queries))
        if rem > 0:
            exp = self.generate_exploratory_queries(vertical_id=vertical_id, count=rem, seed=seed, is_control=False)
            queries.extend(exp)

        return queries[:count]
