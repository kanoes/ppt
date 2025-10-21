from typing import Dict, Any, List, Optional, BinaryIO
from pathlib import Path
import io

from src.logging import get_logger
from src.services.content_parser import ContentParser
from src.services.html_slide_generator import HTMLSlideGenerator
from src.services.pptx_converter import PPTXConverter

logger = get_logger("presentation_workflow")


class PresentationWorkflow:
    """
    Unified workflow for presentation generation
    HTML Generation → PPTX Conversion
    """

    def __init__(
        self,
        workspace_dir: Optional[str] = None,
        content_parser: Optional[ContentParser] = None,
        html_generator: Optional[HTMLSlideGenerator] = None,
        pptx_converter: Optional[PPTXConverter] = None,
    ):
        self.workspace_dir = Path(workspace_dir or "workspace")
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        self.content_parser = content_parser or ContentParser()
        self.html_generator = html_generator or HTMLSlideGenerator(
            output_dir=str(self.workspace_dir / "slides")
        )
        self.pptx_converter = pptx_converter or PPTXConverter(
            workspace_dir=str(self.workspace_dir)
        )

    def generate_presentation(
        self,
        user_name: str,
        conversation: List[Dict[str, Any]],
        decoded_charts: Optional[List[Dict[str, Any]]] = None,
        source_list: Optional[List[Dict[str, str]]] = None,
        output_filename: Optional[str] = None,
    ) -> BinaryIO:
        """
        Complete workflow: Parse content → Generate HTML slides → Convert to PPTX
        
        Args:
            user_name: User name for subtitle
            conversation: List of Q&A turns
            decoded_charts: Optional decoded chart images
            source_list: Optional reference sources
            output_filename: Optional custom output filename
            
        Returns:
            BytesIO object containing the PPTX file
        """
        logger.info({
            "message": "Starting presentation generation workflow",
            "operation": "workflow",
            "status": "started",
            "user_name": user_name,
        })

        try:
            # Step 1: Parse content
            content_data = self.content_parser.parse(
                user_name=user_name,
                conversation=conversation,
                decoded_charts=decoded_charts,
                source_list=source_list,
            )

            # Step 2: Generate HTML slides
            slide_files = self.html_generator.generate_slides(content_data)

            # Step 3: Convert to PPTX
            output_path = self.workspace_dir / (output_filename or "presentation.pptx")
            self.pptx_converter.convert_to_pptx(
                slide_files=slide_files,
                output_path=str(output_path),
                charts=content_data.get("charts"),
            )

            # Step 4: Read and return as BytesIO
            with open(output_path, "rb") as f:
                pptx_data = f.read()
            
            pptx_io = io.BytesIO(pptx_data)
            pptx_io.seek(0)

            logger.info({
                "message": "Presentation generation workflow completed",
                "operation": "workflow",
                "status": "completed",
            })

            return pptx_io

        except Exception as e:
            logger.error({
                "message": "Error in presentation workflow",
                "error_message": str(e),
                "status": "failed",
            })
            raise

    def cleanup_workspace(self):
        """Clean up temporary files in workspace"""
        try:
            import shutil
            if self.workspace_dir.exists():
                shutil.rmtree(self.workspace_dir)
                self.workspace_dir.mkdir(parents=True, exist_ok=True)
            logger.info({"message": "Workspace cleaned up"})
        except Exception as e:
            logger.warning({"message": f"Failed to clean workspace: {e}"})

