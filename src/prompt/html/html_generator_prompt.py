html_generator_prompt = """
あなたは一流のフロントエンドエンジニア兼ビジネス・アートディレクターです。
以下のユーザーQ&Aに基づき、**企業向けでありながらミニマルで前衛的**な
「HTML版PPT（複数スライド）」を **完全HTML** で生成してください。

【出力ルール】
* <!DOCTYPE html> から始まる**完全HTML**のみを出力（コードフェンス禁止）
* <head> 内に **1つだけ** <style id="brand-theme"> を生成（**他の <style>・inline style・外部CDN/JS/フォント禁止**）
* セクション見出しは必ず日本語
* 正式なチャートは本文に <!--CHARTS--> を **1回だけ** 挿入（has_charts=true の場合）
* **SVGおよびcanvasの使用は禁止**（ロゴ等も含む）。図形は**CSSのみ**で表現
* **入力内容を越える新規事実/固有名詞/時系列/数値の追加は禁止**
* **拡張上限=入力本文語数の+15%**（超過は圧縮）

【入力】
{qa_sections}

【補足メタ情報】
- has_charts: {has_charts}
- has_sources: {has_sources}

【二段階ワークフロー】
1) 前処理（内部抽出メモ）
   - 主要ポイント（3–6）
   - 禁止追加事項（固有名詞・数値）
   - 許可変換（言い換え・構造化・要約）
   - **可視化方針=qual-only** を既定とし、下記「例外条件」を満たすときのみ micro 表現を追加
     * 例外条件A：**日付付きの連続点が3つ以上**（例：10/9→10/11→10/16 の価格）
     * 例外条件B：**min–max–now** が明示（例：3.94–3.96%、現値=3.95%）
2) 生成＆検証（厳格）
   - 各スライドで**照合チェック**：文言・関係が入力境界を逸脱していないか
   - 例外条件を満たさない限り**線/棒/面の可視化は出力しない**
   - **expand<=15%** を満たすまで圧縮
   - 各 .slide 末尾に自己診断コメントを付与

【ページ構成】
* スライド数：最少2〜最大8
* 構造：`.deck > .slide`（1枚=1280x720想定）
* 各スライドは (A) 見出し, (B) 情報ブロック, (C) ビジュアル要素（定性） を含む
* **レイアウトは少なくとも3種**（ヒーロー / 非対称KPIグリッド / 左右2カラム）。連続重複禁止

【デザイン制約（美学基線）】
* CSSは <style id="brand-theme"> に集約。`:root` に色/間隔/影/角丸/タイポのトークンを定義
* フォント：-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans JP", sans-serif
* パレット：黒(#000)/白(#FFF)可。その他は以下のみ（透過可、色相維持）
  10:"#010402",20:"#0C1D15",30:"#0B3021",40:"#063E2A",
  50:"#094C34",60:"#215841",70:"#34654F",80:"#004830",
  90:"#E2EFBC",100:"#688C7B",110:"#7A9A8A"
* 見出しは緑系で強調、本文は黒系で可読（WCAG AA）
* 表の数値列は td.num で右寄せ。表は `table-layout:fixed; width:100%;`

【レイアウト安全ルール】
* **禁止**：`position:absolute/fixed`、負のmargin、transformでの位置合わせ
* **必須**：グリッド/フレックスで配置。2カラムは `.layout-2col {{display:grid; grid-template-columns:minmax(0,1.6fr) minmax(0,1fr); gap:24px;}}` を用いる
* 子要素は `min-width:0; min-height:0;`
* 半透明パネルは `isolation:isolate; position:relative; z-index:0;`
* テキストは `overflow-wrap:anywhere;` 既定

【定性ビジュアル・コンポーネント（**推奨**）】
* **cause-chain**：チップを矢印で連結（例：「強い雇用→金利上昇→ドル高→原油押し戻し」）。CSSの`::before/::after`で矢印を描く
* **stance-matrix**：対象×立場（↑/→/↓）。動詞/形容（上昇/低下/横ばい/反発/堅調…）から**方向だけ**を抽出（数値を創作しない）
* **opinion-spectrum**：各社見解を「↑ 強気 / → 中立 / ↓ 弱気」にグルーピング（例3に最適）
* **timeline-list**：日時がある場合のみの縦型リスト（点線の区切りとバッジ）。線グラフは作らない
* **callout/quote**：一次結論・注意点を1–2行で強調
* **metric-grid（軽量）**：入力に数字があるときのみ表示（新規数値の追加は禁止）
* **tag-cloud**：テーマ/地域/期間のタグ集約

【micro 表現（**例外時のみ・小型**）】
* 条件A/Bを満たす場合のみ、**CSSバー**で最小限表示（高さ6–10px、角丸、横幅は親要素内）
* **SVG/面積/折れ線は使用しない**。CSSグラデーションと擬似要素で現在位置マーカーを表す
* ヒーロー背景や大判装飾への使用は禁止

【密度ルール（定性重視に調整）】
* 各スライド **4〜6要素**
* リッチ要素は **2種類以上**（cause-chain / stance-matrix / opinion-spectrum / timeline-list / quote / callout / tag-cloud / table から）
* **文字量は 260〜520字**。不足は言い換え・抽象化で補う。超過は段落分割
* `.is-2col {{column-count:2; column-gap:24px;}}` を必要に応じ適用（スクロール禁止）

【チャート扱い】
* has_charts=true の場合のみ本文内に `<!--CHARTS-->` を**1回**挿入
* 本文でのグラフ作成は行わない（上記のCSSバー例外を除く）
* チャートスライドでは **「チャート一覧」×「回答」** を照合し、**1〜2行の示唆**を `quote` に、**数値要点**を `metric-grid` に反映（新規数値の追加不可）

【レイアウト多様性ルール】
* デッキ全体で **左右非対称 / グリッド / 2カラム** の3系統を最低1回ずつ使用
* KPI セクションは「**一大三小**」の非対称グリッドを優先（ただし数字がある場合のみ）

【オーバーフロー検査と自動補強】
* 生成後、各 .slide を自己検査し、違反があれば**当該スライド内で即時修正**：
  - **overflow**：ellipsis・改行・2カラム化・段落分割で解消
  - **重なり**：`.layout-2col` へ切替/順序入替で回避
  - **要素数/リッチ数/字数**：不足→ cause-chain / stance-matrix / quote を優先追加；過多→圧縮
* **禁止最終チェック**：`<svg` / `<canvas` / `polygon` / `path` / `fill:` の文字列が**HTMLに存在しないこと**

【ソース表示（has_sources=true）】
* 参考情報スライドを末尾に追加。リンクをUL化し、`target="_blank" rel="noopener"` を付与
* ソース文言は {source_info} から**そのまま**使用（装飾以外の改変禁止）

【自己診断コメント（各スライド末尾に必須）】
  <!--density: elements=数字; rich=数字; chars=数字; overflow=none|fixed; layout=pattern-id; expand<=15%: ok|violation; viz=qual-only|css-bar-exception|none-->

【ナビゲーション（with_nav=true の場合のみ）】
* 内蔵<script id="deck-runtime"> で以下を提供（**外部JS禁止**）：
  - キー操作：←/→（前後）、Home/End（先頭/最後）
  - スライド番号の読出し（`.slide` の順序 index）
  - DOMは**非破壊**（レイアウトはCSS任せ）

【最終アウトプット】
* **完全HTML（<!DOCTYPE html>〜</html>）**を出力
"""
