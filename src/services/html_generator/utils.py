# src/services/html_generator/utils.py
import os
from typing import Optional
import time

from dotenv import load_dotenv
from src.services.llm import LLM
from src.logging import get_logger

load_dotenv()
logger = get_logger("html_utils")


class HTMLLLMInvoker:
    """
    HTML用のLLM呼び出し。再フォーマットは行わない。
    """

    def __init__(
        self,
        deployment_name: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ):
        # 既定値
        default_dep = os.getenv("DEFAULT_LLM_DEPLOYMENT", "gpt-5")
        default_temp = float(os.getenv("DEFAULT_LLM_TEMPERATURE", "1"))

        self.deployment = deployment_name or default_dep
        self.temperature = default_temp if temperature is None else float(temperature)

        self.llm = LLM(
            deployment_name=self.deployment,
            temperature=self.temperature,
            json_mode=json_mode,
        )

    def invoke(self, prompt_text: str) -> str:
        try:
            logger.info({
                "message": "LLM呼び出し開始",
                "operation": "html_llm_invoke",
                "deployment": self.deployment,
                "temperature": self.temperature,
                "status": "started",
            })
            start_time = time.time()

            answer = self.llm.invoke(prompt_text)

            end_time = time.time()
            execution_time = end_time - start_time

            # usage 情報の抽出
            usage_new = getattr(answer, "usage_metadata", None) or {}
            resp_meta = getattr(answer, "response_metadata", {}) or {}
            usage_old = resp_meta.get("token_usage", {}) if isinstance(resp_meta, dict) else {}

            token_log = {
                "input_tokens": usage_new.get("input_tokens"),
                "output_tokens": usage_new.get("output_tokens"),
                "total_tokens": usage_new.get("total_tokens") or usage_old.get("total_tokens"),
                "prompt_tokens": usage_old.get("prompt_tokens"),
                "completion_tokens": usage_old.get("completion_tokens"),
                "model": resp_meta.get("model") if isinstance(resp_meta, dict) else None,
                "system_fingerprint": resp_meta.get("system_fingerprint") if isinstance(resp_meta, dict) else None,
                "deployment_name": self.deployment,
                "temperature": self.temperature,
                "execution_time": execution_time,
            }
            logger.info({
                "message": "LLMトークン使用量",
                "operation": "llm_invoke_usage",
                "tokens": token_log,
            })

            # 応答本文
            content = getattr(answer, "content", answer)
            if not isinstance(content, str):
                raise TypeError("応答が文字列ではありません。")

            logger.info({
                "message": "LLM呼び出し完了",
                "operation": "html_llm_invoke",
                "status": "completed",
            })
            return content

        except Exception as e:
            logger.error({
                "message": "LLM呼び出しエラー",
                "operation": "html_llm_invoke",
                "error_message": str(e),
                "status": "problem",
            })
            raise
