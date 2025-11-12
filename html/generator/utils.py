"""Utilities used by the HTML generator."""

import time
from typing import Optional

from shared.config import settings
from shared.logging import get_logger
from shared.llm.llm import LLM

logger = get_logger("html_utils")


class HTMLLLMInvoker:
    """Thin wrapper that invokes the LLM for HTML generation."""

    def __init__(
        self,
        deployment_name: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ):
        self.deployment = deployment_name or settings.default_llm_deployment
        default_temp = settings.html_llm_temperature
        self.temperature = default_temp if temperature is None else float(temperature)

        self.llm = LLM(
            deployment_name=self.deployment,
            temperature=self.temperature,
            json_mode=json_mode,
        )

    def invoke(self, prompt_text: str) -> str:
        try:
            logger.info({
                "message": "Starting LLM invocation",
                "operation": "html_llm_invoke",
                "deployment": self.deployment,
                "temperature": self.temperature,
                "status": "started",
            })
            start_time = time.time()

            answer = self.llm.invoke(prompt_text)

            end_time = time.time()
            execution_time = end_time - start_time

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
                "message": "LLM token usage",
                "operation": "llm_invoke_usage",
                "tokens": token_log,
            })

            content = getattr(answer, "content", answer)
            if not isinstance(content, str):
                raise TypeError("LLM response is not a string.")

            logger.info({
                "message": "LLM invocation completed",
                "operation": "html_llm_invoke",
                "status": "completed",
            })
            return content

        except Exception as e:
            logger.error({
                "message": "LLM invocation failed",
                "operation": "html_llm_invoke",
                "error_message": str(e),
                "status": "problem",
            })
            raise
