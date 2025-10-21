from dotenv import load_dotenv
from fastapi import FastAPI

# 環境変数を読み込む
load_dotenv()

app = FastAPI()


def include_routers():
    from src.api import routes_generate

    app.include_router(routes_generate.router)


include_routers()
