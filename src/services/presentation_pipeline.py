from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, List, Sequence

from src.logging import get_logger
from src.services.html_generator.html_generator import HTMLContentParser
from src.services.html_deck.deck_renderer import DeckHTMLRenderer
from src.services.html_to_ppt.converter import HTMLToPPTXConverter

logger = get_logger("presentation_pipeline")


@dataclass(slots=True)
class PresentationArtifacts:
    html: str
    ppt_stream: BytesIO
    content_data: Dict[str, Any]


class PresentationPipeline:
    """High-level orchestrator that turns conversations into PPT/HTML."""

    def __init__(
        self,
        html_parser: HTMLContentParser | None = None,
        deck_renderer: DeckHTMLRenderer | None = None,
        ppt_converter: HTMLToPPTXConverter | None = None,
    ) -> None:
        self.html_parser = html_parser or HTMLContentParser()
        self.deck_renderer = deck_renderer or DeckHTMLRenderer()
        self.ppt_converter = ppt_converter or HTMLToPPTXConverter()

    def build(
        self,
        *,
        user_name: str,
        conversation: Sequence[Dict[str, Any]],
        assets: Dict[str, Any] | None = None,
    ) -> PresentationArtifacts:
        logger.info(
            {
                "message": "Starting presentation pipeline.",
                "user_name": user_name,
                "status": "started",
            }
        )

        normalized_conversation = self._prepare_conversation(conversation, assets)

        content_data = self.html_parser.parse(
            user_name=user_name,
            conversation=normalized_conversation,
        )
        content_data.setdefault("subtitle", "Generated market insights")

        html_document = self.deck_renderer.render(content_data)
        ppt_stream = self.ppt_converter.convert(html_document)

        logger.info(
            {
                "message": "Presentation pipeline completed.",
                "user_name": user_name,
                "status": "completed",
                "slides": len(content_data.get("qa_items", []) or []),
            }
        )

        return PresentationArtifacts(
            html=html_document,
            ppt_stream=ppt_stream,
            content_data=content_data,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _prepare_conversation(
        self,
        conversation: Sequence[Dict[str, Any]],
        assets: Dict[str, Any] | None,
    ) -> List[Dict[str, Any]]:
        turns = [self._to_plain_dict(item) for item in conversation or []]
        if not turns:
            turns = [
                {
                    "index": 0,
                    "question": {"content": "レポート"},
                    "answer": {"content": ""},
                }
            ]
        self._merge_assets_into_turns(turns, assets or {})
        return turns

    def _merge_assets_into_turns(
        self,
        turns: List[Dict[str, Any]],
        assets: Dict[str, Any],
    ) -> None:
        if not turns:
            return
        first = turns[0]
        sources = self._extract_sources(assets)
        if sources:
            existing = first.get("sources") if isinstance(first.get("sources"), list) else []
            first["sources"] = list(existing) + sources
        charts = self._extract_charts(assets)
        if charts:
            existing_charts = first.get("charts") if isinstance(first.get("charts"), list) else []
            first["charts"] = list(existing_charts) + charts

    def _extract_sources(self, assets: Dict[str, Any]) -> List[Dict[str, str]]:
        src_list = assets.get("sourceList")
        results: List[Dict[str, str]] = []
        if not src_list:
            return results
        for entry in src_list:
            data = self._to_plain_dict(entry)
            title = str(data.get("title") or data.get("name") or "")
            link = str(
                data.get("link")
                or data.get("link_pdf")
                or data.get("link_img")
                or data.get("url")
                or ""
            )
            if title or link:
                results.append({"title": title or link, "link": link})
        return results

    def _extract_charts(self, assets: Dict[str, Any]) -> List[Dict[str, str]]:
        charts = assets.get("indicatorCharts")
        results: List[Dict[str, str]] = []
        if not charts:
            return results
        for entry in charts:
            data = self._to_plain_dict(entry)
            encoded = data.get("encodedImage")
            if not encoded:
                continue
            title = data.get("title") or data.get("label") or ""
            results.append({"title": title, "encodedImage": encoded})
        return results

    def _to_plain_dict(self, value: Any) -> Dict[str, Any]:
        if isinstance(value, dict):
            return deepcopy(value)
        if hasattr(value, "model_dump"):
            return dict(value.model_dump())  # type: ignore[call-arg]
        if hasattr(value, "dict"):
            return dict(value.dict())  # type: ignore[call-arg]
        return deepcopy(dict(value)) if value is not None else {}

