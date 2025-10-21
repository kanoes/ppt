from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence

from src.logging import get_logger

logger = get_logger("deck_renderer")


@dataclass(frozen=True)
class SlideSnippet:
    """Container representing a single HTML slide snippet."""

    role: str
    body: str


class DeckHTMLRenderer:
    """Render structured conversation data into HTML slides.

    The renderer intentionally emits HTML that follows the html2pptx
    guidance so that it can be round-tripped into a PowerPoint deck.
    """

    def __init__(self, theme: str | None = None) -> None:
        self._theme = theme or "lake"
        self._palette = self._select_palette(self._theme)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render(self, content_data: Dict[str, Any]) -> str:
        """Render the full HTML document for the supplied content."""

        logger.info(
            {
                "message": "Rendering HTML deck from structured content.",
                "operation": "deck_render",
                "status": "started",
            }
        )

        slides: list[SlideSnippet] = []
        slides.append(self._title_slide(content_data))

        qa_items: Sequence[Dict[str, Any]] = content_data.get("qa_items", []) or []
        for item in qa_items:
            slides.append(self._qa_slide(item))
            slides.extend(self._chart_slides(item))

        if content_data.get("sources"):
            slides.append(self._sources_slide(content_data["sources"]))

        document = self._wrap_document(slides)

        logger.info(
            {
                "message": "Rendering HTML deck completed.",
                "operation": "deck_render",
                "status": "completed",
                "slide_count": len(slides),
            }
        )
        return document

    # ------------------------------------------------------------------
    # Slide builders
    # ------------------------------------------------------------------
    def _title_slide(self, content_data: Dict[str, Any]) -> SlideSnippet:
        title = html.escape(content_data.get("title") or "レポート")
        subtitle = html.escape(content_data.get("user_name") or "")
        highlight = html.escape(content_data.get("subtitle") or "AI Generated Presentation")

        body = f"""
<section class="slide" data-role="title">
  <div class="title-surface">
    <p class="eyebrow">{highlight}</p>
    <h1>{title}</h1>
    <p class="subtitle">{subtitle}</p>
  </div>
</section>
"""
        return SlideSnippet(role="title", body=body)

    def _qa_slide(self, item: Dict[str, Any]) -> SlideSnippet:
        question = html.escape(item.get("question") or "質問")
        answer = item.get("answer") or ""
        bullets = self._answer_to_bullets(answer)
        key_points = self._ensure_points(bullets)

        summary = html.escape(self._build_summary_sentence(answer))

        bullet_html = "\n".join(f"    <li>{html.escape(point)}</li>" for point in key_points)

        body = f"""
<section class="slide" data-role="content">
  <h2>{question}</h2>
  <p class="lead">{summary}</p>
  <ul>
{bullet_html}
  </ul>
</section>
"""
        return SlideSnippet(role="content", body=body)

    def _chart_slides(self, item: Dict[str, Any]) -> Iterable[SlideSnippet]:
        charts = item.get("charts") or []
        if not charts:
            return []

        slides: list[SlideSnippet] = []
        question = html.escape(item.get("question") or "質問")
        for idx, chart in enumerate(charts, start=1):
            title = html.escape(chart.get("title") or f"チャート{idx}")
            data_uri = chart.get("data_uri")
            if not data_uri:
                continue
            body = f"""
<section class="slide" data-role="chart">
  <h2>{question} – チャート{idx}</h2>
  <figure>
    <img src="{data_uri}" alt="{title}" />
    <figcaption>{title}</figcaption>
  </figure>
</section>
"""
            slides.append(SlideSnippet(role="chart", body=body))
        return slides

    def _sources_slide(self, sources: Sequence[Dict[str, Any]]) -> SlideSnippet:
        items = [
            f"    <li><a href=\"{html.escape(src.get('link') or '#')}\">{html.escape(src.get('title') or '情報源')}</a></li>"
            for src in sources
            if src.get("link") or src.get("title")
        ]
        if not items:
            items.append("    <li>引用元情報は提供されませんでした。</li>")

        body = """
<section class="slide" data-role="sources">
  <h2>引用元</h2>
  <ul>
{items}
  </ul>
</section>
"""
        body = body.replace("{items}", "\n".join(items))
        return SlideSnippet(role="sources", body=body)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _wrap_document(self, slides: Sequence[SlideSnippet]) -> str:
        palette = self._palette
        slide_markup = "\n".join(slide.body.strip() for slide in slides)
        return f"""<!DOCTYPE html>
<html lang=\"ja\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Auto Generated Presentation</title>
    <style>
      html {{ background: {palette['surface']}; }}
      body {{
        margin: 0;
        padding: 32pt 16pt;
        font-family: Arial, Helvetica, sans-serif;
        background: {palette['surface']};
        color: {palette['ink']};
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 24pt;
      }}
      .slide {{
        width: 720pt;
        height: 405pt;
        box-sizing: border-box;
        padding: 36pt 42pt;
        background: {palette['card']};
        border: 2pt solid {palette['stroke']};
        border-radius: 12pt;
        box-shadow: 0 8pt 24pt rgba(15, 23, 42, 0.1);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        gap: 18pt;
      }}
      .slide h1 {{ font-size: 40pt; margin: 0; color: {palette['accent']}; }}
      .slide h2 {{ font-size: 28pt; margin: 0; color: {palette['accent']}; }}
      .slide p {{ font-size: 18pt; line-height: 1.5; margin: 0; }}
      .slide p.lead {{ font-size: 20pt; font-weight: bold; color: {palette['ink']}; }}
      .slide ul {{ margin: 0; padding-left: 24pt; display: flex; flex-direction: column; gap: 8pt; }}
      .slide li {{ font-size: 18pt; }}
      .slide figure {{ margin: 0; display: flex; flex-direction: column; gap: 12pt; align-items: center; }}
      .slide figure img {{ max-width: 620pt; max-height: 280pt; border-radius: 12pt; box-shadow: 0 6pt 18pt rgba(15, 23, 42, 0.14); }}
      .slide figure figcaption {{ font-size: 16pt; color: {palette['muted']}; }}
      .title-surface {{ margin-top: 48pt; display: flex; flex-direction: column; gap: 16pt; }}
      .eyebrow {{ text-transform: uppercase; letter-spacing: 4pt; font-size: 14pt; color: {palette['muted']}; }}
      .subtitle {{ font-size: 20pt; color: {palette['ink']}; }}
      a {{ color: {palette['accent']}; }}
    </style>
  </head>
  <body>
{slide_markup}
  </body>
</html>
"""

    def _answer_to_bullets(self, answer: str | None) -> List[str]:
        if not answer:
            return []
        text = answer.replace("\r", "\n").strip()
        if not text:
            return []
        segments: list[str] = []
        for raw_line in text.split("\n"):
            candidate = raw_line.strip()
            if not candidate:
                continue
            candidate = re.sub(r"^[\u30fb\-\*\s]+", "", candidate)
            segments.extend(self._split_sentence(candidate))
        return [seg for seg in segments if seg]

    def _split_sentence(self, sentence: str) -> List[str]:
        sentence = sentence.strip()
        if not sentence:
            return []
        parts = re.split(r"[。.!?]\s*", sentence)
        return [part.strip() for part in parts if part.strip()]

    def _ensure_points(self, points: Sequence[str]) -> List[str]:
        out = [point for point in points if point]
        if not out:
            out.append("回答内容は提供されませんでした。")
        return out[:6]

    def _build_summary_sentence(self, answer: str | None) -> str:
        if not answer:
            return "回答概要がありません。"
        summary_candidates = self._split_sentence(answer)
        return summary_candidates[0] if summary_candidates else "回答概要がありません。"

    def _select_palette(self, theme: str) -> Dict[str, str]:
        palettes = {
            "lake": {
                "surface": "#f0f4f8",
                "card": "#ffffff",
                "stroke": "#cbd5f5",
                "accent": "#1e3a8a",
                "ink": "#0f172a",
                "muted": "#475569",
            },
            "dusk": {
                "surface": "#f4f1ff",
                "card": "#ffffff",
                "stroke": "#d8ccff",
                "accent": "#5b21b6",
                "ink": "#1f2937",
                "muted": "#6b7280",
            },
        }
        return palettes.get(theme, palettes["lake"])

