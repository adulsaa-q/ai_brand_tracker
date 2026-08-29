# src/prompts.py
"""Central prompt registry.

Phase 2 remediation: prompts used to be hardcoded string literals scattered
across engine modules with no version tracking. Every LLM observation now
records which prompt version produced it (persisted on fact_observation), so a
change in extraction quality can be traced to a prompt change.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    name: str
    version: str
    template: str

    def render(self, **kw: str) -> str:
        return self.template.format(**kw)

    @property
    def id(self) -> str:
        return f"{self.name}@{self.version}"


_GEMINI_BRAND_AUDIT = Prompt(
    name="gemini.brand_audit",
    version="1.1.0",
    template=(
        "คุณคือผู้ช่วยช้อปปิ้งและวิเคราะห์ตลาดไทย ตอบจากข้อมูลจริงที่ค้นเจอเท่านั้น\n"
        'คำถามจากผู้บริโภค: "{query_text}"\n\n'
        "แบรนด์/แพลตฟอร์มที่ต้องประเมิน: {brands}\n\n"
        "ตอบคำถามอย่างเป็นธรรมชาติก่อน แล้วปิดท้ายด้วย JSON block เดียวใน ```json ... ``` "
        "ที่มี key `brand_mentions` เป็น array ของ object:\n"
        "{{\n"
        '  "brand_mentions": [\n'
        "    {{\n"
        '      "brand_name": "<ชื่อแบรนด์ตามรายการข้างบน>",\n'
        '      "mentioned": true,\n'
        '      "rank": 1,\n'
        '      "recommendation_intent": "strongly_recommended|recommended|neutral_mention|not_recommended|warning_or_caution",\n'
        '      "sentiment": "positive|neutral|negative",\n'
        '      "key_strengths": ["..."],\n'
        '      "key_weaknesses": ["..."]\n'
        "    }}\n"
        "  ]\n"
        "}}\n"
        "ถ้าแบรนด์ใดไม่ถูกกล่าวถึง ให้ mentioned=false และ rank=null"
    ),
)

_GEMINI_REPAIR = Prompt(
    name="gemini.brand_audit.repair",
    version="1.0.0",
    template=(
        "จากคำตอบก่อนหน้านี้ ให้ส่งกลับเฉพาะ JSON block เดียวใน ```json ... ``` "
        "ตาม schema `brand_mentions` เท่านั้น ห้ามมีข้อความอื่น\n\n"
        "คำตอบก่อนหน้า:\n{previous}"
    ),
)

_OPENROUTER_BRAND_AUDIT = Prompt(
    name="openrouter.brand_audit",
    version="1.1.0",
    template=(
        'Consumer query (Thai): "{query_text}"\n'
        "Target brands: {brands}\n\n"
        "Return ONLY a JSON object in ```json ... ``` with key `brand_mentions`, an array of "
        "{{brand_name, mentioned, rank, recommendation_intent, sentiment, key_strengths, key_weaknesses}}. "
        "Use brand_name exactly as listed. mentioned=false and rank=null if a brand is not discussed."
    ),
)

_OPENROUTER_SYSTEM = Prompt(
    name="openrouter.system",
    version="1.0.0",
    template="You are a Thai market-intelligence analyst. Always answer with a single ```json``` block.",
)

_REGISTRY: dict[str, Prompt] = {
    p.name: p
    for p in (
        _GEMINI_BRAND_AUDIT,
        _GEMINI_REPAIR,
        _OPENROUTER_BRAND_AUDIT,
        _OPENROUTER_SYSTEM,
    )
}


def get_prompt(name: str) -> Prompt:
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Unknown prompt '{name}'. Known: {sorted(_REGISTRY)}") from exc
