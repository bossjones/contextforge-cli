"""Base classes for MDC file validation.

This module provides the abstract base classes and core implementation
for the MDC file validation system. It defines the interface that all
validators must implement and provides common utilities.
"""

from __future__ import annotations

import abc
import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Type,
)

import structlog
from pydantic import BaseModel, Field

from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationContext,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
)

logger = structlog.get_logger(__name__)


class ValidatorConfig(BaseModel):
    """Configuration for a validator.

    Attributes:
        enabled: Whether this validator is enabled
        severity_overrides: Map of rule IDs to custom severities
        custom_rules: Additional validation rules to apply
        max_concurrent: Maximum number of concurrent validations
    """

    enabled: bool = Field(default=True, description="Whether this validator is enabled")
    severity_overrides: dict[str, ValidationSeverity] = Field(
        default_factory=dict,
        description="Map of rule IDs to custom severities",
    )
    custom_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional validation rules to apply",
    )
    max_concurrent: int = Field(
        default=10,
        ge=1,
        description="Maximum number of concurrent validations",
    )


class BaseValidator(abc.ABC):
    """Abstract base class for all validators.

    This class defines the interface that all validators must implement.
    It provides common functionality for validation and result handling.

    Attributes:
        name: Name of the validator
        description: Description of what this validator checks
        config: Validator configuration
    """

    def __init__(
        self,
        name: str,
        description: str,
        config: ValidatorConfig | None = None,
    ) -> None:
        """Initialize the validator.

        Args:
            name: Name of the validator
            description: Description of what this validator checks
            config: Optional validator configuration
        """
        self.name = name
        self.description = description
        self.config = config or ValidatorConfig()
        self._logger = logger.bind(validator=name)

    @abc.abstractmethod
    async def validate(
        self, context: ValidationContext
    ) -> AsyncGenerator[ValidationResult, None]:
        """Validate content according to specific rules.

        Args:
            context: Validation context containing file and workspace information

        Yields:
            ValidationResult for each validation check

        Raises:
            ValidationError: If validation cannot be performed
        """
        raise NotImplementedError()

    async def cleanup(self) -> None:
        """Cleanup any resources used during validation.

        This method should be called after validation is complete to
        clean up any resources that were allocated during validation.
        """
        pass

    def get_severity(self, rule_id: str) -> ValidationSeverity:
        """Get the severity level for a rule, considering overrides.

        Args:
            rule_id: The ID of the rule to get the severity for

        Returns:
            The severity level to use for the rule
        """
        return self.config.severity_overrides.get(rule_id, ValidationSeverity.ERROR)


class ValidationPipeline:
    """Orchestrates the validation process across multiple validators.

    This class manages the execution of multiple validators and aggregates
    their results into a single validation summary.

    Attributes:
        validators: List of validators to run
        parallel: Whether to run validators in parallel
        max_concurrent: Maximum number of concurrent validations
    """

    def __init__(
        self,
        validators: Sequence[BaseValidator],
        parallel: bool = True,
        max_concurrent: int = 10,
    ) -> None:
        """Initialize the validation pipeline.

        Args:
            validators: List of validators to run
            parallel: Whether to run validators in parallel
            max_concurrent: Maximum number of concurrent validations
        """
        self.validators = validators
        self.parallel = parallel
        self.max_concurrent = max_concurrent
        self._logger = logger.bind(component="ValidationPipeline")

    async def _run_validator(
        self, validator: BaseValidator, context: ValidationContext
    ) -> list[ValidationResult]:
        """Run a single validator and collect its results.

        Args:
            validator: The validator to run
            context: Validation context

        Returns:
            List of validation results from the validator
        """
        try:
            results = []
            async for result in validator.validate(context):
                results.append(result)
            return results
        except Exception as e:
            self._logger.error(
                "Validator failed",
                validator=validator.name,
                error=str(e),
                exc_info=True,
            )
            return [
                ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Validator failed: {str(e)}",
                    details={"validator": validator.name, "error": str(e)},
                )
            ]
        finally:
            await validator.cleanup()

    async def validate(self, context: ValidationContext) -> ValidationSummary:
        """Run all validators on a file.

        Args:
            context: Validation context containing file and workspace information

        Returns:
            A summary of all validation results

        Raises:
            ValidationError: If validation pipeline fails
        """
        all_results: list[ValidationResult] = []
        self._logger.info("Starting validation pipeline", file_path=context.file_path)

        try:
            if self.parallel:
                # Run validators in parallel with concurrency limit
                semaphore = asyncio.Semaphore(self.max_concurrent)
                async with semaphore:
                    tasks = [
                        self._run_validator(validator, context)
                        for validator in self.validators
                        if validator.config.enabled
                    ]
                    results = await asyncio.gather(*tasks)
                    for validator_results in results:
                        all_results.extend(validator_results)
            else:
                # Run validators sequentially
                for validator in self.validators:
                    if validator.config.enabled:
                        results = await self._run_validator(validator, context)
                        all_results.extend(results)

            # Calculate summary statistics
            error_count = sum(
                1 for r in all_results if r.severity == ValidationSeverity.ERROR
            )
            warning_count = sum(
                1 for r in all_results if r.severity == ValidationSeverity.WARNING
            )
            info_count = sum(
                1 for r in all_results if r.severity == ValidationSeverity.INFO
            )

            summary = ValidationSummary(
                file_path=context.file_path,
                is_valid=error_count == 0,
                results=all_results,
                error_count=error_count,
                warning_count=warning_count,
                info_count=info_count,
            )

            self._logger.info(
                "Validation complete",
                file_path=context.file_path,
                is_valid=summary.is_valid,
                error_count=error_count,
                warning_count=warning_count,
                info_count=info_count,
            )

            return summary

        except Exception as e:
            self._logger.error(
                "Validation pipeline failed",
                error=str(e),
                exc_info=True,
            )
            raise
