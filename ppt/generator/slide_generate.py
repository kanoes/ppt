import json
import random
import os

from dotenv import load_dotenv

from ppt.generator.utils import LLMInvoker, OtherUtils, PPTUtils
from ppt.prompt.normal_template_prompt import (
    template1,
    template1B,
    template2,
    template3,
    template4,
    template5,
    template6,
    template7,
)
from shared.logging import get_logger

load_dotenv()

logger = get_logger("slide_generate")

llm_invoker = LLMInvoker()

# 　テンプレート情報の読み込み
with open("resources/title_template_info.json", "r") as file:
    title_template_info = json.load(file)

with open("resources/chart_template_info.json", "r") as file:
    chart_template_info = json.load(file)

with open("resources/reference_template_info.json", "r") as file:
    reference_template_info = json.load(file)

with open("resources/normal_template_info.json", "r") as file:
    normal_template_info = json.load(file)

class TitleSlideFactory:
    """
    タイトルスライドを作成するためのファクトリクラス。
    """

    @staticmethod
    def create_title_slide(title: str, subtitle: str, presentation) -> None:
        """
        タイトルスライドを作成する関数。
        テンプレートID「0」のスライドを複製し、タイトルとサブタイトルを設定する。

        変種テンプレート：なし。
        複数スライド生成対応：なし。
        空白内容の削除：なし。
        """
        try:
            # コンテンツを解析
            title = title  # 変動なし
            subtitle = subtitle  # 変動なし

            # 目標テンプレートの情報を取得
            template_info_standard = "1"  # 標準テンプレートID
            template_info_item = next(
                (
                    item["main"]
                    for item in title_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )

            # 目標シェイプや目標プレースホルダーの番号を取得
            title_placeholder_number = template_info_item["placeholder_number"]["title"]
            subtitle_placeholder_number = template_info_item["placeholder_number"][
                "subtitle"
            ]

            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # コンテンツを埋め込む
            slide.placeholders[title_placeholder_number].text = title  # タイトル
            slide.placeholders[subtitle_placeholder_number].text = subtitle  # サブタイトル
            
        except Exception as e:
            logger.error({
                "message": "タイトルスライドの作成中にエラーが発生しました。",
                "operation": "create_title_slide",
                "error_message": str(e),
                "status": "problem",
            })
            raise


class ChartSlideFactory:
    """
    グラフスライドを作成するためのファクトリクラス。
    """

    @staticmethod
    def ready_for_creating_slide(
        template: str,
        title: str,
        image: list,
        content: str,
        presentation,
    ) -> None:
        """
        グラフスライドを作成するための準備をする関数。
        各ページの図表数に基づいて適切なスライド生成メソッドを呼び出す。
        """
        if template == "1p":
            method_name = "create_chart_slide_1p"
        elif template == "2p":
            method_name = "create_chart_slide_2p"
        elif template == "4p":
            method_name = "create_chart_slide_4p"
        else:
            raise ValueError(f"Template ID {template} は未対応です。")

        getattr(ChartSlideFactory, method_name)(
            template, title, image, content, presentation
        )

    @staticmethod
    def create_chart_slide_1p(
        template: str,
        title: str,
        image: list,
        content: str,
        presentation,
    ) -> None:
        """
        1pチャートスライドを作成する。
        """
        try:
            # コンテンツを解析
            title = title
            chart_file = image[0]
            chart_title = PPTUtils.extract_all_between_tags("TITLE", content)[0]
            chart_explanation = PPTUtils.extract_all_between_tags("EXPLANATION", content)[0]

            # 目標テンプレートの情報を取得
            template_info_standard = template  # 標準テンプレートID
            template_info_item = next(
                (
                    item["main"]
                    for item in chart_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )

            # 目標シェイプや目標プレースホルダーの番号を取得
            title_placeholder_number = template_info_item["placeholder_number"]["title"]
            chart_placeholder_number = template_info_item["placeholder_number"]["chart"]
            chart_title_shape_number = template_info_item["shape_number"]["chart_title"]
            explanation_shape_number = template_info_item["shape_number"]["explanation"]

            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # コンテンツを埋め込む
            PPTUtils.add_text_to_shape(
                slide.placeholders[title_placeholder_number], title
            )  # タイトル
            PPTUtils.add_text_to_shape(
                slide.shapes[chart_title_shape_number], chart_title
            )  # チャートタイトル
            PPTUtils.add_text_to_shape(
                slide.shapes[explanation_shape_number], chart_explanation
            )  # チャート説明
            PPTUtils.add_picture_to_slide(
                slide.placeholders[chart_placeholder_number], chart_file
            )  # チャート

        except Exception as e:
            logger.error({
                "message": "1pチャートスライドの作成中にエラーが発生しました。",
                "operation": "create_chart_slide_1p",
                "error_message": str(e),
                "status": "problem",
            })
            raise

    @staticmethod
    def create_chart_slide_2p(
        template: str,
        title: str,
        image: list,
        content: str,
        presentation,
    ) -> None:
        """
        2pチャートスライドを作成する。
        """
        try:
            # コンテンツを解析
            title = title
            chart_file = image
            chart_title = PPTUtils.extract_all_between_tags("TITLE", content)
            chart_explanation = PPTUtils.extract_all_between_tags("EXPLANATION", content)[0]

            # 目標テンプレートの情報を取得
            template_info_standard = template  # 標準テンプレートID
            template_info_item = next(
                (
                    item["main"]
                    for item in chart_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )

            # 目標シェイプや目標プレースホルダーの番号を取得
            title_placeholder_number = template_info_item["placeholder_number"]["title"]
            chart_placeholder_number = template_info_item["placeholder_number"]["chart"]
            chart_title_shape_number = template_info_item["shape_number"]["chart_title"]
            explanation_shape_number = template_info_item["shape_number"]["explanation"]

            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # コンテンツを埋め込む

            PPTUtils.add_text_to_shape(
                slide.placeholders[title_placeholder_number], title
            )  # タイトル

            PPTUtils.add_text_to_shape(
                slide.shapes[explanation_shape_number], chart_explanation
            )  # チャート説明

            length = len(chart_file)

            for i in range(length):
                current_chart_file = chart_file[i]
                PPTUtils.add_picture_to_slide(
                    slide.placeholders[chart_placeholder_number[i]], current_chart_file
                )  # チャート
                PPTUtils.add_text_to_shape(
                    slide.shapes[chart_title_shape_number[i]], chart_title[i]
                )  # チャートタイトル

        except Exception as e:
            logger.error({
                "message": "2pチャートスライドの作成中にエラーが発生しました。",
                "operation": "create_chart_slide_2p",
                "error_message": str(e),
                "status": "problem",
            })
            raise

    @staticmethod
    def create_chart_slide_4p(
        template: str,
        title: str,
        image: list,
        content: str,
        presentation,
    ) -> None:
        """
        4pチャートスライドを作成する。
        """
        try:
            # コンテンツを解析
            title = title
            chart_file = image
            chart_title = PPTUtils.extract_all_between_tags("TITLE", content)

            # 目標テンプレートの情報を取得
            template_info_standard = template  # 标准模板ID
            template_info_item = next(
                (
                    item["main"]
                    for item in chart_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )

            # 目標シェイプや目標プレースホルダーの番号を取得
            title_placeholder_number = template_info_item["placeholder_number"]["title"]
            chart_placeholder_number = template_info_item["placeholder_number"]["chart"]
            chart_title_shape_number = template_info_item["shape_number"]["chart_title"]

            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # コンテンツを埋め込む

            PPTUtils.add_text_to_shape(
                slide.placeholders[title_placeholder_number], title
            )  # タイトル

            length = len(chart_file)

            for i in range(length):
                current_chart_file = chart_file[i]
                PPTUtils.add_picture_to_slide(
                    slide.placeholders[chart_placeholder_number[i]], current_chart_file
                )  # チャート
                PPTUtils.add_text_to_shape(
                    slide.shapes[chart_title_shape_number[i]], chart_title[i]
                )  # チャートタイトル

        except Exception as e:
            logger.error({
                "message": "4pチャートスライドの作成中にエラーが発生しました。",
                "operation": "create_chart_slide_4p",
                "error_message": str(e),
                "status": "problem",
            })
            raise

class ReferenceSlideFactory:
    """
    参照スライドを作成するためのファクトリクラス。
    """

    @staticmethod
    def create_reference_slide(title: str, references: list, presentation):
        """
        引用元スライドを作成する関数。

        変種テンプレート：なし。
        複数スライド生成対応：あり。
        空白内容の削除：あり。
        """
        try:

            # 目標テンプレートの情報を取得
            template_info_standard = "1"  # 標準テンプレートID
            template_info_item = next(
                (
                    item["main"]
                    for item in reference_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )

            # 目標シェイプや目標プレースホルダーの番号を取得
            title_placeholder_number = template_info_item["placeholder_number"]["title"]
            table_shape_number = template_info_item["shape_number"]["table"]

            # 1ページあたりの最大引用数
            REFS_PER_PAGE = 11

            # 必要なページ数を計算
            total_pages = (len(references) - 1) // REFS_PER_PAGE + 1

            for page in range(total_pages):
                # 目標テンプレートスライドを複製
                slide_number = template_info_item["slide_number"]
                slide = PPTUtils.duplicate_slide(slide_number, presentation)

                # コンテンツを埋め込む
                PPTUtils.add_text_to_shape(
                    slide.placeholders[title_placeholder_number], title
                )  # タイトル

                cell = slide.shapes[table_shape_number].table.cell(0, 1)
                PPTUtils.add_text_to_shape(cell, title)  # テーブルヘッダー

                # 現在のページに表示する引用範囲を計算
                start_idx = page * REFS_PER_PAGE
                end_idx = min((page + 1) * REFS_PER_PAGE, len(references))

                # 現在のページの実際の引用数を計算
                current_page_refs = references[start_idx:end_idx]
                actual_refs = len(current_page_refs)

                # 現在のページに引用を追加
                for row_idx, reference in enumerate(current_page_refs):
                    title = reference.title
                    link = reference.link
                    cell = slide.shapes[table_shape_number].table.cell(row_idx + 1, 1)
                    PPTUtils.add_text_to_shape(cell, title, hyperlink=link)  # 引用内容

                # 余分な行を削除
                table = slide.shapes[table_shape_number].table
                for row_index in range(REFS_PER_PAGE, actual_refs, -1):
                    table._tbl.remove(table._tbl.tr_lst[row_index])

        except Exception as e:
            logger.error({
                "message": "引用元スライドの作成中にエラーが発生しました。",
                "operation": "create_reference_slide",
                "error_message": str(e),
                "status": "problem",
            })
            raise


class NormalSlideFactory:
    """
    PowerPointスライドをテンプレートに基づいて作成するためのファクトリクラス。
    """

    @staticmethod
    def ready_for_creating_slide(
        template_id: str, title: str, content: str, presentation
    ):
        """
        指定されたテンプレートIDに基づいてスライドを作成するための準備をする。

        Parameters:
            template_id: str
                作成するテンプレートのID（例: "1", "2"）。
            content: str
                スライドに入力するコンテンツ。
            presentation: Presentation
                操作対象のPPTXプレゼンテーションオブジェクト。
        """
        method_name = f"create_template{template_id}_slide"
        if not hasattr(NormalSlideFactory, method_name):
            raise ValueError(f"Template ID {template_id} は未対応です。")

        try:
            getattr(NormalSlideFactory, method_name)(title, content, presentation)
            
        except Exception as e:
            logger.error({
                "message": "テンプレート{template_id}スライドの作成中にエラーが発生しました。",
                "operation": f"create_template{template_id}_slide",
                "error_message": str(e),
                "status": "problem",
            })
            raise


    @staticmethod
    def create_template1_slide(title: str, content: str, presentation):
        """
        テンプレート1スライドを作成する。

        変種テンプレート：なし。
        複数スライド生成対応：なし。
        空白内容の削除：なし。
        """

        def create_slide(subtitle, body, slide_index=None):
            # 目標テンプレートの情報を取得
            template_info_standard = "1"  # 標準テンプレートID
            template_info_group = ["mainA", "mainB"]
            variant_key = OtherUtils.random_choice(template_info_group)
            template_info_item = next(
                (
                    item[variant_key]
                    for item in normal_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )

            # 目標シェイプや目標プレースホルダーの番号を取得
            title_placeholder_number = template_info_item["placeholder_number"]["title"]
            subtitle_shape_number = template_info_item["shape_number"]["subtitle"]
            body_shape_number = template_info_item["shape_number"]["body"]

            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # タイトルにスライドインデックスを追加
            final_title = title
            if slide_index is not None:
                final_title = f"{title} {chr(9311 + slide_index +1)}"  # 追加番号 ①, ②...

            # コンテンツを埋め込む
            slide.placeholders[title_placeholder_number].text = final_title  # タイトル
            PPTUtils.add_text_to_shape(
                slide.shapes[subtitle_shape_number], subtitle
            )  # サブタイトル
            PPTUtils.add_text_to_shape(slide.shapes[body_shape_number], body)  # 本文

        # 字数チェック
        if len(content) > 350:
            content = llm_invoker.invoke(template1B, content=content)
            subtitles = PPTUtils.extract_all_between_tags("SUBTITLE", content)
            bodies = PPTUtils.extract_all_between_tags("BODY", content)

            for index, (subtitle, body) in enumerate(zip(subtitles, bodies)):
                create_slide(subtitle, body, slide_index=index)
        else:
            content = llm_invoker.invoke(template1, content=content)
            subtitle = PPTUtils.extract_all_between_tags("SUBTITLE", content)[0]
            body = PPTUtils.extract_all_between_tags("BODY", content)[0]
            create_slide(subtitle, body)


    @staticmethod
    def create_template2_slide(title: str, content: str, presentation):
        """
        テンプレート2スライドを作成する。

        変種テンプレート：あり。
        複数スライド生成対応：なし。
        空白内容の削除：なし。
        """

        # コンテンツを解析
        title = title
        content = llm_invoker.invoke(template2, content=content)
        step_mark = PPTUtils.extract_all_between_tags("STEP_MARK", content)
        step_content = PPTUtils.extract_all_between_tags("STEP_CONTENT", content)

        # 目標テンプレートの情報を取得
        template_info_standard = "2"  # 標準テンプレートID
        template_info_variant = {4: "main", 3: "sub1", 5: "spc"}  # 準テンプレートの変種
        variant_key = template_info_variant.get(
            len(step_mark)
        )  # 項目数に応じた目標テンプレート決定

        if variant_key:
            template_info_item = next(
                (
                    item[variant_key]
                    for item in normal_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )
        else:
            raise ValueError(f"step_markの長さが不正です: {len(step_mark)}")

        # 目標シェイプや目標プレースホルダーの番号を取得
        title_placeholder_number = template_info_item["placeholder_number"]["title"]
        step_mark_shape_number = template_info_item["shape_number"]["step_mark"]
        step_content_shape_number = template_info_item["shape_number"]["step_content"]

        # 目標テンプレートスライドを複製
        slide_number = template_info_item["slide_number"]
        slide = PPTUtils.duplicate_slide(slide_number, presentation)

        # コンテンツを埋め込む
        slide.placeholders[title_placeholder_number].text = title  # タイトル

        for i, mark in enumerate(step_mark):
            PPTUtils.add_text_to_shape(
                slide.shapes[step_mark_shape_number[i]], mark
            )  # ステップマーク

        for i, content in enumerate(step_content):
            PPTUtils.add_text_to_shape(
                slide.shapes[step_content_shape_number[i]], content
            )  # ステップ内容


    @staticmethod
    def create_template3_slide(title: str, content: str, presentation):
        """
        テンプレート3スライドを作成する。

        変種テンプレート：あり。
        複数スライド生成対応：あり。
        空白内容の削除：なし。
        """

        # コンテンツを解析
        title = title
        content = llm_invoker.invoke(template3, content=content)
        agenda_summary = PPTUtils.extract_all_between_tags("AGENDA_SUMMARY", content)
        agenda_content = PPTUtils.extract_all_between_tags("AGENDA_CONTENT", content)

        # １ページあたりの項目数の最大値
        max_agenda_summary_num = 8
        content_size = len(agenda_summary)
        page_num = (content_size - 1) // max_agenda_summary_num + 1

        # 目標テンプレートの情報を取得
        template_info_standard = "3"  # 標準テンプレートID
        template_info_group = {
            1: "sub7",
            2: "sub1",
            3: "sub2",
            4: "sub3",
            5: "sub4",
            6: "sub5",
            7: "sub6",
        }  # 標準テンプレートの変種
        template_info_group_sub = {
            1: "subsub7",
            2: "subsub6",
            3: "subsub5",
            4: "subsub4",
            5: "subsub3",
            6: "subsub2",
            7: "subsub1",
        }  # 

        for current_page_num in range(page_num):
            # 残りの内容数を計算
            remaining_content = content_size - (current_page_num + 1) * max_agenda_summary_num

            # 残りの項目数に基づいてテンプレートを選択
            if remaining_content < 0 and page_num == 1:
                current_size = max_agenda_summary_num + remaining_content
                variant_key = template_info_group.get(current_size)
            elif remaining_content < 0 and page_num != 1:
                current_size = max_agenda_summary_num + remaining_content
                variant_key = template_info_group_sub.get(current_size)
            else:
                current_size = max_agenda_summary_num
                variant_key = "main"

            if not variant_key:
                raise ValueError(f"agenda_summaryの長さが不正です: {content_size}")

            # 現在のページの目標テンプレート情報を取得
            template_info_item = next(
                (
                    item[variant_key]
                    for item in normal_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )
            if not template_info_item:
                raise ValueError(f"テンプレート情報が見つかりません: {variant_key}")

            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # タイトルを設定
            slide.placeholders[template_info_item["placeholder_number"]["title"]].text = title

            # コンテンツを埋め込む
            agenda_summary_shape_numbers = template_info_item["shape_number"]["agenda_summary"]
            agenda_content_shape_numbers = template_info_item["shape_number"]["agenda_content"]

            for current_size_idx in range(current_size):
                size_idx = current_page_num * max_agenda_summary_num + current_size_idx

                # agenda_summary の内容を設定
                PPTUtils.add_text_to_shape(
                    slide.shapes[agenda_summary_shape_numbers[current_size_idx]],
                    agenda_summary[size_idx],
                )

                # agenda_content の内容を設定
                PPTUtils.add_text_to_shape(
                    slide.shapes[agenda_content_shape_numbers[current_size_idx]],
                    agenda_content[size_idx],
                )


    @staticmethod
    def create_template4_slide(title: str, content: str, presentation):
        """
        テンプレート4スライドを作成する。

        変種テンプレート：なし。
        複数スライド生成対応：あり。
        空白内容の削除：あり。
        """

        # コンテンツを解析
        title = title
        content = llm_invoker.invoke(template4, content=content)
        list_name = title
        list_content = PPTUtils.extract_all_between_tags("LIST_CONTENT", content)

        # 目標テンプレートの情報を取得
        template_info_standard = "4"  # 標準テンプレートID
        template_info_item = next(
            (
                item["main"]
                for item in normal_template_info
                if item["template_id"] == template_info_standard
            ),
            None,
        )

        # 目標シェイプや目標プレースホルダーの番号を取得
        title_placeholder_number = template_info_item["placeholder_number"]["title"]
        list_shape_number = template_info_item["shape_number"]["list"]

        # 必要なページ数を計算
        page_num = (len(list_content) - 1) // 11 + 1

        # １ページあたりのリスト内容の最大数を設定
        max_list_content_num = 11

        # 各ページを作成
        for current_page_num in range(page_num):
            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # コンテンツを埋め込む
            PPTUtils.add_text_to_shape(
                slide.placeholders[title_placeholder_number], title
            )  # タイトル

            table_shape = slide.shapes[list_shape_number]
            cell = table_shape.table.cell(0, 1)
            PPTUtils.add_text_to_shape(cell, list_name)  # リスト名

            # 現在のページの実際のコンテンツ数を計算
            start_index = current_page_num * max_list_content_num
            remaining_items = len(list_content) - start_index
            actual_items = min(max_list_content_num, remaining_items)

            # コンテンツを埋め込む
            for row_index in range(actual_items):
                current_content_num = start_index + row_index
                cell = table_shape.table.cell(row_index + 1, 1)
                PPTUtils.add_text_to_shape(
                    cell, list_content[current_content_num]
                )  # リスト内容

            # 余分な行を削除
            table = table_shape.table
            for row_index in range(max_list_content_num, actual_items, -1):
                table._tbl.remove(table._tbl.tr_lst[row_index])


    @staticmethod
    def create_template5_slide(title: str, content: str, presentation):
        """
        テンプレート5スライドを作成する。

        変種テンプレート：あり。
        複数スライド生成対応：あり。
        空白内容の削除：なし。
        """

        # コンテンツを解析
        title = title
        content = llm_invoker.invoke(template5, content=content)
        agenda_summary = PPTUtils.extract_all_between_tags("AGENDA_SUMMARY", content)
        agenda_content = PPTUtils.extract_all_between_tags("AGENDA_CONTENT", content)

        # １ページあたりの項目数の最大値
        max_agenda_summary_num = 5
        content_size = len(agenda_summary)
        page_num = (content_size - 1) // max_agenda_summary_num + 1

        # 目標テンプレートの情報を取得
        template_info_standard = "5"  # 標準テンプレートID
        template_info_group = {
            4: ["subA1", "mainB"],
            3: ["subA2", "subB1"],
            2: ["subA3", "subB2"],
            1: ["subA4"],
        }  # 標準テンプレートの変種
        template_info_group_sub = {
            4: "subC1",
            3: "subC2",
            2: "subC3",
            1: "subA4",
        }  # 

        for current_page_num in range(page_num):
            # 残りの内容数を計算
            remaining_content = (
                content_size - (current_page_num + 1) * max_agenda_summary_num
            )

            # 残りの項目数に基づいてテンプレートを選択
            if remaining_content < 0 and page_num == 1:
                current_size = max_agenda_summary_num + remaining_content
                possible_variants = template_info_group.get(current_size)
                if possible_variants:
                    variant_key = OtherUtils.random_choice(possible_variants)
                else:
                    raise ValueError(f"agenda_summaryの長さが不正です: {content_size}")
            elif remaining_content < 0 and page_num != 1:
                current_size = max_agenda_summary_num + remaining_content
                variant_key = template_info_group_sub.get(current_size)
            else:
                current_size = max_agenda_summary_num
                variant_key = "mainA"

            # 現在のページの目標テンプレート情報を取得
            template_info_item = next(
                (
                    item[variant_key]
                    for item in normal_template_info
                    if item["template_id"] == template_info_standard
                ),
                None,
            )
            if not template_info_item:
                raise ValueError(f"テンプレート情報が見つかりません: {variant_key}")

            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # タイトルを設定
            slide.placeholders[
                template_info_item["placeholder_number"]["title"]
            ].text = title

            # コンテンツを埋め込む
            agenda_summary_shape_numbers = template_info_item["shape_number"][
                "agenda_summary"
            ]
            agenda_content_shape_numbers = template_info_item["shape_number"][
                "agenda_content"
            ]

            for current_size_idx in range(current_size):
                size_idx = current_page_num * max_agenda_summary_num + current_size_idx

                # agenda_summary の内容を設定
                PPTUtils.add_text_to_shape(
                    slide.shapes[agenda_summary_shape_numbers[current_size_idx]],
                    agenda_summary[size_idx],
                )

                # agenda_content の内容を設定
                PPTUtils.add_text_to_shape(
                    slide.shapes[agenda_content_shape_numbers[current_size_idx]],
                    agenda_content[size_idx],
                )


    @staticmethod
    def create_template6_slide(title: str, content: str, presentation):
        """
        テンプレート6スライドを作成する。

        変種テンプレート：なし。
        複数スライド生成対応：なし。
        空白内容の削除：あり。
        """

        # コンテンツを解析
        title = title
        content = llm_invoker.invoke(template6, content=content)

        # 目標テンプレートの情報を取得
        template_info_standard = "6"  # 標準テンプレートID
        template_info_item = next(
            (
                item["main"]
                for item in normal_template_info
                if item["template_id"] == template_info_standard
            ),
            None,
        )

        # 目標シェイプや目標プレースホルダーの番号を取得
        title_placeholder_number = template_info_item["placeholder_number"]["title"]
        content_shape_number = template_info_item["shape_number"]["content_shape"]
        shape_group = template_info_item["shape_number"]["shape_group"]
        area_group = template_info_item["shape_number"][
            "area_group"
        ]  # 地域グループの定義

        # 各地域のコンテンツを抽出
        areas_contents = {
            area: PPTUtils.extract_all_between_tags(area, content)
            for group in area_group
            for area in group
        }

        # 各地域のコンテンツをフォーマット
        formatted_content_groups = []
        for group in area_group:
            group_content = "\n\n".join(
                [f"[{area}] {item}" for area in group for item in areas_contents[area]]
            )
            formatted_content_groups.append(group_content)

        # 目標テンプレートスライドを複製
        slide_number = template_info_item["slide_number"]
        slide = PPTUtils.duplicate_slide(slide_number, presentation)

        # コンテンツを埋め込む
        PPTUtils.add_text_to_shape(
            slide.placeholders[title_placeholder_number], title
        )  # タイトル

        shapes_to_delete = []
        for i, content in enumerate(formatted_content_groups):
            if content:
                PPTUtils.add_text_to_shape(
                    slide.shapes[content_shape_number[i]], content
                )  # 各地域の情報
            else:
                shapes_to_delete.extend(shape_group[i])

        # 余分な形状を削除
        for shape_index in sorted(shapes_to_delete, reverse=True):
            sp = slide.shapes[shape_index]
            sp.element.getparent().remove(sp.element)


    @staticmethod
    def create_template7_slide(title: str, content: str, presentation):
        """
        テンプレート7スライドを作成する。

        変種テンプレート：なし。
        複数スライド生成対応：あり。
        空白内容の削除：あり。

        テーブルの列数:5列限定。
        """

        # コンテンツを解析
        title = title
        content = llm_invoker.invoke(template7, content=content)
        raw_table_rows = [
            row.strip().split("|") for row in content.strip().split("\n")
        ]  # テーブルの生データ
        cleaned_table_rows = [
            [cell.strip() for cell in row if cell.strip()] for row in raw_table_rows
        ]  # テーブルのクリーニング
        headers = cleaned_table_rows[0]  # ヘッダー行
        data_rows = cleaned_table_rows[2:]  # データ行

        # 目標テンプレートの情報を取得
        template_info_standard = "7"  # 標準テンプレートID
        template_info_item = next(
            (
                item["main"]
                for item in normal_template_info
                if item["template_id"] == template_info_standard
            ),
            None,
        )

        # 目標シェイプや目標プレースホルダーの番号を取得
        title_placeholder_number = template_info_item["placeholder_number"]["title"]
        table_shape_number = template_info_item["shape_number"]["table"]

        # １ページあたりの最大行数を設定
        max_rows_per_page = 10
        max_columns_per_row = 5

        # 各ページを作成
        for i in range(0, len(data_rows), max_rows_per_page):
            # 目標テンプレートスライドを複製
            slide_number = template_info_item["slide_number"]
            slide = PPTUtils.duplicate_slide(slide_number, presentation)

            # コンテンツを埋め込む
            PPTUtils.add_text_to_shape(
                slide.placeholders[title_placeholder_number], title
            )  # タイトル

            # 現在のページの実際のデータ行数を計算
            current_page_rows = data_rows[i : i + max_rows_per_page]
            row_count = len(current_page_rows)

            # テーブルのヘッダーを設定
            for j, header in enumerate(headers[:max_columns_per_row]):
                cell = slide.shapes[table_shape_number].table.cell(0, j)
                PPTUtils.add_text_to_shape(cell, header)

            # データをテーブルに埋め込む
            for row_idx, row in enumerate(current_page_rows):
                for col_idx, cell_content in enumerate(row[:max_columns_per_row]):
                    cell = slide.shapes[table_shape_number].table.cell(
                        row_idx + 1, col_idx
                    )
                    PPTUtils.add_text_to_shape(cell, cell_content)  # テーブルデータ

            # 余分な行を削除
            table = slide.shapes[table_shape_number].table
            for row_index in range(max_rows_per_page, row_count, -1):
                table._tbl.remove(table._tbl.tr_lst[row_index])

            # 余分な列を削除
            actual_columns = min(
                max(len(headers), max(len(row) for row in data_rows)),
                max_columns_per_row,
            )
            if actual_columns < max_columns_per_row:
                # tblGrid（列定義）から余分な列を削除
                grid = table._tbl.tblGrid
                for col_index in range(max_columns_per_row - 1, actual_columns - 1, -1):
                    grid.remove(grid.gridCol_lst[col_index])

                # 各行から対応する列のセルを削除
                for row in table._tbl.tr_lst:
                    for col_index in range(
                        max_columns_per_row - 1, actual_columns - 1, -1
                    ):
                        row.remove(row.tc_lst[col_index])
