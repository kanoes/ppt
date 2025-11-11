import io
import json
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from pptx import Presentation

from ppt_app.generator.slide_generate import (
    ChartSlideFactory,
    NormalSlideFactory,
    ReferenceSlideFactory,
    TitleSlideFactory,
)
from ppt_app.generator.utils import LLMInvoker, PPTUtils
from ppt_app.prompt.content_parser_prompt import content_parser_prompt
from ppt_app.prompt.content_parser_prompt_without_chart import (
    content_parser_prompt_without_chart,
)
from shared.logging import get_logger


# ログ設定
logger = get_logger("pres_generator")


class ContentParser:
    """
    ユーザー入力を解析し、標準化されたリスト形式に変換するクラス
    """

    def __init__(self, llm_invoker: Optional[LLMInvoker] = None) -> None:
        # デフォルト設定またはユーザー指定の設定を使用
        self.llm_invoker = llm_invoker or LLMInvoker(json_mode=True)

    def parse(
            self,
            user_name: str,
            conversation: List[Dict[str, Any]],
            decoded_charts: Optional[List[Dict[str, Any]]] = None,
            source_list: Optional[List[Dict[str, str]]] = None,
        ) -> List[Dict[str, Any]]:
            logger.info({
                "message": "入力の解析を開始します。",
                "operation": "input_parse",
                "status": "started",
            })

            try:
                turns = conversation or []
                # index があれば昇順、なければ元順
                def _key(t):
                    idx = t.get("index")
                    return (0, idx) if isinstance(idx, int) else (1, len(turns))

                turns = sorted(turns, key=_key)

                def _nz(s: Optional[str]) -> str:
                    return (s or "").strip()

                def _get_q(t) -> str:
                    return _nz(((t.get("question") or {}).get("content")))

                def _get_a(t) -> str:
                    return _nz(((t.get("answer") or {}).get("content")))

                first_question = _get_q(turns[0]) if turns else ""
                question_title = first_question or "レポート"

                qa_blocks = []
                for t in turns:
                    q, a = _get_q(t), _get_a(t)
                    if q or a:
                        qa_blocks.append(f"[Q]{q}[/Q]\n[A]{a}[/A]")
                article = "\n\n".join(qa_blocks) if qa_blocks else ""

                dc = decoded_charts or []
                for idx, entry in enumerate(dc):
                    entry["id"] = str(idx)
                    if not entry.get("title"):
                        entry["title"] = f"チャート{idx+1}"

                normal_slides, chart_slides = self._parse_content_slides(article, dc)

                title_slide = {
                    "title": question_title,
                    "subtitle": user_name,
                    "template": "title",
                }

                reference_slide = None
                if source_list:
                    reference_slide = {
                        "title": "引用元",
                        "reference": source_list,  # Source は Pydantic なので .title/.link アクセス可
                        "template": "reference",
                    }
                else:
                    logger.info({
                        "message": "引用元なし。reference スライドは作成しません。",
                        "operation": "input_parse",
                    })

                slides = [
                    slide for slide in (
                        [title_slide]
                        + (chart_slides or [])
                        + normal_slides
                        + ([reference_slide] if reference_slide else [])
                    ) if slide is not None
                ]

                logger.info({
                    "message": "入力の解析が完了しました。",
                    "operation": "input_parse",
                    "status": "completed",
                })
                return slides

            except Exception as e:
                logger.error({
                    "message": "入力の解析中にエラーが発生しました。",
                    "error_message": str(e),
                    "status": "problem"
                })
                raise

    def _parse_content_slides(
        self, answer: str, decoded_charts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        LLMを使用してメインコンテンツスライドを解析する
        """
        if decoded_charts:
            chart_content = "\n".join(
                [f"{entry['id']}:{entry['title']}" for entry in decoded_charts]
            )
            template = content_parser_prompt
            kwargs = {"article": answer, "chart": chart_content}
        else:
            template = content_parser_prompt_without_chart
            kwargs = {"article": answer}
            logger.warning({
                "message": "データがないため、チャートスライドの作成をスキップします。",
                "operation": "input_parse"
            })

        try:
            slides = self.llm_invoker.invoke(template, **kwargs)
            content_slides = json.loads(slides)

            if isinstance(content_slides, dict) and "slides" in content_slides:
                slides_list = content_slides["slides"]
            elif isinstance(content_slides, list):
                slides_list = content_slides
            else:
                slides_list = [content_slides]

            chart_slides = [
                slide for slide in slides_list if slide["template"] in ["1p", "2p", "4p"]
            ]
            normal_slides = [
                slide for slide in slides_list if slide["template"] not in ["1p", "2p", "4p"]
            ]

            if decoded_charts:
                id_to_image = {entry["id"]: entry["image"] for entry in decoded_charts}

                for slide in chart_slides:
                    if "image" in slide and isinstance(slide["image"], list):
                        slide["image"] = [
                            id_to_image.get(image_id)
                            for image_id in slide["image"]
                            if image_id in id_to_image
                        ]

            return normal_slides, chart_slides
        except Exception as e:
            logger.error({
                "message": "メインコンテンツスライドの解析中にエラーが発生しました。",
                "operation": "input_parse",
                "error_message": str(e),
                "status": "problem",
            })
            raise


class PPTGenerator:
    def __init__(
        self,
        template_path: str,
        title_slide_factory: Optional[TitleSlideFactory] = None,
        chart_slide_factory: Optional[ChartSlideFactory] = None,
        reference_slide_factory: Optional[ReferenceSlideFactory] = None,
        normal_slide_factory: Optional[NormalSlideFactory] = None,
        ppt_utils: Optional[PPTUtils] = None,
    ) -> None:
        # デフォルト設定またはユーザー指定の設定を使用
        self.template_path = template_path
        self.title_slide_factory = title_slide_factory or TitleSlideFactory()
        self.chart_slide_factory = chart_slide_factory or ChartSlideFactory()
        self.reference_slide_factory = (
            reference_slide_factory or ReferenceSlideFactory()
        )
        self.normal_slide_factory = normal_slide_factory or NormalSlideFactory()
        self.ppt_utils = ppt_utils or PPTUtils()

    def generate(self, slides: List[Dict[str, Any]]) -> BinaryIO:
        """
        標準化された入力に基づいてPPTを生成し、バイトストリームを返す
        """
        logger.info({
            "message": "パワポの生成を開始します。",
            "operation": "slide_generate",
            "status": "started"
        })

        try:
            presentation = Presentation(self.template_path)
            original_slide_count = len(presentation.slides)

            # 各スライドの作成
            for slide_data in slides:
                self._create_slide(slide_data, presentation)

            # テンプレートの元のスライドを削除
            self.ppt_utils.remove_original_slides(presentation, original_slide_count)

            # バイトストリームとして保存
            ppt_io = io.BytesIO()
            presentation.save(ppt_io)
            ppt_io.seek(0)
            logger.info({
                "message": "パワポの生成が完了しました。",
                "operation": "slide_generate",
                "status": "completed"
            })
            return ppt_io
        except Exception as e:
            logger.error({
                "message": "パワポの生成中にエラーが発生しました。",
                "operation": "slide_generate",
                "error_message": str(e),
                "status": "problem"
            })
            raise

    def _create_slide(
        self, slide_data: Dict[str, Any], presentation: Presentation
    ) -> None:
        """
        標準化されたデータに基づいて単一のスライドを生成する
        """
        template = slide_data["template"]

        if template == "title":
            self.title_slide_factory.create_title_slide(
                slide_data["title"], slide_data["subtitle"], presentation
            )
        elif template in ["1p", "2p", "4p"]:
            self.chart_slide_factory.ready_for_creating_slide(
                template,
                slide_data["title"],
                slide_data["image"],
                slide_data["content"],
                presentation,
            )
        elif template == "reference":
            self.reference_slide_factory.create_reference_slide(
                slide_data["title"], slide_data["reference"], presentation
            )
        else:
            self.normal_slide_factory.ready_for_creating_slide(
                template, slide_data["title"], slide_data["content"], presentation
            )
