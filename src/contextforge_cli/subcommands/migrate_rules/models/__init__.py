"""Models for MDC file validation.

This package provides the data models used throughout the MDC file
validation system, including context, validation results, and specific
validation models for different aspects of MDC files.
"""

from contextforge_cli.subcommands.migrate_rules.models.annotations import (
    AnnotationContent,
    ContextAnnotation,
    ExamplesAnnotation,
    FormatAnnotation,
    ImplementationAnnotation,
    OptionsAnnotation,
    QuotesAnnotation,
    RulesAnnotation,
    ThinkingAnnotation,
    ValidationAnnotation,
)
from contextforge_cli.subcommands.migrate_rules.models.context import MDCContext
from contextforge_cli.subcommands.migrate_rules.models.frontmatter import (
    FrontmatterConfig,
    FrontmatterMetadata,
    FrontmatterValidationResult,
)
from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationLocation,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
)

__all__ = [
    # Annotation models
    "AnnotationContent",
    "ContextAnnotation",
    "ExamplesAnnotation",
    "FormatAnnotation",
    "ImplementationAnnotation",
    "OptionsAnnotation",
    "QuotesAnnotation",
    "RulesAnnotation",
    "ThinkingAnnotation",
    "ValidationAnnotation",
    # Context models
    "MDCContext",
    # Frontmatter models
    "FrontmatterConfig",
    "FrontmatterMetadata",
    "FrontmatterValidationResult",
    # Validation models
    "ValidationLocation",
    "ValidationResult",
    "ValidationSeverity",
    "ValidationSummary",
]
