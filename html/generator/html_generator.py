"""High-level helpers for parsing conversation data and producing HTML."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from html.generator.utils import HTMLLLMInvoker
from html.prompt.html_generator_prompt import html_generator_prompt
from shared.config import settings
from shared.logging import get_logger

logger = get_logger("html_generator")


def _safe_strip(value: Any, fallback: str) -> str:
    """Return a trimmed string or a fallback description."""

    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else fallback
    return fallback


class HTMLContentParser:
    """Transform user conversations into structured data for HTML generation."""

    def __init__(self, llm_invoker: Optional[HTMLLLMInvoker] = None) -> None:
        self.llm_invoker = llm_invoker or HTMLLLMInvoker(
            deployment_name=settings.default_llm_deployment,
            temperature=settings.html_llm_temperature,
            json_mode=False,
        )

    def _charts_to_data_uri(self, charts_any: Any) -> List[Dict[str, str]]:
        charts: List[Dict[str, str]] = []
        if not charts_any:
            return charts
        for chart in charts_any:
            data = chart.dict() if hasattr(chart, "dict") else chart
            if not isinstance(data, dict):
                continue
            encoded = data.get("encodedImage")
            if not encoded:
                continue
            title = data.get("title") or data.get("label") or "Untitled chart"
            charts.append({
                "title": str(title),
                "data_uri": f"data:image/png;base64,{encoded}",
            })
        return charts

    def _sources_normalize(self, src_any: Any) -> List[Dict[str, str]]:
        sources: List[Dict[str, str]] = []
        if not src_any:
            return sources
        for source in src_any:
            data = source if isinstance(source, dict) else {"title": "", "link": ""}
            if not isinstance(data, dict):
                continue
            title = data.get("title")
            if not title:
                source_type = data.get("type", "source")
                page = data.get("page")
                title = f"[{source_type}]{f' p.{page}' if page else ''}".strip()
            link = data.get("link_pdf") or data.get("link_img") or data.get("link") or ""
            sources.append({"title": str(title), "link": str(link)})
        return sources

    def _build_item(self, turn: Dict[str, Any], user_name: str) -> Dict[str, Any]:
        question = _safe_strip((turn.get("question") or {}).get("content"), "Untitled question")
        answer = _safe_strip((turn.get("answer") or {}).get("content"), "No answer")

        charts = self._charts_to_data_uri(turn.get("charts"))
        chart_info = "\n".join([f"Chart {idx + 1}: {chart['title']}" for idx, chart in enumerate(charts)]) if charts else ""

        sources = self._sources_normalize(turn.get("sources"))
        source_info = "\n".join([f"- {source['title']}: {source['link']}" for source in sources]) if sources else ""

        return {
            "question": question,
            "user_name": user_name,
            "answer": answer,
            "charts": charts,
            "chart_info": chart_info,
            "sources": sources,
            "source_info": source_info,
            "has_charts": bool(charts),
            "has_sources": bool(sources),
        }

    def parse(self, user_name: str, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info({
            "message": "Parsing conversation payload for HTML generation",
            "operation": "html_parse",
            "status": "started",
        })

        try:
            turns = sorted(
                conversation or [],
                key=lambda turn: (0, turn.get("index")) if isinstance(turn.get("index"), int) else (1, 10**9),
            )
            if not turns:
                turns = [{"question": {"content": "Report"}, "answer": {"content": ""}}]

            items = [self._build_item(turn, user_name) for turn in turns]

            title_question = items[0]["question"]
            if len(items) > 1:
                title_question = f"{title_question} and others (total {len(items)} items)"

            merged_charts = [chart for item in items for chart in item["charts"]]
            has_any_charts = any(item["has_charts"] for item in items)
            has_any_sources = any(item["has_sources"] for item in items)

            content_data = {
                "title": title_question,
                "user_name": user_name,
                "qa_items": items,
                "charts": merged_charts,
                "has_charts": has_any_charts,
                "has_sources": has_any_sources,
                "chart_info": "\n".join([item["chart_info"] for item in items if item["chart_info"]]),
                "source_info": "\n".join([item["source_info"] for item in items if item["source_info"]]),
            }

            logger.info({
                "message": "Conversation parsed for HTML generation",
                "operation": "html_parse",
                "status": "completed",
            })
            return content_data
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error({
                "message": "Failed to parse HTML content payload",
                "operation": "html_parse",
                "error_message": str(exc),
                "status": "problem",
            })
            raise


class HTMLGenerator:
    """Render structured content into an HTML document using the LLM."""

    def __init__(
        self,
        llm_invoker: Optional[HTMLLLMInvoker] = None,
        prompt: Optional[str] = None,
    ) -> None:
        self.llm_invoker = llm_invoker or HTMLLLMInvoker(
            deployment_name=settings.default_llm_deployment,
            temperature=settings.html_llm_temperature,
            json_mode=False,
        )
        self._prompt: str = prompt or html_generator_prompt

    def _build_prompt_payload(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        qa_items = content_data.get("qa_items", []) or []
        qa_sections: list[str] = []

        for index, item in enumerate(qa_items, start=1):
            qa_sections.append(
                "\n".join(
                    [
                        f"QA{index}",
                        f"* Question: {_safe_strip(item.get('question'), 'N/A')}",
                        f"* Answer: {_safe_strip(item.get('answer'), 'N/A')}",
                        f"* Charts: {_safe_strip(item.get('chart_info'), 'None')}",
                        f"* Sources: {_safe_strip(item.get('source_info'), 'None')}",
                        f"* has_charts: {str(bool(item.get('has_charts'))).lower()}",
                        f"* has_sources: {str(bool(item.get('has_sources'))).lower()}",
                    ]
                )
            )

        if qa_sections:
            qa_sections_text = "\n\n".join(qa_sections)
        else:
            qa_sections_text = (
                "QA1\n* Question: None\n* Answer: None\n* Charts: None\n"
                "* Sources: None\n* has_charts: false\n* has_sources: false"
            )

        return {
            "qa_sections": qa_sections_text,
            "has_charts": bool(content_data.get("has_charts", False)),
            "has_sources": bool(content_data.get("has_sources", False)),
            "title": content_data.get("title", "Report"),
            "user_name": content_data.get("user_name", ""),
            "source_info": content_data.get("source_info", ""),
        }

    def generate(self, content_data: Dict[str, Any]) -> str:
        logger.info({
            "message": "Generating HTML document with LLM",
            "operation": "html_generate",
            "status": "started",
        })

        try:
            payload = self._build_prompt_payload(content_data)
            base_prompt_text = self._prompt.format(**payload)
            logger.debug({"message": "Prepared HTML prompt", "prompt_preview": base_prompt_text[:2000]})

            html_content = self.llm_invoker.invoke(base_prompt_text)

            if not isinstance(html_content, str):
                raise TypeError("LLM response is not a string.")

            text = html_content.strip()
            if text.startswith("```html"):
                text = text[len("```html"):].lstrip()
            elif text.startswith("```"):
                text = text[len("```"):].lstrip()
            if text.endswith("```"):
                text = text[:-3].rstrip()

            if ("<!doctype" not in text.lower()) and ("<html" not in text.lower()):
                logger.warning({
                    "message": "LLM output was not a full HTML document; wrapping in boilerplate",
                })
                text = (
                    "<!DOCTYPE html><html lang='en'><head>"
                    "<meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
                    "<title>Report</title></head><body>"
                    f"{text}</body></html>"
                )

            text = self._inject_images_at_anchor(text, content_data.get("charts", []) or [])

            logger.info({
                "message": "HTML document generated",
                "operation": "html_generate",
                "status": "completed",
            })
            return text
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error({
                "message": "Failed to generate HTML document",
                "operation": "html_generate",
                "error_message": str(exc),
                "status": "problem",
            })
            raise

    def _inject_images_at_anchor(self, html: str, charts: list[dict]) -> str:
        """Replace the <!--CHARTS--> placeholder with chart markup."""

        valid_charts = [chart for chart in (charts or []) if chart.get("data_uri")]
        if not valid_charts:
            return html.replace("<!--CHARTS-->", "")

        def escape(text: str) -> str:
            escaped = (text or "")
            return escaped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def figure_markup(chart: dict) -> str:
            title = escape(chart.get("title", ""))
            return (
                f'<figure class="chart-fig">'
                f'  <img class="chart-img" src="{chart["data_uri"]}" alt="{title}" '
                f'loading="lazy" decoding="async" />'
                f'  <figcaption class="chart-cap">{title}</figcaption>'
                f'</figure>'
            )

        count = len(valid_charts)
        if count == 1:
            body = (
                '<section class="charts-embed chart-hero" aria-labelledby="charts-heading">'
                '  <h2 id="charts-heading">Charts</h2>'
                f'  {figure_markup(valid_charts[0])}'
                '</section>'
            )
        elif count == 2:
            body = (
                '<section class="charts-embed chart-split" aria-labelledby="charts-heading">'
                '  <h2 id="charts-heading">Charts</h2>'
                '  <div class="chart-split-wrap">'
                f'    {figure_markup(valid_charts[0])}{figure_markup(valid_charts[1])}'
                '  </div>'
                '</section>'
            )
        else:
            figures = "\n".join(figure_markup(chart) for chart in valid_charts)
            body = (
                '<section class="charts-embed chart-gallery" aria-labelledby="charts-heading">'
                '  <h2 id="charts-heading">Charts</h2>'
                f'  <div class="chart-gallery-wrap">{figures}</div>'
                '</section>'
            )

        if "<!--CHARTS-->" in html:
            return html.replace("<!--CHARTS-->", body)

        lowercase_html = html.lower()
        if "</body>" in lowercase_html:
            index = lowercase_html.rfind("</body>")
            return html[:index] + body + html[index:]
        return html + body
