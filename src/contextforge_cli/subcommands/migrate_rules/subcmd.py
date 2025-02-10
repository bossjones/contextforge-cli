"""CLI module for MDC validation commands.

This module provides the CLI interface for validating MDC files using
the implemented validators.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Set

import typer
from pydantic import BaseModel, Field
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from contextforge_cli.subcommands.migrate_rules.models.context import MDCContext
from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationResult,
    ValidationSeverity,
)
from contextforge_cli.subcommands.migrate_rules.validators.annotations import (
    AnnotationsConfig,
    AnnotationsValidator,
)
from contextforge_cli.subcommands.migrate_rules.validators.base import BaseValidator
from contextforge_cli.subcommands.migrate_rules.validators.content import (
    ContentConfig,
    ContentValidator,
)
from contextforge_cli.subcommands.migrate_rules.validators.cross_refs import (
    CrossRefConfig,
    CrossRefValidator,
)
from contextforge_cli.subcommands.migrate_rules.validators.frontmatter import (
    FrontmatterConfig,
    FrontmatterValidator,
)
from contextforge_cli.subcommands.migrate_rules.validators.xml_tags import (
    XMLTagConfig,
    XMLTagValidator,
)

if TYPE_CHECKING:
    from rich.progress import TaskID


class ValidationCliConfig(BaseModel):
    """Configuration for the validation CLI.

    Attributes:
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude
        validators: List of validators to run
        parallel: Whether to run validation in parallel
        fail_on_warnings: Whether to treat warnings as errors
        report_format: Format for validation report
        base_path: Base path for resolving references
    """

    include_patterns: set[str] = Field(default_factory=lambda: {"**/*.md", "**/*.mdc"})
    exclude_patterns: set[str] = Field(default_factory=lambda: {"**/node_modules/**"})
    validators: list[str] = Field(
        default_factory=lambda: [
            "frontmatter",
            "annotations",
            "content",
            "xml_tags",
            "cross_refs",
        ]
    )
    parallel: bool = Field(default=True)
    fail_on_warnings: bool = Field(default=False)
    report_format: str = Field(default="rich")
    base_path: Path | None = None


class ValidationCli:
    """CLI handler for MDC validation commands."""

    def __init__(self, config: ValidationCliConfig | None = None) -> None:
        """Initialize the ValidationCli.

        Args:
            config: Configuration for the validation CLI. If None, default config is used.
        """
        self.config = config or ValidationCliConfig()
        self.console = Console()
        self._validators: list[BaseValidator] = []
        self._initialize_validators()

    def _initialize_validators(self) -> None:
        """Initialize the configured validators."""
        validator_map = {
            "frontmatter": lambda: FrontmatterValidator(),
            "annotations": lambda: AnnotationsValidator(),
            "content": lambda: ContentValidator(),
            "xml_tags": lambda: XMLTagValidator(),
            "cross_refs": lambda: CrossRefValidator(
                config=CrossRefConfig(base_path=self.config.base_path)
            ),
        }

        for validator_name in self.config.validators:
            if validator_name in validator_map:
                self._validators.append(validator_map[validator_name]())

    async def _validate_file(
        self,
        file_path: Path,
        progress: Progress,
        task_id: TaskID,
    ) -> list[ValidationResult]:
        """Validate a single file.

        Args:
            file_path: Path to the file to validate
            progress: Progress bar instance
            task_id: ID of the current task

        Returns:
            List of ValidationResult objects
        """
        try:
            content = await asyncio.to_thread(file_path.read_text)
            context = MDCContext(
                content=content,
                file_path=str(file_path),
            )

            results: list[ValidationResult] = []
            for validator in self._validators:
                validator_results = await validator.validate(context)
                results.extend(validator_results)

            progress.update(task_id, advance=1)
            return results

        except Exception as e:
            return [
                ValidationResult(
                    message=f"Failed to validate file: {str(e)}",
                    line_number=0,
                    severity=ValidationSeverity.ERROR,
                    context=None,
                )
            ]

    async def validate_files(self, files: list[Path]) -> list[ValidationResult]:
        """Validate multiple files.

        Args:
            files: List of file paths to validate

        Returns:
            List of ValidationResult objects
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task_id = progress.add_task(
                description="Validating files...",
                total=len(files),
            )

            if self.config.parallel:
                # Run validation in parallel
                tasks = [
                    self._validate_file(file_path, progress, task_id)
                    for file_path in files
                ]
                results = await asyncio.gather(*tasks)
                return [result for sublist in results for result in sublist]
            else:
                # Run validation sequentially
                results: list[ValidationResult] = []
                for file_path in files:
                    file_results = await self._validate_file(
                        file_path, progress, task_id
                    )
                    results.extend(file_results)
                return results

    def _print_results(self, results: list[ValidationResult]) -> None:
        """Print validation results in the configured format.

        Args:
            results: List of ValidationResult objects to print
        """
        if not results:
            self.console.print("\n✅ No validation issues found!", style="green")
            return

        table = Table(title="\nValidation Results")
        table.add_column("File", style="cyan")
        table.add_column("Line", style="magenta")
        table.add_column("Severity", style="yellow")
        table.add_column("Message", style="white")
        table.add_column("Validator", style="blue")

        for result in sorted(
            results,
            key=lambda x: (
                x.context.file_path if x.context else "",
                x.line_number,
                x.severity.value,
            ),
        ):
            severity_style = (
                "red" if result.severity == ValidationSeverity.ERROR else "yellow"
            )
            table.add_row(
                result.context.file_path if result.context else "N/A",
                str(result.line_number),
                result.severity.value,
                result.message,
                result.context.validator_name if result.context else "N/A",
                style=severity_style
                if result.severity == ValidationSeverity.ERROR
                else None,
            )

        self.console.print(table)

        # Print summary
        error_count = sum(1 for r in results if r.severity == ValidationSeverity.ERROR)
        warning_count = sum(
            1 for r in results if r.severity == ValidationSeverity.WARNING
        )

        self.console.print(f"\nFound {error_count} errors and {warning_count} warnings")

    def should_fail(self, results: list[ValidationResult]) -> bool:
        """Determine if validation should be considered failed.

        Args:
            results: List of ValidationResult objects

        Returns:
            bool: True if validation should fail, False otherwise
        """
        has_errors = any(r.severity == ValidationSeverity.ERROR for r in results)
        has_warnings = any(r.severity == ValidationSeverity.WARNING for r in results)

        return has_errors or (self.config.fail_on_warnings and has_warnings)


app = typer.Typer()


def path_callback(paths: list[str] | None) -> list[Path] | None:
    if not paths:
        return None
    return [Path(p) if isinstance(p, str) else p for p in paths]


@app.command()
def validate(
    paths: list[Path] = typer.Argument(
        None,
        help="Paths to files or directories to validate",
        exists=True,
        callback=path_callback,
    ),
    include: list[str] = typer.Option(
        None,
        "--include",
        "-i",
        help="Glob patterns for files to include",
    ),
    exclude: list[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Glob patterns for files to exclude",
    ),
    validators: list[str] = typer.Option(
        None,
        "--validator",
        "-v",
        help="Validators to run",
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--no-parallel",
        help="Run validation in parallel",
    ),
    fail_on_warnings: bool = typer.Option(
        False,
        "--fail-on-warnings",
        help="Treat warnings as errors",
    ),
    report_format: str = typer.Option(
        "rich",
        "--format",
        "-f",
        help="Format for validation report",
    ),
) -> None:
    """Validate MDC files for compliance with rules and standards."""
    # Create configuration
    config = ValidationCliConfig(
        include_patterns=set(include) if include else None,
        exclude_patterns=set(exclude) if exclude else None,
        validators=validators if validators else None,
        parallel=parallel,
        fail_on_warnings=fail_on_warnings,
        report_format=report_format,
        base_path=paths[0].parent if paths else None,
    )

    # Initialize CLI handler
    cli = ValidationCli(config=config)

    # Collect files to validate
    files_to_validate: list[Path] = []
    for path in paths or ["."]:
        if path.is_file():
            files_to_validate.append(path)
        else:
            for pattern in config.include_patterns:
                files_to_validate.extend(
                    f
                    for f in path.glob(pattern)
                    if not any(f.match(ep) for ep in config.exclude_patterns)
                )

    if not files_to_validate:
        cli.console.print("No files found to validate!", style="yellow")
        raise typer.Exit(code=0)

    # Run validation
    results = asyncio.run(cli.validate_files(files_to_validate))

    # Print results
    cli.console.print(f"\nValidated {len(files_to_validate)} files:")
    cli._print_results(results)

    # Exit with appropriate code
    if cli.should_fail(results):
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
