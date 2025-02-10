"""Test suite for XMLTagValidator.

This module contains tests for the XMLTagValidator class, which validates XML tags
in MDC files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Set

import pytest

from contextforge_cli.subcommands.migrate_rules.models.context import MDCContext
from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationSeverity,
)
from contextforge_cli.subcommands.migrate_rules.validators.xml_tags import (
    XMLTagConfig,
    XMLTagValidator,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def basic_config() -> XMLTagConfig:
    """Create a basic XMLTagConfig for testing.

    Returns:
        XMLTagConfig: A basic configuration for testing
    """
    return XMLTagConfig(
        required_tags={"required-tag"},
        allowed_tags={"required-tag", "optional-tag", "self-closing-tag"},
        required_attributes={"required-tag": {"id", "class"}},
        allowed_attributes={"required-tag": {"id", "class", "data-test"}},
        max_nesting_depth=3,
        validate_xml_syntax=True,
    )


@pytest.fixture
def validator(basic_config: XMLTagConfig) -> XMLTagValidator:
    """Create an XMLTagValidator instance with basic configuration.

    Args:
        basic_config: The basic configuration to use

    Returns:
        XMLTagValidator: A configured validator instance
    """
    return XMLTagValidator(config=basic_config)


@pytest.mark.asyncio
async def test_valid_xml_tags(validator: XMLTagValidator) -> None:
    """Test validation of valid XML tags.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<required-tag id="test" class="test-class">
    <optional-tag>Content</optional-tag>
    <self-closing-tag />
</required-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert not results, "Expected no validation errors for valid XML tags"


@pytest.mark.asyncio
async def test_missing_required_tag(validator: XMLTagValidator) -> None:
    """Test validation when a required tag is missing.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<optional-tag>Content</optional-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Missing required XML tags: required-tag" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_unauthorized_tag(validator: XMLTagValidator) -> None:
    """Test validation of unauthorized XML tags.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<unauthorized-tag>Content</unauthorized-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert len(results) == 2  # One for unauthorized tag, one for missing required tag
    assert any("Unauthorized XML tag: unauthorized-tag" in r.message for r in results)
    assert all(r.severity == ValidationSeverity.ERROR for r in results)


@pytest.mark.asyncio
async def test_missing_required_attributes(validator: XMLTagValidator) -> None:
    """Test validation when required attributes are missing.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<required-tag>Content</required-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Missing required attributes" in results[0].message
    assert "id" in results[0].message and "class" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_invalid_attributes(validator: XMLTagValidator) -> None:
    """Test validation of invalid attributes.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<required-tag id="test" class="test-class" invalid-attr="value">
    Content
</required-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Invalid attributes" in results[0].message
    assert "invalid-attr" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_nesting_depth(validator: XMLTagValidator) -> None:
    """Test validation of XML tag nesting depth.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<required-tag id="test" class="test-class">
    <optional-tag>
        <optional-tag>
            <optional-tag>
                Too deep
            </optional-tag>
        </optional-tag>
    </optional-tag>
</required-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "XML tag nesting too deep" in results[0].message
    assert results[0].severity == ValidationSeverity.WARNING


@pytest.mark.asyncio
async def test_unclosed_tags(validator: XMLTagValidator) -> None:
    """Test validation of unclosed XML tags.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<required-tag id="test" class="test-class">
    <optional-tag>
        Unclosed tag
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert len(results) == 1
    assert "Unclosed XML tags" in results[0].message
    assert results[0].severity == ValidationSeverity.ERROR


@pytest.mark.asyncio
async def test_mismatched_tags(validator: XMLTagValidator) -> None:
    """Test validation of mismatched XML tags.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<required-tag id="test" class="test-class">
    <optional-tag>
        Content
    </required-tag>
</optional-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert len(results) >= 1
    assert any("Mismatched closing tag" in r.message for r in results)
    assert all(r.severity == ValidationSeverity.ERROR for r in results)


@pytest.mark.asyncio
async def test_tags_in_code_blocks(validator: XMLTagValidator) -> None:
    """Test that XML tags in code blocks are ignored.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<required-tag id="test" class="test-class">
    Content
</required-tag>

```xml
<unauthorized-tag>
    This should be ignored
</unauthorized-tag>
```
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert not results, "Expected no validation errors for XML tags in code blocks"


@pytest.mark.asyncio
async def test_self_closing_tags(validator: XMLTagValidator) -> None:
    """Test validation of self-closing XML tags.

    Args:
        validator: The configured validator instance
    """
    content = """
# Test Document

<required-tag id="test" class="test-class">
    <self-closing-tag />
    <self-closing-tag/>
</required-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert not results, "Expected no validation errors for self-closing tags"


@pytest.mark.asyncio
async def test_custom_config() -> None:
    """Test XMLTagValidator with custom configuration."""
    custom_config = XMLTagConfig(
        required_tags={"custom-tag"},
        allowed_tags={"custom-tag", "other-tag"},
        required_attributes={"custom-tag": {"required-attr"}},
        allowed_attributes={"custom-tag": {"required-attr", "optional-attr"}},
        max_nesting_depth=2,
        validate_xml_syntax=True,
    )
    validator = XMLTagValidator(config=custom_config)

    content = """
# Test Document

<custom-tag required-attr="value" optional-attr="value">
    <other-tag>Content</other-tag>
</custom-tag>
"""
    context = MDCContext(content=content, file_path="test.mdc")
    results = await validator.validate(context)
    assert not results, "Expected no validation errors with custom configuration"
