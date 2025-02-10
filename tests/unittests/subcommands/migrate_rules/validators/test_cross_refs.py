"""Test suite for CrossRefValidator.

This module contains tests for the CrossRefValidator class, which validates
cross-references between MDC files.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from contextforge_cli.subcommands.migrate_rules.models.context import MDCContext
from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationSeverity,
)
from contextforge_cli.subcommands.migrate_rules.validators.cross_refs import (
    CrossRefConfig,
    CrossRefValidator,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def basic_config(tmp_path: Path) -> CrossRefConfig:
    """Create a basic CrossRefConfig for testing.

    Args:
        tmp_path: Pytest fixture providing a temporary directory path

    Returns:
        CrossRefConfig: A basic configuration for testing
    """
    return CrossRefConfig(
        allowed_extensions={".md", ".mdc"},
        validate_external_urls=True,
        require_relative_paths=True,
        allow_anchor_only_refs=True,
        validate_anchors=True,
        base_path=tmp_path,
        ignored_urls={"https://example.com/ignored"},
        required_ref_prefixes={"docs/", "./docs/"},
        max_reference_depth=3,
    )


@pytest.fixture
def validator(basic_config: CrossRefConfig) -> CrossRefValidator:
    """Create a CrossRefValidator instance with basic configuration.

    Args:
        basic_config: The basic configuration to use

    Returns:
        CrossRefValidator: A configured validator instance
    """
    return CrossRefValidator(config=basic_config)


@pytest.mark.asyncio
async def test_valid_internal_reference(
    validator: CrossRefValidator,
    tmp_path: Path,
) -> None:
    """Test validation of valid internal references.

    Args:
        validator: The configured validator instance
        tmp_path: Pytest fixture providing a temporary directory path
    """
    # Create a test file
    test_file = tmp_path / "docs" / "test.md"
    test_file.parent.mkdir(exist_ok=True)
    test_file.touch()

    content = """
# Test Document

[Link to test](docs/test.md)
"""
    context = MDCContext(content=content, file_path=str(tmp_path / "source.md"))
    results = await validator.validate(context)
    assert not results, "Expected no validation errors for valid internal reference"


@pytest.mark.asyncio
async def test_invalid_file_extension(validator: CrossRefValidator) -> None:
    """Test validation of references with invalid file extensions.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

[Invalid extension](docs/test.txt)
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Invalid file extension" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_missing_file(validator: CrossRefValidator) -> None:
    """Test validation of references to non-existent files.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

[Missing file](docs/missing.md)
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Referenced file does not exist" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_valid_anchor_reference(validator: CrossRefValidator) -> None:
    """Test validation of valid anchor references.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

## Section One

[Link to section](#section-one)
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert not results, "Expected no validation errors for valid anchor reference"


@pytest.mark.asyncio
async def test_invalid_anchor_reference(validator: CrossRefValidator) -> None:
    """Test validation of invalid anchor references.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

[Invalid anchor](#non-existent-section)
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Invalid anchor reference" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_external_url_validation(validator: CrossRefValidator) -> None:
    """Test validation of external URLs.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

[Valid URL](https://example.com/valid)
[Invalid URL](https:invalid-url)
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Invalid external URL" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_ignored_urls(validator: CrossRefValidator) -> None:
    """Test that ignored URLs are skipped during validation.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

[Ignored URL](https://example.com/ignored)
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert not results, "Expected no validation errors for ignored URL"


@pytest.mark.asyncio
async def test_reference_style_links(validator: CrossRefValidator) -> None:
    """Test validation of reference-style links.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

[Reference link][ref1]

[ref1]: docs/non-existent.md
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Referenced file does not exist" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_links_in_code_blocks(validator: CrossRefValidator) -> None:
    """Test that links in code blocks are ignored.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

```markdown
[This link should be ignored](invalid.txt)
```
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert not results, "Expected no validation errors for links in code blocks"


@pytest.mark.asyncio
async def test_absolute_paths(validator: CrossRefValidator) -> None:
    """Test validation of absolute paths in references.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

[Absolute path](/docs/test.md)
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Absolute paths are not allowed" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_empty_references(validator: CrossRefValidator) -> None:
    """Test validation of empty references.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

[Empty reference]()
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Empty reference URL" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_custom_config() -> None:
    """Test CrossRefValidator with custom configuration."""
    custom_config = CrossRefConfig(
        allowed_extensions={".txt"},
        validate_external_urls=False,
        require_relative_paths=False,
        allow_anchor_only_refs=False,
        validate_anchors=False,
    )
    validator = CrossRefValidator(config=custom_config)

    content = """
# Test Document

[Absolute path](/path/to/file.txt)
[Anchor only](#section)
"""
    context = MDCContext(content=content, file_path="test.md")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Anchor-only references are not allowed" in results[0].message
