# tests/test_html_runner.py
import json
from pathlib import Path
import sys
import os
import time
from importlib.util import spec_from_file_location, module_from_spec

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.html_generator.html_generator import HTMLContentParser, HTMLGenerator
from src.services.html_saver.html_save import save_html_to_local
from src.api.routes_generate import generate_filename, generate_user_hash


def _load_prompt_from_py(prompt_path: str | None) -> str | None:
    if not prompt_path:
        return None
    p = Path(prompt_path)
    if not p.exists():
        print(f"[WARN] Prompt file not found: {p}")
        return None
    try:
        spec = spec_from_file_location("custom_prompt_mod", str(p))
        if not spec or not spec.loader:
            print(f"[WARN] Failed to create import spec for: {p}")
            return None
        mod = module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[assignment]
        prompt = getattr(mod, "html_generator_prompt", None)
        if isinstance(prompt, str) and prompt.strip():
            return prompt
        print(f"[WARN] html_generator_prompt not found in: {p}")
        return None
    except Exception as e:
        print(f"[WARN] Failed to import prompt from {p}: {e}")
        return None


def _normalize_payload(payload: dict) -> tuple[str, list[dict], str]:
    user_name = payload.get("userName") or payload.get("user_name") or "ローカル テスター"

    if isinstance(payload.get("conversation"), list) and payload["conversation"]:
        name_for_filename = payload.get("userQuestion") or user_name
        return user_name, payload["conversation"], name_for_filename

    uq = payload.get("userQuestion") or "レポート"
    ans = payload.get("answer") or ""
    conversation = [{
        "index": 0,
        "question": {"content": uq},
        "answer": {"content": ans},
    }]
    name_for_filename = uq or user_name
    return user_name, conversation, name_for_filename


def _merge_assets_into_conversation(payload: dict, conversation: list[dict]) -> None:
    if not conversation:
        return
    assets = payload.get("assets") or {}
    src_list = assets.get("sourceList") or []
    charts = assets.get("indicatorCharts") or []

    first = conversation[0]

    if src_list:
        normalized_sources = [
            {"title": (s.get("title") or ""), "link": (s.get("link") or "")}
            for s in src_list
            if isinstance(s, dict) and (s.get("title") or s.get("link"))
        ]
        if normalized_sources:
            if "sources" in first and isinstance(first["sources"], list):
                first["sources"].extend(normalized_sources)
            else:
                first["sources"] = normalized_sources

    if charts:
        normalized_charts = [
            {"title": c.get("title"), "encodedImage": c.get("encodedImage")}
            for c in charts
            if isinstance(c, dict) and c.get("encodedImage")
        ]
        if normalized_charts:
            if "charts" in first and isinstance(first["charts"], list):
                first["charts"].extend(normalized_charts)
            else:
                first["charts"] = normalized_charts


def run_once(
    json_path: str,
    outname: str | None = None,
    user_hash: str | None = None,
    prompt_path: str | None = None,
):
    payload = json.loads(Path(json_path).read_text(encoding="utf-8"))

    user_name, conversation, name_for_filename = _normalize_payload(payload)
    _merge_assets_into_conversation(payload, conversation)

    parser = HTMLContentParser()
    content_data = parser.parse(
        user_name=user_name,
        conversation=conversation,
    )

    prompt_to_use = _load_prompt_from_py(prompt_path)
    generator = HTMLGenerator(prompt=prompt_to_use)
    html = generator.generate(content_data)

    user_hash_val = user_hash or generate_user_hash(user_name)
    filename = outname or generate_filename(name_for_filename, "test_thread_id","html")
    save_html_to_local(html, filename, user_hash_val)

    out_path = Path(f"generated_files/{user_hash_val}/{filename}").resolve()
    print(f"[OK] HTML saved to: {out_path}")


if __name__ == "__main__":
    OUTPUT_NAME = None
    USER_HASH_OVERRIDE = None

    JSON_FILE = "tests/tests_case/test_1.json"
    PROMPT_PATH = "src/prompt/html/html_generator_prompt.py"

    start_time = time.time()
    run_once(
        json_path=JSON_FILE,
        outname=OUTPUT_NAME,
        user_hash=USER_HASH_OVERRIDE,
        prompt_path=PROMPT_PATH,
    )
    print(f"Takes time for HTML generation: {time.time() - start_time:.2f} seconds")
