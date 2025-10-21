# ベースイメージを指定
FROM python:3.11-slim

# 環境変数を設定
ENV PYTHONPYCACHEPREFIX=/usr/src/pycache \
    PYTHONPATH=/app \
    TZ=Asia/Tokyo \
    POETRY_VIRTUALENVS_CREATE=false

# 作業ディレクトリを設定
WORKDIR /app

# システム依存関係をインストール
RUN apt update && \
    apt install -y libxmlsec1-dev libxmlsec1-openssl tzdata curl && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# # 依存関係をインストール
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY src ./src
COPY resources ./resources

# プロジェクトコードをコンテナ内にコピー
COPY app.py ./

# アプリケーションのポートを公開
EXPOSE 5056

# コンテナ起動時のコマンドを指定
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--bind=0.0.0.0:5056", "--timeout", "0"]