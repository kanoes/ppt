# ローカル起動

## 環境の準備

1. 以下の内容を記載した `.env` ファイルをルートディレクトリに作成します。

   ```
   AZURE_OPENAI_API_KEY=xxxxx
   AZURE_OPENAI_ENDPOINT=https://xxxxx.openai.azure.com/
   ```

2. poetry をインストールします。

   ```
   pip install poetry
   poetry install --no-root
   pip install -e ./shared -e ./html/src -e ./ppt/src
   ```

3. poetry を起動します。

   ```
   poetry shell
   ```


## 起動(FastAPI)

1. FastAPI サーバーを起動します。
   ```
   poetry run uvicorn app:app --reload  
   ```

2. 以下の URL にアクセスし、PPT 生成のエンドポイントにアクセスします。
   http://127.0.0.1:8000/docs

## 起動(Docker)

1. Dockerfile をビルドします。
   ```
   docker build -t ppt-generator:latest .
   ```

2. Docker コンテナを起動します。
   ```
   docker run -p 5056:5056 ppt-generator:latest
   ```

3. 以下の URL にアクセスし、PPT 生成のエンドポイントにアクセスします。
   http://127.0.0.1:5056/docs


# Azureデプロイに関する注意事項

Azure Pipelinesで手動でGit Tagを選択する必要があります。手順は以下の通りです。

手順 1：Azure Pipelines にアクセス
Azure DevOps にログインします。
対象の プロジェクト を選択します。
左側のメニューから Pipelines > Pipelines をクリックし、パイプライン一覧のページに移動します。

手順 2：対象のパイプラインを見つける
パイプライン一覧から、使用したいパイプライン（YAML またはクラシックエディターどちらでも可）を探します。
該当するパイプラインの右側にある 「Run pipeline（パイプラインの実行）」ボタン をクリックします。

手順 3：Git Tag を選択する
Run Pipeline（パイプラインの実行）画面 がポップアップ表示されます。
「Branch/tag」の部分を探します。
デフォルトでは Branch（例：main ブランチ） が選択されています。
Branch のドロップダウンをクリックし、Tag オプションに切り替えます。
リポジトリ内のすべての Git Tag が一覧表示されます。ここから、必要な Tag（例：stg-v1.0.0）を選択します。

選択が完了したら、Run（実行）ボタン をクリックして、選択した Tag に基づいてパイプラインを開始します。

# Logに関して

APP全体の開始Statusは「received」、成功の場合には「success」。
各処理ステップの開始Statusは「started」、成功の場合には「completed」。