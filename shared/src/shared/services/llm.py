import os
from typing import Any, Literal
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()

def LLM(
    deployment_name: Literal[
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o-new",
        "gpt-5",
    ] = "gpt-5",
    json_mode: bool = True,
    **kwargs: Any,
) -> AzureChatOpenAI:

    if deployment_name in ("gpt-4o", "gpt-4o-new"):
        model_name = "gpt-4o"
    elif deployment_name == "gpt-4o-mini":
        model_name = "gpt-4o-mini"
    elif deployment_name == "gpt-5":
        model_name = "gpt-5"
    else:
        raise ValueError(f"Unknown model name: {deployment_name}")

    model_kwargs = kwargs.pop("model_kwargs", {})

    llm = AzureChatOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
        openai_api_version="2024-10-21",
        deployment_name=deployment_name,
        model_name=model_name,
        max_retries=1,
        request_timeout=600,
        **model_kwargs,
        **kwargs,
    )

    return llm.bind(response_format={"type": "json_object"}) if json_mode else llm
