import os
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.logging import get_logger

logger = get_logger("pptx_converter")


class PPTXConverter:
    """Convert HTML slides to PowerPoint using html2pptx"""

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir or "workspace")
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def convert_to_pptx(
        self,
        slide_files: List[str],
        output_path: str,
        charts: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        Convert HTML slides to PPTX using Node.js script
        
        Args:
            slide_files: List of HTML file paths
            output_path: Output PPTX file path
            charts: Optional chart data to add to placeholders
            
        Returns:
            Path to generated PPTX file
        """
        logger.info({
            "message": "Starting PPTX conversion",
            "operation": "pptx_convert",
            "status": "started",
            "num_slides": len(slide_files),
        })

        try:
            script_path = self._create_converter_script(
                slide_files,
                output_path,
                charts or []
            )
            
            self._run_node_script(script_path)
            
            if not Path(output_path).exists():
                raise FileNotFoundError(f"PPTX file not created: {output_path}")

            logger.info({
                "message": "PPTX conversion completed",
                "operation": "pptx_convert",
                "status": "completed",
                "output_path": output_path,
            })

            return output_path

        except Exception as e:
            logger.error({
                "message": "Error converting to PPTX",
                "error_message": str(e),
                "status": "failed",
            })
            raise

    def _create_converter_script(
        self,
        slide_files: List[str],
        output_path: str,
        charts: List[Dict[str, Any]]
    ) -> str:
        """Create Node.js script for conversion"""
        script_content = f"""const pptxgen = require('pptxgenjs');
const {{ html2pptx }} = require('@ant/html2pptx');
const fs = require('fs');

async function createPresentation() {{
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_16x9';
  pptx.author = 'PPT Automate';
  pptx.title = 'Generated Presentation';

  const slideFiles = {slide_files};
  
  for (const htmlFile of slideFiles) {{
    console.log(`Processing: ${{htmlFile}}`);
    try {{
      const {{ slide, placeholders }} = await html2pptx(htmlFile, pptx);
      
      // Add charts to placeholders if needed
      if (placeholders.length > 0) {{
        console.log(`Found ${{placeholders.length}} placeholder(s)`);
        // Chart insertion logic can be added here
      }}
    }} catch (err) {{
      console.error(`Error processing ${{htmlFile}}:`, err.message);
      throw err;
    }}
  }}

  await pptx.writeFile({{ fileName: '{output_path}' }});
  console.log('Presentation created successfully!');
}}

createPresentation().catch(err => {{
  console.error('Fatal error:', err);
  process.exit(1);
}});
"""
        
        script_path = self.workspace_dir / "convert_to_pptx.js"
        script_path.write_text(script_content, encoding="utf-8")
        return str(script_path)

    def _run_node_script(self, script_path: str):
        """Execute Node.js conversion script"""
        node_path = subprocess.run(
            ["npm", "root", "-g"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()

        env = os.environ.copy()
        env["NODE_PATH"] = node_path

        result = subprocess.run(
            ["node", script_path],
            env=env,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            logger.error({
                "message": "Node.js script failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
            })
            raise RuntimeError(f"Node.js conversion failed: {result.stderr}")

        logger.info({
            "message": "Node.js script executed successfully",
            "stdout": result.stdout,
        })

