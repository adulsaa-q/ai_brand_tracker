import json
import os
import time
from datetime import datetime

from src.engines.base import BaseObservationEngine
from src.models.observations import BrandMentionDetail, CitationSource, RawObservation


class GeminiObservationEngine(BaseObservationEngine):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("GEMINI_API_KEY"))
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except ImportError:
                pass

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        if not self.client:
            raise RuntimeError("Gemini Client not initialized. Check GEMINI_API_KEY.")

        from google.genai import types
        start_time = time.time()
        
        prompt = f'''คุณคือผู้ช่วยช้อปปิ้งและวิเคราะห์ตลาดไทย
คำถามจากผู้บริโภค: "{query_text}"

รายชื่อแบรนด์/แพลตฟอร์มที่ต้องวิเคราะห์: {', '.join(target_brands)}

กรุณาตอบคำถามอย่างเป็นธรรมชาติโดยอ้างอิงข้อมูลจริง และสรุป JSON ใน ```json ... ```:
{{
  "brand_mentions": [
    {{
      "brand_name": "ชื่อแบรนด์",
      "mentioned": true,
      "rank": 1,
      "recommendation_intent": "strongly_recommended",
      "sentiment": "positive",
      "key_strengths": ["จุดเด่น"],
      "key_weaknesses": ["ข้อจำกัด"]
    }}
  ]
}}'''

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        latency = int((time.time() - start_time) * 1000)
        raw_text = response.text or ""
        
        citations = []
        if response.candidates and response.candidates[0].grounding_metadata:
            meta = response.candidates[0].grounding_metadata
            chunks = getattr(meta, "grounding_chunks", None) or []
            for chunk in chunks:
                web = getattr(chunk, "web", None)
                if web:
                    title = getattr(web, "title", "Web Source") or "Web Source"
                    url = getattr(web, "uri", None)
                    domain = url.split("//")[-1].split("/")[0] if url else "web"
                    citations.append(CitationSource(url=url, domain=domain, title=title, source_type="news"))

        mentions = []
        try:
            if "```json" in raw_text:
                json_str = raw_text.split("```json")[1].split("```")[0].strip()
            elif "{" in raw_text:
                json_str = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
            else:
                json_str = "{}"
            
            parsed = json.loads(json_str)
            for m in parsed.get("brand_mentions", []):
                b_name = m.get("brand_name", "")
                mentions.append(BrandMentionDetail(
                    brand_id=b_name.lower().replace(" ", "_"),
                    brand_name=b_name,
                    mentioned=m.get("mentioned", True),
                    rank=m.get("rank"),
                    recommendation_intent=m.get("recommendation_intent", "recommended"),
                    sentiment=m.get("sentiment", "neutral"),
                    key_strengths_mentioned=m.get("key_strengths", []),
                    key_weaknesses_mentioned=m.get("key_weaknesses", [])
                ))
        except Exception:
            pass

        return RawObservation(
            observation_id=f"obs_gemini_{int(time.time())}",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            engine_provider="google_gemini",
            model_name=self.model_name,
            grounding_enabled=True,
            response_raw_text=raw_text,
            response_latency_ms=latency,
            brand_mentions=mentions,
            citations=citations
        )
