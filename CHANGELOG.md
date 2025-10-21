# Changelog

## [2.0.0] - 2024-10-21

### Major Refactoring - Unified HTML-to-PPTX Architecture

#### Breaking Changes

- **Removed MODE system**: No separate PPT and HTML modes
- **Single endpoint**: `/generate` replaces `/generate-ppt` and `/generate-html`
- **Removed python-pptx**: Now uses html2pptx for conversion
- **Removed template system**: Dynamic HTML generation instead

#### Added

- **Unified workflow**: HTML Generation → PPTX Conversion pipeline
- **Node.js integration**: html2pptx library for conversion
- **New services**:
  - `content_parser.py` - Parse conversation data
  - `html_slide_generator.py` - Generate HTML slides
  - `pptx_converter.py` - Convert HTML to PPTX
  - `file_saver.py` - Unified file operations
- **Workflow orchestration**: `presentation_workflow.py`
- **Design principles**: Web-safe fonts, proper layouts, contrast guidelines
- **Documentation**:
  - Comprehensive README.md
  - SETUP.md for installation
  - MIGRATION.md for upgrade guide
- **Docker support**: Updated Dockerfile with Node.js

#### Changed

- **API endpoint**: Unified `/generate` for all requests
- **Response format**: Always returns PPTX file
- **Architecture**: Simplified from dual-mode to single pipeline
- **Dependencies**: Removed python-pptx, cleaned requirements
- **Logging**: Improved English logs with minimal comments

#### Removed

- MODE environment variable
- Template-based generation system
- Separate HTML/PPT generation endpoints
- Old services: `html_generator/`, `html_saver/`, `ppt_generator/`, `ppt_saver/`
- Old prompts: `prompt/html/`, `prompt/ppt/`
- Template JSON configuration files
- python-pptx dependency

#### Inspiration

This refactoring is inspired by [claude-skills/pptx](https://github.com/anthropics/claude-skills), adopting:
- HTML-first slide generation approach
- Design principles and guidelines
- html2pptx workflow
- Proper color palette selection
- Web-safe font requirements
- Layout best practices

#### Migration

See MIGRATION.md for detailed upgrade instructions.

---

## [1.x.x] - Previous versions

Legacy version with dual PPT/HTML modes using python-pptx templates.

