"""HTML content parsing and rendering utilities."""

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from html.generator.utils import HTMLLLMInvoker
from html.prompt.html_generator_prompt import html_generator_prompt
from shared.logging import get_logger

load_dotenv()

# ログ設定
logger = get_logger("html_generator")

# 環境変数からデフォルト値を取得
default_deployment = os.getenv("DEFAULT_LLM_DEPLOYMENT", "gpt-5")
default_temperature = float(os.getenv("DEFAULT_LLM_TEMPERATURE", "1"))


class HTMLContentParser:
    """
    ユーザー入力を解析し、HTML生成用の構造化データに変換するクラス
    """

    def __init__(self, llm_invoker: Optional[HTMLLLMInvoker] = None) -> None:
        self.llm_invoker = llm_invoker or HTMLLLMInvoker(
            deployment_name=default_deployment,
            temperature=default_temperature,
            json_mode=False
        )

    def _charts_to_data_uri(self, charts_any) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        if not charts_any:
            return out
        for c in charts_any:
            d = c.dict() if hasattr(c, "dict") else c
            if not isinstance(d, dict):
                continue
            enc = d.get("encodedImage")
            if not enc:
                continue
            title = d.get("title") or d.get("label") or "タイトルなし"
            out.append({"title": str(title), "data_uri": f"data:image/png;base64,{enc}"})
        return out

    def _sources_normalize(self, src_any) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        if not src_any:
            return out
        for s in src_any:
            d = s if isinstance(s, dict) else {"title": "", "link": ""}
            if not isinstance(d, dict):
                continue
            title = d.get("title")
            if not title:
                tp = d.get("type", "source")
                pg = d.get("page")
                title = f"[{tp}]{f' p.{pg}' if pg else ''}".strip()
            link = d.get("link_pdf") or d.get("link_img") or d.get("link") or ""
            out.append({"title": str(title), "link": str(link)})
        return out

    def _build_item(self, t: Dict[str, Any], user_name: str) -> Dict[str, Any]:
        q = ((t.get("question") or {}).get("content") or "（タイトルなし）").strip()
        a = ((t.get("answer") or {}).get("content") or "（回答なし）").strip()

        charts = self._charts_to_data_uri(t.get("charts"))
        chart_info = "\n".join([f"チャート{idx+1}: {c['title']}" for idx, c in enumerate(charts)]) if charts else ""

        sources = self._sources_normalize(t.get("sources"))
        source_info = "\n".join([f"- {s['title']}: {s['link']}" for s in sources]) if sources else ""

        return {
            "question": q,
            "user_name": user_name,
            "answer": a,
            "charts": charts,
            "chart_info": chart_info,
            "sources": sources,
            "source_info": source_info,
            "has_charts": bool(charts),
            "has_sources": bool(sources),
        }

    def parse(self, user_name: str, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info({
            "message": "HTMLコンテンツの解析を開始します（conversation統一）。",
            "operation": "html_parse",
            "status": "started",
        })

        try:
            turns = sorted(
                conversation or [],
                key=lambda t: (0, t.get("index")) if isinstance(t.get("index"), int) else (1, 10**9),
            )
            if not turns:
                turns = [{"question": {"content": "レポート"}, "answer": {"content": ""}}]

            qa_items = [self._build_item(t, user_name) for t in turns]

            title_q = qa_items[0]["question"]
            if len(qa_items) > 1:
                title_q = f"{title_q} など（全{len(qa_items)}件）"

            merged_charts = [c for it in qa_items for c in it["charts"]]
            has_any_charts = any(it["has_charts"] for it in qa_items)
            has_any_sources = any(it["has_sources"] for it in qa_items)

            content_data = {
                "title": title_q,
                "user_name": user_name,
                "qa_items": qa_items,
                "charts": merged_charts,
                "has_charts": has_any_charts,
                "has_sources": has_any_sources,
                "chart_info": "\n".join([it["chart_info"] for it in qa_items if it["chart_info"]]),
                "source_info": "\n".join([it["source_info"] for it in qa_items if it["source_info"]]),
            }

            logger.info({
                "message": "HTMLコンテンツの解析が完了しました。",
                "operation": "html_parse",
                "status": "completed",
            })
            return content_data

        except Exception as e:
            logger.error({
                "message": "HTMLコンテンツの解析中にエラーが発生しました。",
                "error_message": str(e),
                "status": "problem",
            })
            raise


class HTMLGenerator:
    def __init__(self, llm_invoker: Optional[HTMLLLMInvoker] = None,
                 prompt: Optional[str] = None) -> None:
        self.llm_invoker = llm_invoker or HTMLLLMInvoker(
            deployment_name=default_deployment,
            temperature=default_temperature,
            json_mode=False
        )
        self._prompt: str = prompt or html_generator_prompt

    def generate(self, content_data: Dict[str, Any]) -> str:
        logger.info({"message": "HTML文書の生成を開始します。", "operation": "html_generate", "status": "started"})

        try:
            qa_items = content_data.get("qa_items", []) or []

            def _nz(v: Any) -> str:
                s = v if isinstance(v, str) else ""
                return s.strip() or "（なし）"

            qa_sections_parts: list[str] = []
            for i, it in enumerate(qa_items, start=1):
                qa_sections_parts.append(
                    "\n".join([
                        f"QA{i}",
                        f"* 質問: { _nz(it.get('question')) }",
                        f"* 回答: { _nz(it.get('answer')) }",
                        f"* チャート一覧: { _nz(it.get('chart_info')) }",
                        f"* 引用元: { _nz(it.get('source_info')) }",
                        f"* has_charts: { str(bool(it.get('has_charts'))).lower() }",
                        f"* has_sources: { str(bool(it.get('has_sources'))).lower() }",
                    ])
                )
            qa_sections_text = "\n\n".join(qa_sections_parts) if qa_sections_parts else "QA1\n* 質問: （なし）\n* 回答: （なし）\n* チャート一覧: （なし）\n* 引用元: （なし）\n* has_charts: false\n* has_sources: false"

            payload = {
                "qa_sections": qa_sections_text,
                "has_charts": bool(content_data.get("has_charts", False)),
                "has_sources": bool(content_data.get("has_sources", False)),
                "title": content_data.get("title", "レポート"),
                "user_name": content_data.get("user_name", ""),
                "source_info": content_data.get("source_info", ""),
            }

            base_prompt_text = self._prompt.format(**payload)
            logger.info(f"base_prompt_text: {base_prompt_text}")

            html_content = self.llm_invoker.invoke(base_prompt_text)

            if not isinstance(html_content, str):
                raise TypeError("LLMからの応答が文字列ではありません。")

            t = html_content.strip()
            if t.startswith("```html"):
                t = t[len("```html"):].lstrip()
            elif t.startswith("```"):
                t = t[len("```"):].lstrip()
            if t.endswith("```"):
                t = t[:-3].rstrip()
            html_content = t

            if ("<!doctype" not in html_content.lower()) and ("<html" not in html_content.lower()):
                logger.warning({"message": "LLM出力が完全なHTMLではないため外枠でラップします。"})
                html_content = (
                    "<!DOCTYPE html><html lang='ja'><head>"
                    "<meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
                    "<title>Report</title></head><body>"
                    f"{html_content}</body></html>"
                )

            html_content = self._inject_images_at_anchor(
                html_content,
                content_data.get("charts", []) or []
            )

            logger.info({"message": "HTML文書の生成が完了しました。", "operation": "html_generate", "status": "completed"})
            return html_content

        except Exception as e:
            logger.error({"message": "HTML文書の生成中にエラーが発生しました。", "operation": "html_generate", "error_message": str(e), "status": "problem"})
            raise

    def _inject_images_at_anchor(self, html: str, charts: list[dict]) -> str:
        """
        <!--CHARTS--> を、名前空間付きクラス（charts-embed …）で置換する。
        これにより LLM 側のグローバル CSS と干渉しにくくする。
        """
        valid = [c for c in (charts or []) if c.get("data_uri")]
        if not valid:
            return html.replace("<!--CHARTS-->", "")

        def esc(t: str) -> str:
            t = (t or "")
            return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def fig(c):
            title = esc(c.get("title", ""))
            return (
                f'<figure class="chart-fig">'
                f'  <img class="chart-img" src="{c["data_uri"]}" alt="{title}" loading="lazy" decoding="async" />'
                f'  <figcaption class="chart-cap">{title}</figcaption>'
                f'</figure>'
            )

        n = len(valid)
        if n == 1:
            body = (
                '<section class="charts-embed chart-hero" aria-labelledby="charts-heading">'
                '  <h2 id="charts-heading">チャート</h2>'
                f'  {fig(valid[0])}'
                '</section>'
            )
        elif n == 2:
            body = (
                '<section class="charts-embed chart-split" aria-labelledby="charts-heading">'
                '  <h2 id="charts-heading">チャート</h2>'
                '  <div class="chart-split-wrap">'
                f'    {fig(valid[0])}{fig(valid[1])}'
                '  </div>'
                '</section>'
            )
        else:
            figures = "\n".join(fig(c) for c in valid)
            body = (
                '<section class="charts-embed chart-gallery" aria-labelledby="charts-heading">'
                '  <h2 id="charts-heading">チャート</h2>'
                f'  <div class="chart-gallery-wrap">{figures}</div>'
                '</section>'
            )

        if "<!--CHARTS-->" in html:
            return html.replace("<!--CHARTS-->", body)

        low = html.lower()
        if "</body>" in low:
            idx = low.rfind("</body>")
            return html[:idx] + body + html[idx:]
        return html + body
