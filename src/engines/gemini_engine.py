import os
import time
from datetime import datetime

from src.engines._parsing import parse_brand_mentions
from src.engines.base import BaseObservationEngine
from src.exceptions import EngineError
from src.ids import new_observation_id
from src.models.observations import CitationSource, RawObservation

_PROMPT_VERSION = "gemini.brand_audit.v1"

_PROMPT = """คุณคือผู้ช่วยช้อปปิ้งและวิเคราะห์ตลาดไทย
คำถามจากผู้บริโภค: "{query_text}"

รายชื่อแบรนด์/แพลตฟอร์มที่ต้องวิเคราะห์: {brands}

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
}}"""


class GeminiObservationEngine(BaseObservationEngine):
    prompt_version = _PROMPT_VERSION

    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("GEMINI_API_KEY"))
        self.client = None
        self._import_error: str | None = None
        if self.api_key:
            try:
                from google import genai

                self.client = genai.Client(api_key=self.api_key)
            except ImportError as exc:  # dependency genuinely missing
                self._import_error = str(exc)

    def observe(self, query_id: str, query_text: str, target_brands: list[str]) -> RawObservation:
        if not self.api_key:
            raise EngineError("Gemini engine requires GEMINI_API_KEY", {"engine": "gemini"})
        if not self.client:
            raise EngineError(
                "google-genai SDK not installed",
                {"engine": "gemini", "import_error": self._import_error},
            )

        from google.genai import types

        start_time = time.time()
        prompt = _PROMPT.format(query_text=query_text, brands=", ".join(target_brands))

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
            )
        except Exception as exc:  # provider failure - surface, do not swallow
            raise EngineError(
                f"Gemini API call failed: {exc}",
                {"engine": "gemini", "model": self.model_name, "query_id": query_id},
            ) from exc

        latency = int((time.time() - start_time) * 1000)
        raw_text = response.text or ""

        citations: list[CitationSource] = []
        if response.candidates and response.candidates[0].grounding_metadata:
            meta = response.candidates[0].grounding_metadata
            for chunk in getattr(meta, "grounding_chunks", None) or []:
                web = getattr(chunk, "web", None)
                if not web:
                    continue
                url = getattr(web, "uri", None)
                domain = url.split("//")[-1].split("/")[0] if url else "web"
                citations.append(
                    CitationSource(
                        url=url,
                        domain=domain,
                        title=getattr(web, "title", "Web Source") or "Web Source",
                        source_type="news",
                    )
                )

        mentions, parse_status = parse_brand_mentions(raw_text, query_id=query_id)
        token_count = None
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            token_count = getattr(usage, "total_token_count", None)

        return RawObservation(
            observation_id=new_observation_id("gemini"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            provider="google_genai",
            model_name=self.model_name,
            answer_surface="generative_answer",
            grounding_enabled=True,
            response_raw_text=raw_text,
            response_latency_ms=latency,
            token_count=token_count,
            parse_status=parse_status,
            brand_mentions=mentions,
            citations=citations,
        )
