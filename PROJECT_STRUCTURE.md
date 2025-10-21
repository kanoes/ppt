# Project Structure

## Directory Tree

```
Core-PPTAutomate/
├── app.py                          # FastAPI application entry point
├── requirements.txt                # Python dependencies
├── package.json                    # Node.js configuration
├── Dockerfile                      # Docker container definition
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
│
├── docs/                           # Documentation
│   ├── README.md                   # Main documentation
│   ├── SETUP.md                    # Setup instructions
│   ├── MIGRATION.md                # Migration guide
│   ├── CHANGELOG.md                # Version history
│   ├── REFACTORING_SUMMARY.md     # Refactoring summary
│   └── PROJECT_STRUCTURE.md       # This file
│
├── src/                            # Source code
│   ├── __init__.py
│   ├── logging.py                  # Logging configuration
│   │
│   ├── api/                        # API layer
│   │   ├── __init__.py
│   │   ├── routes_generate.py     # Main API endpoint
│   │   └── generate_schema.py     # Request/response schemas
│   │
│   ├── services/                   # Business logic
│   │   ├── __init__.py
│   │   ├── content_parser.py      # Parse conversation data
│   │   ├── html_slide_generator.py # Generate HTML slides
│   │   ├── pptx_converter.py      # Convert HTML to PPTX
│   │   ├── file_saver.py          # File operations
│   │   └── llm.py                 # LLM client wrapper
│   │
│   ├── workflows/                  # Orchestration
│   │   ├── __init__.py
│   │   └── presentation_workflow.py # Main workflow
│   │
│   └── prompts/                    # LLM prompts
│       ├── __init__.py
│       └── html_slide_generator.py # Prompt templates
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── test_workflow.py           # Workflow tests
│   ├── test_html_mode.py          # (legacy, needs update)
│   └── test_insert.py             # (legacy, needs update)
│
├── resources/                      # Static resources
│   ├── smbc_template_new.pptx     # (deprecated template)
│   └── *_template_info.json       # (deprecated configs)
│
├── refactor_ideas/                 # Reference materials
│   └── pptx/                      # claude-skills/pptx reference
│       ├── SKILL.md               # html2pptx guide
│       ├── html2pptx.md           # Conversion specifications
│       ├── html2pptx.tgz          # html2pptx library
│       ├── ooxml.md               # OOXML reference
│       └── scripts/               # Utility scripts
│
├── output/                         # Generated presentations
│   └── <user_hash>/               # Per-user directories
│       └── *.pptx                 # Output files
│
└── workspace/                      # Temporary files
    ├── slides/                    # Generated HTML slides
    │   ├── slide-00-title.html
    │   ├── slide-01-content.html
    │   └── ...
    └── convert_to_pptx.js         # Generated conversion script
```

## Core Files Description

### Application Entry

- **app.py**: FastAPI application initialization, router inclusion

### API Layer

- **routes_generate.py**: `/generate` endpoint implementation
  - Request handling
  - Chart decoding
  - Workflow orchestration
  - Error handling and retries
  
- **generate_schema.py**: Pydantic models
  - `GenerateQuery`: Request schema
  - `IndicatorChart`: Chart data
  - `Source`: Reference source
  - `Assets`: Charts and sources container

### Services

- **content_parser.py**: Parse user conversation
  - Extract questions and answers
  - Organize into slide structure
  - Process chart metadata
  - Handle source references

- **html_slide_generator.py**: Generate HTML slides
  - Title slide generation
  - Content slide generation (via LLM)
  - Chart placeholder insertion
  - Sources/references slide

- **pptx_converter.py**: Convert HTML to PPTX
  - Create Node.js conversion script
  - Execute html2pptx
  - Chart insertion support
  - Error handling

- **file_saver.py**: File operations
  - Save to user-specific directories
  - File path management

- **llm.py**: Azure OpenAI client
  - Model configuration
  - JSON mode support
  - Retry logic

### Workflows

- **presentation_workflow.py**: Main orchestration
  - Complete pipeline coordination
  - Content parsing → HTML generation → PPTX conversion
  - Workspace management
  - BytesIO output

### Prompts

- **html_slide_generator.py**: LLM prompt templates
  - Design principles
  - HTML requirements
  - Styling guidelines
  - Layout rules

## Data Flow

```
1. API Request (GenerateQuery)
   ↓
2. Decode Charts (base64 → BytesIO)
   ↓
3. PresentationWorkflow.generate_presentation()
   ├─→ ContentParser.parse()
   │   └─→ Structured content data
   ├─→ HTMLSlideGenerator.generate_slides()
   │   ├─→ Title slide HTML
   │   ├─→ Content slides HTML (via LLM)
   │   └─→ Sources slide HTML
   └─→ PPTXConverter.convert_to_pptx()
       ├─→ Create Node.js script
       ├─→ Run html2pptx
       └─→ PPTX file
   ↓
4. FileSaver.save_file_to_local()
   ↓
5. API Response (fileId)
```

## File Naming Conventions

### Generated Files

- HTML slides: `slide-{NN}-{type}.html`
  - `slide-00-title.html` - Title slide
  - `slide-01-content.html` - Content slide 1
  - `slide-02-content.html` - Content slide 2
  - `slide-99-sources.html` - Sources/references

- PPTX output: `{date}-{question}-{threadId}.pptx`
  - Example: `20241021-market_outlook-thread123.pptx`

### Directory Organization

- Output: `output/{user_hash}/{filename}.pptx`
- Workspace: `workspace/slides/` and `workspace/convert_to_pptx.js`

## Dependencies

### Python
- fastapi - Web framework
- uvicorn/gunicorn - ASGI servers
- langchain-openai - LLM integration
- python-dotenv - Environment management
- azure-monitor-opentelemetry - Monitoring

### Node.js
- @ant/html2pptx - HTML to PPTX conversion
- pptxgenjs - PowerPoint generation
- playwright - HTML rendering
- sharp - Image processing

## Configuration Files

- **.env**: Environment variables (not in git)
- **.env.example**: Template for .env
- **.gitignore**: Git exclusions
- **package.json**: Node.js project config
- **requirements.txt**: Python dependencies
- **Dockerfile**: Container definition
- **azure-pipelines.yml**: CI/CD pipeline

## Testing

- **test_workflow.py**: Main workflow tests
  - ContentParser tests
  - HTMLSlideGenerator tests
  - PresentationWorkflow tests
  - Integration tests

## Documentation

All documentation uses minimal comments in code, with comprehensive external docs:

- **README.md**: Project overview and usage
- **SETUP.md**: Installation and configuration
- **MIGRATION.md**: Upgrade guide from v1.x
- **CHANGELOG.md**: Version history
- **REFACTORING_SUMMARY.md**: Detailed refactoring notes
- **PROJECT_STRUCTURE.md**: This file

## Code Style

- Minimal comments (only key areas)
- English for all logs and comments
- Type hints for function parameters
- Descriptive variable names
- Clear function purposes

## Workspace Management

The `workspace/` directory is temporary and can be cleaned:

```python
workflow.cleanup_workspace()
```

This removes all temporary files while preserving the directory structure.

