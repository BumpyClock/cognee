"""ABOUTME: Unit tests for atomic fact extraction and temporal classification prompts.
ABOUTME: Tests template rendering, variable substitution, and edge cases."""

import pytest
from cognee.infrastructure.llm.prompts import render_prompt, read_query_prompt
from cognee.root_dir import get_absolute_path


class TestAtomicFactExtractionPrompts:
    """Test suite for atomic fact extraction prompt templates."""

    @pytest.fixture
    def base_directory(self):
        """Get the base directory for cascade extract prompts."""
        return get_absolute_path("./tasks/graph/cascade_extract/prompts")

    @pytest.fixture
    def sample_context(self):
        """Sample context for testing extraction prompts."""
        return {
            "text": "John works at Google and lives in NYC.",
            "previous_facts": [
                {"subject": "John", "predicate": "works at", "object": "Google"}
            ],
            "round_number": 2,
            "total_rounds": 3,
        }

    def test_extraction_system_prompt_loads(self, base_directory):
        """Test that extraction system prompt loads without errors."""
        system_prompt = read_query_prompt(
            "extract_atomic_facts_prompt_system.txt", base_directory=base_directory
        )
        assert system_prompt is not None
        assert len(system_prompt) > 0
        assert "atomic fact" in system_prompt.lower()

    def test_extraction_input_template_renders(self, base_directory, sample_context):
        """Test that extraction input template renders correctly."""
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            sample_context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "John works at Google and lives in NYC" in rendered
        assert "round 2 of 3" in rendered
        assert "Google" in rendered

    def test_extraction_prompt_with_empty_text(self, base_directory):
        """Test extraction prompt with empty text."""
        context = {
            "text": "",
            "previous_facts": [],
            "round_number": 1,
            "total_rounds": 1,
        }
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "round 1 of 1" in rendered

    def test_extraction_prompt_with_long_text(self, base_directory):
        """Test extraction prompt with very long text (>10k chars)."""
        long_text = "A" * 15000  # 15k characters
        context = {
            "text": long_text,
            "previous_facts": [],
            "round_number": 1,
            "total_rounds": 2,
        }
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert long_text in rendered

    def test_extraction_prompt_with_special_characters(self, base_directory):
        """Test extraction prompt with special characters."""
        context = {
            "text": "Revenue was $1M in Q1'24. CEO's salary: €500k/year!",
            "previous_facts": [],
            "round_number": 1,
            "total_rounds": 1,
        }
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "$1M" in rendered
        assert "€500k/year" in rendered

    def test_extraction_prompt_with_unicode(self, base_directory):
        """Test extraction prompt with unicode characters."""
        context = {
            "text": "François Müller führt das Unternehmen. 日本の首都は東京です。",
            "previous_facts": [],
            "round_number": 1,
            "total_rounds": 1,
        }
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "François Müller" in rendered
        assert "東京" in rendered

    def test_extraction_prompt_all_variables_substituted(
        self, base_directory, sample_context
    ):
        """Test that all template variables are properly substituted."""
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            sample_context,
            base_directory=base_directory,
        )
        # Check that no Jinja2 template syntax remains
        assert "{{" not in rendered
        assert "}}" not in rendered
        assert "{%" not in rendered
        assert "%}" not in rendered


class TestTemporalClassificationPrompts:
    """Test suite for temporal classification prompt templates."""

    @pytest.fixture
    def base_directory(self):
        """Get the base directory for cascade extract prompts."""
        return get_absolute_path("./tasks/graph/cascade_extract/prompts")

    @pytest.fixture
    def sample_classification_context(self):
        """Sample context for testing classification prompts."""
        return {
            "source_text": "Tesla's stock price was $250 on January 1, 2024. The CEO is Elon Musk.",
            "facts_list": [
                {"subject": "Tesla stock price", "predicate": "was", "object": "$250"},
                {
                    "subject": "Stock price measurement",
                    "predicate": "occurred on",
                    "object": "January 1, 2024",
                },
                {"subject": "The CEO", "predicate": "is", "object": "Elon Musk"},
            ],
            "context": "Financial data from quarterly report",
        }

    def test_classification_system_prompt_loads(self, base_directory):
        """Test that classification system prompt loads without errors."""
        system_prompt = read_query_prompt(
            "classify_atomic_fact_prompt_system.txt", base_directory=base_directory
        )
        assert system_prompt is not None
        assert len(system_prompt) > 0
        assert "temporal" in system_prompt.lower()
        assert "FACT" in system_prompt
        assert "OPINION" in system_prompt
        assert "PREDICTION" in system_prompt
        assert "ATEMPORAL" in system_prompt
        assert "STATIC" in system_prompt
        assert "DYNAMIC" in system_prompt

    def test_classification_input_template_renders(
        self, base_directory, sample_classification_context
    ):
        """Test that classification input template renders correctly."""
        rendered = render_prompt(
            "classify_atomic_fact_prompt_input.txt",
            sample_classification_context,
            base_directory=base_directory,
        )
        assert rendered is not None
        # Check for content (may be HTML-escaped)
        assert ("Tesla's stock price" in rendered or "Tesla&#39;s stock price" in rendered)
        assert "Elon Musk" in rendered
        assert "Financial data" in rendered

    def test_classification_prompt_with_empty_facts(self, base_directory):
        """Test classification prompt with empty facts list."""
        context = {
            "source_text": "Some text",
            "facts_list": [],
            "context": "No facts extracted",
        }
        rendered = render_prompt(
            "classify_atomic_fact_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "Some text" in rendered

    def test_classification_prompt_with_many_facts(self, base_directory):
        """Test classification prompt with many facts (100+)."""
        many_facts = [
            {
                "subject": f"Entity{i}",
                "predicate": "relates to",
                "object": f"Value{i}",
            }
            for i in range(150)
        ]
        context = {
            "source_text": "Source document with many facts",
            "facts_list": many_facts,
            "context": "Large dataset",
        }
        rendered = render_prompt(
            "classify_atomic_fact_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "Entity0" in rendered
        assert "Entity149" in rendered

    def test_classification_prompt_with_special_characters(self, base_directory):
        """Test classification prompt with special characters in facts."""
        context = {
            "source_text": "Revenue data: $1M, €500k, ¥10M",
            "facts_list": [
                {
                    "subject": "Revenue (USD)",
                    "predicate": "equals",
                    "object": "$1M @ 2024",
                }
            ],
            "context": "Multi-currency & special chars!",
        }
        rendered = render_prompt(
            "classify_atomic_fact_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        # Check for content (special chars may be HTML-escaped)
        assert "$1M" in rendered
        assert "2024" in rendered
        assert ("Multi-currency & special chars!" in rendered or
                "Multi-currency &amp; special chars!" in rendered)

    def test_classification_prompt_all_variables_substituted(
        self, base_directory, sample_classification_context
    ):
        """Test that all template variables are properly substituted."""
        rendered = render_prompt(
            "classify_atomic_fact_prompt_input.txt",
            sample_classification_context,
            base_directory=base_directory,
        )
        # Check that no Jinja2 template syntax remains
        assert "{{" not in rendered
        assert "}}" not in rendered
        assert "{%" not in rendered
        assert "%}" not in rendered

    def test_classification_prompt_with_nested_data(self, base_directory):
        """Test classification prompt with nested fact structures."""
        context = {
            "source_text": "Complex nested data",
            "facts_list": [
                {
                    "subject": "Company",
                    "predicate": "has",
                    "object": "Department",
                    "metadata": {"confidence": 0.95, "source": "official docs"},
                }
            ],
            "context": "Hierarchical organization",
        }
        rendered = render_prompt(
            "classify_atomic_fact_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "Company" in rendered


class TestPromptEdgeCases:
    """Test suite for edge cases across all prompts."""

    @pytest.fixture
    def base_directory(self):
        """Get the base directory for cascade extract prompts."""
        return get_absolute_path("./tasks/graph/cascade_extract/prompts")

    def test_prompt_with_newlines_in_text(self, base_directory):
        """Test prompts with text containing multiple newlines."""
        context = {
            "text": "Line 1\n\nLine 2\n\n\nLine 3",
            "previous_facts": [],
            "round_number": 1,
            "total_rounds": 1,
        }
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "Line 1" in rendered
        assert "Line 3" in rendered

    def test_prompt_with_quotes_in_text(self, base_directory):
        """Test prompts with various quote types."""
        context = {
            "text": 'He said "Hello" and she replied \'Hi\' with a smile.',
            "previous_facts": [],
            "round_number": 1,
            "total_rounds": 1,
        }
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "Hello" in rendered
        assert "Hi" in rendered

    def test_prompt_with_html_like_content(self, base_directory):
        """Test prompts with HTML-like content (should be escaped)."""
        context = {
            "text": "<div>Some content</div> & <span>more</span>",
            "previous_facts": [],
            "round_number": 1,
            "total_rounds": 1,
        }
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        # Jinja2 with autoescape should escape HTML
        assert "content" in rendered

    def test_prompt_with_none_context_values(self, base_directory):
        """Test prompts with None values in context."""
        context = {
            "text": "Valid text",
            "previous_facts": None,
            "round_number": 1,
            "total_rounds": 1,
        }
        rendered = render_prompt(
            "extract_atomic_facts_prompt_input.txt",
            context,
            base_directory=base_directory,
        )
        assert rendered is not None
        assert "Valid text" in rendered

    def test_all_prompts_exist(self, base_directory):
        """Test that all required prompt files exist."""
        required_prompts = [
            "extract_atomic_facts_prompt_system.txt",
            "extract_atomic_facts_prompt_input.txt",
            "classify_atomic_fact_prompt_system.txt",
            "classify_atomic_fact_prompt_input.txt",
        ]
        for prompt_file in required_prompts:
            prompt = read_query_prompt(prompt_file, base_directory=base_directory)
            assert prompt is not None, f"{prompt_file} should exist and be readable"
            assert len(prompt) > 0, f"{prompt_file} should not be empty"
