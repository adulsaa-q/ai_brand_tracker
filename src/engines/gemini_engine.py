import os
import time
from datetime import datetime

from src.engines._http import retry_call
from src.engines._parsing import parse_brand_mentions
from src.engines.base import BaseObservationEngine
from src.exceptions import EngineError
from src.ids import new_observation_id
from src.logger import get_logger
from src.models.observations import CitationSource, RawObservation
from src.prompts import get_prompt

logger = get_logger("engine.gemini")


class GeminiObservationEngine(BaseObservationEngine):
    def __init__(self, model_name: str = "gemini-2.5-flash", api_key: str | None = None):
        super().__init__(model_name, api_key or os.getenv("GEMINI_API_KEY"))
        self.client = None
        self._import_error: str | None = None
        self._prompt = get_prompt("gemini.brand_audit")
        self._repair_prompt = get_prompt("gemini.brand_audit.repair")
        if self.api_key:
            try:
                from google import genai

                self.client = genai.Client(api_key=self.api_key)
            except ImportError as exc:
                self._import_error = str(exc)

    def _generate(self, prompt: str):
        from google.genai import types

        return self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
        )

    def observe(
        self,
        query_id: str,
        query_text: str,
        target_brands: list[str],
        brand_aliases: dict[str, list[str]] | None = None,
    ) -> RawObservation:
        if not self.api_key:
            raise EngineError("Gemini engine requires GEMINI_API_KEY", {"engine": "gemini"})
        if not self.client:
            raise EngineError(
                "google-genai SDK not installed", {"engine": "gemini", "import_error": self._import_error}
            )

        start_time = time.time()
        prompt = self._prompt.render(query_text=query_text, brands=_brand_list(target_brands, brand_aliases))
        response, retries = retry_call(lambda: self._generate(prompt), engine="gemini")

        raw_text = response.text or ""
        citations = _extract_citations(response)
        mentions, parse_status = parse_brand_mentions(raw_text, query_id=query_id)

        # one bounded repair attempt if the model did not return usable JSON
        if parse_status != "ok":
            logger.info("Gemini parse_status=%s for %s, attempting repair", parse_status, query_id)
            repair = self._repair_prompt.render(previous=raw_text[:4000])
            try:
                repair_resp, r2 = retry_call(lambda: self._generate(repair), engine="gemini", max_retries=1)
                retries += r2 + 1
                repaired, repaired_status = parse_brand_mentions(repair_resp.text or "", query_id=query_id)
                if repaired_status == "ok":
                    mentions, parse_status = repaired, "ok"
            except EngineError as exc:
                logger.warning("Gemini repair failed for %s: %s", query_id, exc)

        latency = int((time.time() - start_time) * 1000)
        usage = getattr(response, "usage_metadata", None)
        token_count = getattr(usage, "total_token_count", None) if usage is not None else None

        return RawObservation(
            observation_id=new_observation_id("gemini"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            query_id=query_id,
            query_text=query_text,
            provider="google_genai",
            model_name=self.model_name,
            answer_surface="generative_answer",
            grounding_enabled=True,
            prompt_version=self._prompt.id,
            retry_count=retries,
            response_raw_text=raw_text,
            response_latency_ms=latency,
            token_count=token_count,
            parse_status=parse_status,
            brand_mentions=mentions,
            citations=citations,
        )


def _brand_list(names: list[str], aliases: dict[str, list[str]] | None) -> str:
    """Render brands with their alt spellings so the model recognises Thai / short forms."""
    parts = []
    for n in names:
        alts = [a for a in (aliases or {}).get(n, []) if a and a.lower() != n.lower()]
        parts.append(f"{n} ({', '.join(alts)})" if alts else n)
    return "; ".join(parts)


def _extract_citations(response) -> list[CitationSource]:
    out: list[CitationSource] = []
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return out
    meta = getattr(candidates[0], "grounding_metadata", None)
    if not meta:
        return out
    for chunk in getattr(meta, "grounding_chunks", None) or []:
        web = getattr(chunk, "web", None)
        if not web:
            continue
        url = getattr(web, "uri", None)
        title = getattr(web, "title", "") or ""
        host = url.split("//")[-1].split("/")[0].lower() if url else ""
        # Gemini grounding returns Vertex redirect URLs, not the real source host.
        # In that case the source site is carried in `web.title` (e.g. "pantip.com").
        if not host or "vertexaisearch" in host or "grounding-api-redirect" in (url or ""):
            domain = title.strip().lower() or "google-grounding"
        else:
            domain = host.removeprefix("www.")
        out.append(CitationSource(url=url, domain=domain, title=title or "Web Source", source_type="news"))
    return out
