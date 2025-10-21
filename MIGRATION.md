# Migration Guide

## Overview of Changes

This refactoring transforms Core-PPTAutomate from a dual-mode system (PPT/HTML) into a unified HTML-to-PPTX workflow inspired by claude-skills/pptx.

## What Changed

### Removed

1. **Mode System**: No more `MODE` environment variable or separate PPT/HTML endpoints
2. **Template System**: Removed python-pptx template-based generation
3. **Old Services**:
   - `src/services/html_generator/`
   - `src/services/html_saver/`
   - `src/services/ppt_generator/`
   - `src/services/ppt_saver/`
4. **Old Prompts**:
   - `src/prompt/html/`
   - `src/prompt/ppt/`
5. **Resources**: Template JSON files (deprecated but kept for reference)

### Added

1. **Unified Workflow**: Single `/generate` endpoint
2. **New Services**:
   - `content_parser.py` - Parse conversation data
   - `html_slide_generator.py` - Generate HTML slides
   - `pptx_converter.py` - Convert HTML to PPTX using Node.js
   - `file_saver.py` - Unified file saving
3. **Workflow Orchestration**: `presentation_workflow.py`
4. **Node.js Integration**: html2pptx for conversion
5. **Documentation**: README, SETUP, and this MIGRATION guide

### Modified

1. **API Endpoint**: Unified `/generate` replaces `/generate-ppt` and `/generate-html`
2. **LLM Service**: Simplified, removed unnecessary wrappers
3. **Dockerfile**: Now includes Node.js and html2pptx
4. **Requirements**: Removed python-pptx, cleaned dependencies

## Architecture Comparison

### Before

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
   ┌───▼────┐
   │  MODE  │
   └───┬────┘
       │
   ┌───▼────────────────┐
   │  PPT Mode          │   HTML Mode
   │  ├─ ContentParser  │   ├─ HTMLParser
   │  ├─ PPTGenerator   │   ├─ HTMLGenerator
   │  └─ Template       │   └─ HTMLSaver
   └────────────────────┘
```

### After

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
   ┌───▼────────────────┐
   │  PresentationFlow  │
   │  ├─ ContentParser  │
   │  ├─ HTMLGenerator  │
   │  └─ PPTXConverter  │
   │      (Node.js)     │
   └────────────────────┘
```

## API Changes

### Request (No Change)

```json
{
  "userName": "User",
  "threadId": "123",
  "conversation": [...],
  "assets": {
    "indicatorCharts": [...],
    "sourceList": [...]
  }
}
```

### Response

Before:
```json
// PPT mode
{"fileId": "file.pptx"}
// HTML mode
{"fileId": "file.html", "mode": "html"}
```

After:
```json
{"fileId": "file.pptx"}
```

## Environment Variables

### Removed
- `MODE` - No longer needed

### Kept
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `DEFAULT_LLM_DEPLOYMENT`
- `DEFAULT_LLM_TEMPERATURE`

## Code Migration

### If You Extended the Old System

#### Old ContentParser → New ContentParser

Before:
```python
from src.services.ppt_generator.pres_generator import ContentParser

parser = ContentParser()
slides = parser.parse(user_name, conversation, decoded_charts, source_list)
```

After:
```python
from src.services.content_parser import ContentParser

parser = ContentParser()
content_data = parser.parse(user_name, conversation, decoded_charts, source_list)
# Returns dict with title, subtitle, slides, charts, sources
```

#### Old Workflow → New Workflow

Before:
```python
from src.services.ppt_generator.pres_generator import PPTGenerator

generator = PPTGenerator(template_path="resources/template.pptx")
ppt_file = generator.generate(slides)
```

After:
```python
from src.workflows.presentation_workflow import PresentationWorkflow

workflow = PresentationWorkflow()
ppt_file = workflow.generate_presentation(
    user_name, conversation, decoded_charts, source_list
)
```

### Custom Slide Generation

If you had custom slide factories, you'll need to adapt them to generate HTML instead:

Before (Python with python-pptx):
```python
class CustomSlideFactory:
    def create_slide(self, data, presentation):
        slide = presentation.slides.add_slide(layout)
        # Manipulate slide...
```

After (Generate HTML):
```python
def generate_custom_slide_html(data):
    return f"""<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ width: 720pt; height: 405pt; display: flex; }}
  </style>
</head>
<body>
  <div><p>{data['content']}</p></div>
</body>
</html>"""
```

## Dependencies

### Python

Removed:
- `python-pptx`
- `pptx_ea_font`

All other dependencies unchanged.

### Node.js (New)

Added:
- `@ant/html2pptx` (from tarball)

Install:
```bash
npm install -g ./refactor_ideas/pptx/html2pptx.tgz
```

## Deployment

### Docker

The new Dockerfile includes Node.js installation. Rebuild your images:

```bash
docker build -t ppt-automate:v2 .
```

### Azure DevOps / CI/CD

Update your pipeline to:
1. Install Node.js 18+
2. Install html2pptx globally
3. Run tests

Example pipeline addition:
```yaml
- task: NodeTool@0
  inputs:
    versionSpec: '18.x'
  displayName: 'Install Node.js'

- script: |
    npm install -g ./refactor_ideas/pptx/html2pptx.tgz
  displayName: 'Install html2pptx'
```

## Testing

### Old Tests

Tests in `tests/` directory may need updates:
- `test_TemplateInfo.py` - Template system removed, delete or adapt
- `test_html_mode.py` - Update to test new workflow
- `test_insert.py` - Update to test new HTML generation

### Testing the New System

```python
from src.workflows.presentation_workflow import PresentationWorkflow

workflow = PresentationWorkflow(workspace_dir="test_workspace")

ppt_io = workflow.generate_presentation(
    user_name="Test User",
    conversation=[{
        "question": {"content": "Test Q"},
        "answer": {"content": "Test A"}
    }],
)

assert ppt_io is not None
```

## Troubleshooting

### "Cannot find module '@ant/html2pptx'"

```bash
npm install -g ./refactor_ideas/pptx/html2pptx.tgz
export NODE_PATH=$(npm root -g)
```

### "Template not found"

The old template system is removed. The new system generates slides from scratch.

### Missing Fonts in Generated PPTX

Ensure you're using web-safe fonts only in HTML generation:
- Arial, Helvetica, Times New Roman, Georgia
- Courier New, Verdana, Tahoma, Trebuchet MS, Impact

### Gradients Not Appearing

CSS gradients don't convert to PPTX. Use solid colors or pre-render gradients as PNG images.

## Rollback

If you need to rollback:

```bash
git checkout <previous-commit>
```

The old system is preserved in git history.

## Support

For issues or questions:
1. Check SETUP.md for installation steps
2. Review README.md for architecture details
3. Inspect refactor_ideas/pptx/SKILL.md for html2pptx guidelines

