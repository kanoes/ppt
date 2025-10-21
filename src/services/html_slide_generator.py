import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from src.logging import get_logger
from src.services.llm import LLM

load_dotenv()

logger = get_logger("html_slide_generator")

default_deployment = os.getenv("DEFAULT_LLM_DEPLOYMENT", "gpt-5")
default_temperature = float(os.getenv("DEFAULT_LLM_TEMPERATURE", "1"))


class HTMLSlideGenerator:
    """Generate HTML slides for presentation"""

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or "workspace/slides")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = LLM(deployment_name=default_deployment, json_mode=False)

    def generate_slides(self, content_data: Dict[str, Any]) -> List[str]:
        """
        Generate HTML slides from parsed content
        
        Returns:
            List of paths to generated HTML files
        """
        logger.info({
            "message": "Starting HTML slide generation",
            "operation": "html_generate",
            "status": "started",
        })

        try:
            slide_files = []
            
            title_file = self._generate_title_slide(
                content_data["title"],
                content_data.get("subtitle", "")
            )
            slide_files.append(title_file)

            for idx, slide_content in enumerate(content_data.get("slides", [])):
                content_file = self._generate_content_slide(
                    slide_content,
                    idx + 1,
                    content_data.get("charts", [])
                )
                slide_files.append(content_file)

            if content_data.get("has_sources") and content_data.get("sources"):
                sources_file = self._generate_sources_slide(content_data["sources"])
                slide_files.append(sources_file)

            logger.info({
                "message": "HTML slide generation completed",
                "operation": "html_generate",
                "status": "completed",
                "num_files": len(slide_files),
            })

            return slide_files

        except Exception as e:
            logger.error({
                "message": "Error generating HTML slides",
                "error_message": str(e),
                "status": "failed",
            })
            raise

    def _generate_title_slide(self, title: str, subtitle: str) -> str:
        """Generate title slide HTML"""
        html = f"""<!DOCTYPE html>
<html>
<head>
  <style>
    html {{
      background: #ffffff;
    }}
    body {{
      width: 720pt;
      height: 405pt;
      margin: 0;
      padding: 0;
      font-family: Arial, sans-serif;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }}
    .title-container {{
      text-align: center;
      color: #ffffff;
      padding: 40pt;
    }}
    h1 {{
      font-size: 48pt;
      margin: 0 0 20pt 0;
      font-weight: bold;
    }}
    .subtitle {{
      font-size: 24pt;
      opacity: 0.9;
    }}
  </style>
</head>
<body>
  <div class="title-container">
    <h1>{self._escape_html(title)}</h1>
    <p class="subtitle">{self._escape_html(subtitle)}</p>
  </div>
</body>
</html>"""
        
        filepath = self.output_dir / "slide-00-title.html"
        filepath.write_text(html, encoding="utf-8")
        return str(filepath)

    def _generate_content_slide(
        self,
        slide_content: Dict[str, Any],
        slide_num: int,
        charts: List[Dict[str, Any]]
    ) -> str:
        """Generate content slide HTML using LLM"""
        question = slide_content.get("question", "")
        answer = slide_content.get("answer", "")
        
        prompt = f"""Generate a complete HTML slide (720pt × 405pt, 16:9) with the following content:

Title/Question: {question}

Content/Answer: {answer}

Requirements:
1. Use web-safe fonts only (Arial, Helvetica, etc.)
2. ALL text must be in <p>, <h1>-<h6>, <ul>, or <ol> tags
3. Use modern, clean design with good contrast
4. Body must be: width: 720pt; height: 405pt; display: flex;
5. If content is long, use two-column layout
6. Use solid colors only (no gradients, no SVG, no canvas)
7. Include complete HTML structure from <!DOCTYPE html> to </html>

Generate ONLY the HTML code, no explanations."""

        html = self.llm.invoke(prompt).content
        html = self._clean_html_output(html)
        
        filepath = self.output_dir / f"slide-{slide_num:02d}-content.html"
        filepath.write_text(html, encoding="utf-8")
        return str(filepath)

    def _generate_sources_slide(self, sources: List[Any]) -> str:
        """Generate sources/references slide"""
        def get_attr(s, attr, default=""):
            """Get attribute from Pydantic model or dict"""
            if hasattr(s, attr):
                return getattr(s, attr)
            elif isinstance(s, dict):
                return s.get(attr, default)
            return default
        
        sources_html = "\n".join([
            f'<li><a href="{self._escape_html(get_attr(s, "link"))}" target="_blank" rel="noopener">'
            f'{self._escape_html(get_attr(s, "title", "Source"))}</a></li>'
            for s in sources
        ])
        
        html = f"""<!DOCTYPE html>
<html>
<head>
  <style>
    html {{
      background: #ffffff;
    }}
    body {{
      width: 720pt;
      height: 405pt;
      margin: 0;
      padding: 40pt;
      font-family: Arial, sans-serif;
      display: flex;
      flex-direction: column;
      background: #f8f9fa;
    }}
    h1 {{
      color: #2d3748;
      font-size: 36pt;
      margin: 0 0 30pt 0;
    }}
    ul {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}
    li {{
      margin-bottom: 15pt;
      font-size: 14pt;
    }}
    a {{
      color: #667eea;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <h1>References</h1>
  <ul>
    {sources_html}
  </ul>
</body>
</html>"""
        
        filepath = self.output_dir / "slide-99-sources.html"
        filepath.write_text(html, encoding="utf-8")
        return str(filepath)

    def _clean_html_output(self, html: str) -> str:
        """Clean LLM HTML output"""
        html = html.strip()
        if html.startswith("```html"):
            html = html[7:].lstrip()
        elif html.startswith("```"):
            html = html[3:].lstrip()
        if html.endswith("```"):
            html = html[:-3].rstrip()
        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

