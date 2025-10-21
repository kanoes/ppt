import base64
from io import BytesIO
from typing import Any, Dict, List

from pptx import Presentation

from src.services.presentation_pipeline import PresentationPipeline


class _SimpleParser:
    def parse(self, user_name: str, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        turns = conversation or []
        qa_items = []
        all_sources: List[Dict[str, str]] = []
        merged_charts: List[Dict[str, str]] = []
        for turn in turns:
            question = (turn.get("question") or {}).get("content", "")
            answer = (turn.get("answer") or {}).get("content", "")
            charts: List[Dict[str, str]] = []
            for chart in turn.get("charts", []) or []:
                encoded = chart.get("encodedImage")
                if not encoded:
                    continue
                charts.append(
                    {
                        "title": chart.get("title") or "",
                        "data_uri": f"data:image/png;base64,{encoded}",
                    }
                )
            sources = [
                {"title": src.get("title", ""), "link": src.get("link", "")}
                for src in (turn.get("sources") or [])
            ]
            qa_items.append(
                {
                    "question": question,
                    "answer": answer,
                    "charts": charts,
                    "chart_info": "\n".join(c.get("title", "") for c in charts if c.get("title")),
                    "has_charts": bool(charts),
                    "sources": sources,
                    "source_info": "\n".join(
                        f"- {src['title']}: {src['link']}" for src in sources if src.get("title") or src.get("link")
                    ),
                    "has_sources": bool(sources),
                }
            )
            all_sources.extend(sources)
            merged_charts.extend(charts)

        return {
            "title": qa_items[0]["question"] if qa_items else "レポート",
            "user_name": user_name,
            "qa_items": qa_items,
            "charts": merged_charts,
            "has_charts": any(it["has_charts"] for it in qa_items),
            "has_sources": any(it["has_sources"] for it in qa_items),
            "sources": all_sources,
            "chart_info": "",
            "source_info": "",
        }


def _dummy_chart() -> str:
    # Single pixel transparent PNG
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP8/5+hHgAGgwJ/lqukWAAAAABJRU5ErkJggg=="
    )
    return base64.b64encode(png_bytes).decode("utf-8")


def test_pipeline_generates_html_and_ppt(tmp_path):
    pipeline = PresentationPipeline(html_parser=_SimpleParser())
    conversation = [
        {
            "index": 0,
            "question": {"content": "市場動向の概要を教えてください"},
            "answer": {
                "content": "主要企業の売上は前年同期比で増加しています。\n投資家の関心も高まっています。",
            },
        }
    ]
    assets = {
        "indicatorCharts": [
            {"title": "売上推移", "encodedImage": _dummy_chart()},
        ],
        "sourceList": [
            {"title": "業界レポート", "link": "https://example.com/report"},
        ],
    }

    artifacts = pipeline.build(
        user_name="テスター",
        conversation=conversation,
        assets=assets,
    )

    assert "<section" in artifacts.html
    assert "売上推移" in artifacts.html

    ppt_bytes = artifacts.ppt_stream.getvalue()
    assert len(ppt_bytes) > 0

    presentation = Presentation(BytesIO(ppt_bytes))
    # Title + content + chart + sources slides expected
    assert len(presentation.slides) >= 3

