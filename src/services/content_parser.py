from typing import List, Dict, Any, Optional
from src.logging import get_logger

logger = get_logger("content_parser")


class ContentParser:
    """Parse user conversation into structured presentation content"""

    def parse(
        self,
        user_name: str,
        conversation: List[Dict[str, Any]],
        decoded_charts: Optional[List[Dict[str, Any]]] = None,
        source_list: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Parse conversation data into structured content for presentation generation
        
        Returns:
            Dict containing:
            - title: Presentation title
            - subtitle: User name
            - slides: List of slide content dictionaries
            - charts: Decoded chart data
            - sources: Reference sources
        """
        logger.info({
            "message": "Parsing conversation content",
            "operation": "content_parse",
            "status": "started",
        })

        try:
            turns = self._sort_conversation(conversation or [])
            if not turns:
                turns = [{"question": {"content": "Report"}, "answer": {"content": ""}}]

            title = self._extract_title(turns)
            slides_content = self._organize_slides(turns)
            
            charts = decoded_charts or []
            for idx, chart in enumerate(charts):
                if "id" not in chart:
                    chart["id"] = f"chart-{idx}"
                if not chart.get("title"):
                    chart["title"] = f"Chart {idx + 1}"

            result = {
                "title": title,
                "subtitle": user_name,
                "slides": slides_content,
                "charts": charts,
                "sources": source_list or [],
                "has_charts": bool(charts),
                "has_sources": bool(source_list),
            }

            logger.info({
                "message": "Content parsing completed",
                "operation": "content_parse",
                "status": "completed",
                "num_slides": len(slides_content),
            })
            
            return result

        except Exception as e:
            logger.error({
                "message": "Error parsing content",
                "error_message": str(e),
                "status": "failed"
            })
            raise

    def _sort_conversation(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort conversation turns by index if available"""
        def key_fn(turn):
            idx = turn.get("index")
            return (0, idx) if isinstance(idx, int) else (1, len(turns))
        return sorted(turns, key=key_fn)

    def _extract_title(self, turns: List[Dict[str, Any]]) -> str:
        """Extract presentation title from first question"""
        if not turns:
            return "Report"
        
        first_q = (turns[0].get("question") or {}).get("content", "")
        return (first_q or "Report").strip()

    def _organize_slides(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Organize conversation turns into slide structure"""
        slides = []
        
        for idx, turn in enumerate(turns):
            question = (turn.get("question") or {}).get("content", "").strip()
            answer = (turn.get("answer") or {}).get("content", "").strip()
            
            if question or answer:
                slides.append({
                    "type": "content",
                    "question": question,
                    "answer": answer,
                    "index": idx,
                })
        
        return slides

