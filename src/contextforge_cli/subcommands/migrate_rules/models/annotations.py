"""Models for MDC file annotations.

This module defines the data models for handling annotations in MDC files.
Annotations are special blocks in MDC files that provide metadata and structured
information using the @annotation syntax.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field, field_validator


class AnnotationContent(BaseModel):
    """Base model for annotation content.

    This model serves as the base for all annotation content types.
    Each specific annotation type should inherit from this and add its
    specific fields.

    Attributes:
        type: The type of annotation (e.g., "context", "implementation")
        description: Optional description of the annotation's purpose
    """

    type: str = Field(..., description="Type of the annotation")
    description: str | None = Field(
        None, description="Description of the annotation's purpose"
    )


class ContextAnnotation(AnnotationContent):
    """Model for @context annotations.

    Context annotations provide background information and setup requirements
    for the code or documentation.

    Attributes:
        type: Must be "context"
        language: Programming language being used
        python_version: Required Python version
        dependencies: List of required dependencies
        environment: Environment variables or configuration needed
    """

    type: str = Field("context", const=True)
    language: str = Field(..., description="Programming language")
    python_version: str = Field(..., description="Required Python version")
    dependencies: list[str] = Field(
        default_factory=list, description="Required dependencies"
    )
    environment: dict[str, str] = Field(
        default_factory=dict, description="Required environment variables"
    )


class ImplementationAnnotation(AnnotationContent):
    """Model for @implementation annotations.

    Implementation annotations provide details about how code should be
    implemented, including patterns, practices, and requirements.

    Attributes:
        type: Must be "implementation"
        patterns: Design patterns to use
        practices: Coding practices to follow
        requirements: Specific implementation requirements
        constraints: Implementation constraints or limitations
    """

    type: str = Field("implementation", const=True)
    patterns: list[str] = Field(
        default_factory=list, description="Design patterns to use"
    )
    practices: list[str] = Field(
        default_factory=list, description="Coding practices to follow"
    )
    requirements: list[str] = Field(
        default_factory=list, description="Implementation requirements"
    )
    constraints: list[str] = Field(
        default_factory=list, description="Implementation constraints"
    )


class ValidationAnnotation(AnnotationContent):
    """Model for @validation annotations.

    Validation annotations specify validation rules and requirements
    for code or documentation.

    Attributes:
        type: Must be "validation"
        rules: List of validation rules to apply
        severity_levels: Map of rule IDs to severity levels
        custom_validators: Custom validation functions to apply
    """

    type: str = Field("validation", const=True)
    rules: list[str] = Field(
        default_factory=list, description="Validation rules to apply"
    )
    severity_levels: dict[str, str] = Field(
        default_factory=dict, description="Rule severity levels"
    )
    custom_validators: list[str] = Field(
        default_factory=list, description="Custom validation functions"
    )


class ExamplesAnnotation(AnnotationContent):
    """Model for @examples annotations.

    Examples annotations provide code examples and usage demonstrations.

    Attributes:
        type: Must be "examples"
        code_samples: List of code examples
        usage_patterns: Common usage patterns
        test_cases: Example test cases
    """

    type: str = Field("examples", const=True)
    code_samples: list[str] = Field(default_factory=list, description="Code examples")
    usage_patterns: list[str] = Field(
        default_factory=list, description="Common usage patterns"
    )
    test_cases: list[str] = Field(
        default_factory=list, description="Example test cases"
    )


class ThinkingAnnotation(AnnotationContent):
    """Model for @thinking annotations.

    Thinking annotations capture thought processes, decisions,
    and rationale behind code or documentation.

    Attributes:
        type: Must be "thinking"
        decisions: Key decisions made
        rationale: Reasoning behind decisions
        alternatives: Alternative approaches considered
        trade_offs: Trade-offs considered
    """

    type: str = Field("thinking", const=True)
    decisions: list[str] = Field(default_factory=list, description="Key decisions made")
    rationale: list[str] = Field(
        default_factory=list, description="Reasoning behind decisions"
    )
    alternatives: list[str] = Field(
        default_factory=list, description="Alternative approaches considered"
    )
    trade_offs: list[str] = Field(
        default_factory=list, description="Trade-offs considered"
    )


class QuotesAnnotation(AnnotationContent):
    """Model for @quotes annotations.

    Quotes annotations store relevant quotes from documentation,
    discussions, or other sources.

    Attributes:
        type: Must be "quotes"
        quotes: List of quotes
        sources: Sources of the quotes
        relevance: Why each quote is relevant
    """

    type: str = Field("quotes", const=True)
    quotes: list[str] = Field(default_factory=list, description="Relevant quotes")
    sources: list[str] = Field(default_factory=list, description="Quote sources")
    relevance: list[str] = Field(
        default_factory=list, description="Relevance of each quote"
    )


class FormatAnnotation(AnnotationContent):
    """Model for @format annotations.

    Format annotations specify formatting requirements and styles.

    Attributes:
        type: Must be "format"
        style_guide: Style guide to follow
        indentation: Indentation requirements
        line_length: Maximum line length
        naming_conventions: Naming conventions to follow
    """

    type: str = Field("format", const=True)
    style_guide: str = Field(..., description="Style guide to follow")
    indentation: str = Field(..., description="Indentation requirements")
    line_length: int = Field(..., description="Maximum line length")
    naming_conventions: dict[str, str] = Field(
        default_factory=dict, description="Naming conventions"
    )


class OptionsAnnotation(AnnotationContent):
    """Model for @options annotations.

    Options annotations specify configuration options and settings.

    Attributes:
        type: Must be "options"
        settings: Configuration settings
        defaults: Default values
        allowed_values: Allowed values for each setting
    """

    type: str = Field("options", const=True)
    settings: dict[str, Any] = Field(
        default_factory=dict, description="Configuration settings"
    )
    defaults: dict[str, Any] = Field(default_factory=dict, description="Default values")
    allowed_values: dict[str, list[Any]] = Field(
        default_factory=dict, description="Allowed values for settings"
    )


class RulesAnnotation(AnnotationContent):
    """Model for @rules annotations.

    Rules annotations specify rules and guidelines to follow.

    Attributes:
        type: Must be "rules"
        required: Required rules that must be followed
        recommended: Recommended but not required rules
        forbidden: Practices that are not allowed
    """

    type: str = Field("rules", const=True)
    required: list[str] = Field(default_factory=list, description="Required rules")
    recommended: list[str] = Field(
        default_factory=list, description="Recommended rules"
    )
    forbidden: list[str] = Field(
        default_factory=list, description="Forbidden practices"
    )


# Map of annotation types to their model classes
ANNOTATION_TYPE_MAP: dict[str, type[AnnotationContent]] = {
    "context": ContextAnnotation,
    "implementation": ImplementationAnnotation,
    "validation": ValidationAnnotation,
    "examples": ExamplesAnnotation,
    "thinking": ThinkingAnnotation,
    "quotes": QuotesAnnotation,
    "format": FormatAnnotation,
    "options": OptionsAnnotation,
    "rules": RulesAnnotation,
}
