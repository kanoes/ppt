import pytest
from pathlib import Path
from src.services.content_parser import ContentParser
from src.services.html_slide_generator import HTMLSlideGenerator
from src.workflows.presentation_workflow import PresentationWorkflow


class TestContentParser:
    """Test content parsing functionality"""

    def test_parse_basic_conversation(self):
        parser = ContentParser()
        
        conversation = [
            {
                "index": 0,
                "question": {"content": "What is the market outlook?"},
                "answer": {"content": "The market shows positive trends."}
            }
        ]
        
        result = parser.parse(
            user_name="Test User",
            conversation=conversation,
        )
        
        assert result["title"] == "What is the market outlook?"
        assert result["subtitle"] == "Test User"
        assert len(result["slides"]) == 1
        assert result["slides"][0]["question"] == "What is the market outlook?"
        assert result["slides"][0]["answer"] == "The market shows positive trends."

    def test_parse_with_charts(self):
        parser = ContentParser()
        
        conversation = [
            {
                "question": {"content": "Chart Analysis"},
                "answer": {"content": "See the chart below."}
            }
        ]
        
        charts = [
            {"title": "Sales Data", "image": "mock_image_data"}
        ]
        
        result = parser.parse(
            user_name="Test User",
            conversation=conversation,
            decoded_charts=charts,
        )
        
        assert result["has_charts"] is True
        assert len(result["charts"]) == 1
        assert result["charts"][0]["title"] == "Sales Data"

    def test_parse_with_sources(self):
        parser = ContentParser()
        
        conversation = [
            {
                "question": {"content": "Research Summary"},
                "answer": {"content": "Based on multiple sources."}
            }
        ]
        
        sources = [
            {"title": "Report A", "link": "https://example.com/a"},
            {"title": "Report B", "link": "https://example.com/b"}
        ]
        
        result = parser.parse(
            user_name="Test User",
            conversation=conversation,
            source_list=sources,
        )
        
        assert result["has_sources"] is True
        assert len(result["sources"]) == 2


class TestHTMLSlideGenerator:
    """Test HTML slide generation"""

    def test_generate_title_slide(self, tmp_path):
        generator = HTMLSlideGenerator(output_dir=str(tmp_path))
        
        slide_file = generator._generate_title_slide(
            title="Test Presentation",
            subtitle="Test Author"
        )
        
        assert Path(slide_file).exists()
        content = Path(slide_file).read_text()
        assert "Test Presentation" in content
        assert "Test Author" in content
        assert "<!DOCTYPE html>" in content

    def test_generate_sources_slide(self, tmp_path):
        generator = HTMLSlideGenerator(output_dir=str(tmp_path))
        
        sources = [
            {"title": "Source 1", "link": "https://example.com/1"},
            {"title": "Source 2", "link": "https://example.com/2"}
        ]
        
        slide_file = generator._generate_sources_slide(sources)
        
        assert Path(slide_file).exists()
        content = Path(slide_file).read_text()
        assert "References" in content
        assert "Source 1" in content
        assert "https://example.com/1" in content


class TestPresentationWorkflow:
    """Test complete presentation workflow"""

    def test_workflow_initialization(self, tmp_path):
        workflow = PresentationWorkflow(workspace_dir=str(tmp_path))
        assert workflow.workspace_dir.exists()
        assert workflow.content_parser is not None
        assert workflow.html_generator is not None
        assert workflow.pptx_converter is not None

    def test_cleanup_workspace(self, tmp_path):
        workflow = PresentationWorkflow(workspace_dir=str(tmp_path))
        
        test_file = workflow.workspace_dir / "test.txt"
        test_file.write_text("test")
        
        workflow.cleanup_workspace()
        
        assert workflow.workspace_dir.exists()
        assert not test_file.exists()


@pytest.fixture
def sample_conversation():
    return [
        {
            "index": 0,
            "question": {"content": "Market Overview"},
            "answer": {"content": "The market is performing well."}
        },
        {
            "index": 1,
            "question": {"content": "Risk Analysis"},
            "answer": {"content": "Risks are moderate."}
        }
    ]


@pytest.fixture
def sample_charts():
    return [
        {"title": "Chart 1", "image": "mock_data_1"},
        {"title": "Chart 2", "image": "mock_data_2"}
    ]


@pytest.fixture
def sample_sources():
    return [
        {"title": "Research Report", "link": "https://example.com"}
    ]

