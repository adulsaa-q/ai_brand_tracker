from datetime import date
from typing import Any


class ThailandTemporalEngine:
    """Injects Thailand-specific retail, cultural, and promotional events into query generation."""

    EVENTS = [
        {"id": "double_day", "name_th": "แคมเปญ Double Day (เช่น 8.8, 9.9, 11.11)", "months": list(range(1, 13)), "multiplier": 2.5, "intent": "deal_seeking"},
        {"id": "payday_sale", "name_th": "แคมเปญ Payday สิ้นเดือน (25-30 ของทุกเดือน)", "months": list(range(1, 13)), "multiplier": 1.8, "intent": "deal_seeking"},
        {"id": "mid_year_sale", "name_th": "Mid-Year Mega Sale (มิถุนายน-กรกฎาคม)", "months": [6, 7], "multiplier": 1.5, "intent": "comparison"},
        {"id": "songkran_summer", "name_th": "เทศกาลสงกรานต์ / หน้าร้อน (เมษายน)", "months": [4], "multiplier": 2.0, "focus_categories": ["กันแดดคุมมัน", "เครื่องสำอางกันน้ำ", "สกินแคร์กู้ผิวไหม้แดด"]},
        {"id": "back_to_school", "name_th": "เปิดเทอม / Back to School (พฤษภาคม-มิถุนายน)", "months": [5, 6], "multiplier": 1.3, "focus_categories": ["สกินแคร์นักเรียน", "เครื่องสำอางราคาประหยัด"]},
        {"id": "11_11_mega_sale", "name_th": "มหกรรม 11.11 Global Festival (พฤศจิกายน)", "months": [11], "multiplier": 3.0, "intent": "deal_seeking"},
        {"id": "12_12_year_end", "name_th": "แคมเปญส่งท้ายปี 12.12 & ของขวัญปีใหม่ (ธันวาคม)", "months": [12], "multiplier": 2.8, "focus_categories": ["ของขวัญ", "น้ำหอมแท้", "เซ็ตสกินแคร์เคาน์เตอร์แบรนด์"]}
    ]

    @classmethod
    def get_active_events(cls, target_date: date = None) -> list[dict[str, Any]]:
        target = target_date or date.today()
        m = target.month
        active = []
        for e in cls.EVENTS:
            if m in e.get("months", []):
                active.append(e)
        return active

    @classmethod
    def get_event_query_modifiers(cls, target_date: date = None) -> list[str]:
        events = cls.get_active_events(target_date)
        modifiers = []
        for e in events:
            if e["id"] == "double_day":
                modifiers.extend(["โปรโมชั่น Double Day วันเบิ้ล", "แจกโค้ดส่วนลด 8.8 / 9.9"])
            elif e["id"] == "payday_sale":
                modifiers.extend(["โปรเงินเดือนออก Payday", "โค้ดลดสิ้นเดือน"])
            elif e["id"] == "songkran_summer":
                modifiers.extend(["กันน้ำเล่นน้ำสงกรานต์", "กันแดดหน้าร้อนเหงื่อออกไม่เยิ้ม"])
            elif e["id"] == "12_12_year_end":
                modifiers.extend(["ของขวัญปีใหม่แพ็กเกจสวย", "ลดส่งท้ายปี 12.12"])
        return modifiers
