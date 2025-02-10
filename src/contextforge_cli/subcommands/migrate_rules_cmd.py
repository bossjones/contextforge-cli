"""Command module for MDC validation and migration rules.

This module provides the CLI interface for validating and managing MDC files
using the implemented validators. It serves as the main entry point for the
migrate-rules subcommand, delegating actual validation work to the subcmd module.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, List, Optional, cast

import typer
from rich.console import Console

from contextforge_cli.subcommands.migrate_rules.subcmd import (
    ValidationCli,
    ValidationCliConfig,
)

if TYPE_CHECKING:
    from collections.abc import Callable

# Create Typer app for migrate-rules subcommand
APP = typer.Typer(
    name="migrate-rules",
    help="Validate and manage MDC (Markdown Configuration) files",
    no_args_is_help=True,
)

console = Console()


def path_callback(path: str | list[str] | None) -> Path | list[Path] | None:
    """Convert string path(s) to Path object(s) and validate existence.

    Args:
        path: String path or list of paths to convert

    Returns:
        Path object or list of Path objects representing the input path(s)

    Raises:
        typer.BadParameter: If path doesn't exist
    """
    if path is None:
        return None

    if isinstance(path, list):
        return [Path(p) if isinstance(p, str) else p for p in path]

    p = Path(path)
    if not p.exists():
        raise typer.BadParameter(f"Path does not exist: {path}")
    return p


PathArgument = Annotated[
    Path,
    typer.Argument(
        callback=path_callback,
        help="Path to file or directory to validate",
        exists=True,
    ),
]


def collect_files_to_validate(
    paths: list[Path] | None,
    include_patterns: set[str],
    exclude_patterns: set[str],
) -> list[Path]:
    """Collect files to validate based on paths and patterns.

    Args:
        paths: List of paths to validate
        include_patterns: Glob patterns for files to include
        exclude_patterns: Glob patterns for files to exclude

    Returns:
        List of Path objects to validate
    """
    files_to_validate: list[Path] = []
    default_paths = [Path(".")] if not paths else paths

    for path in default_paths:
        if path.is_file():
            files_to_validate.append(path)
        else:
            for pattern in include_patterns:
                files_to_validate.extend(
                    f
                    for f in path.glob(pattern)
                    if not any(f.match(ep) for ep in exclude_patterns)
                )

    return files_to_validate


@APP.command()
def validate(
    paths: list[PathArgument] = None,
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
        help="Validators to run (frontmatter, annotations, content, xml_tags, cross_refs)",
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
        help="Format for validation report (rich)",
    ),
) -> None:
    """Validate MDC files for compliance with rules and standards.

    This command validates MDC (Markdown Configuration) files against a set of rules
    and standards. It can validate multiple aspects including frontmatter, annotations,
    content structure, XML tags, and cross-references.

    Args:
        paths: List of paths to files or directories to validate
        include: Glob patterns for files to include
        exclude: Glob patterns for files to exclude
        validators: List of validators to run
        parallel: Whether to run validation in parallel
        fail_on_warnings: Whether to treat warnings as errors
        report_format: Format for validation report

    Examples:
        # Validate a single file
        $ contextforgectl migrate-rules validate path/to/file.mdc

        # Validate multiple files
        $ contextforgectl migrate-rules validate file1.mdc file2.mdc

        # Validate a directory recursively
        $ contextforgectl migrate-rules validate ./docs

        # Validate with specific validators
        $ contextforgectl migrate-rules validate --validator frontmatter --validator content ./docs

        # Validate with custom patterns
        $ contextforgectl migrate-rules validate --include "*.md" --include "*.mdc" --exclude "**/temp/*" ./docs

        # Validate with strict warnings
        $ contextforgectl migrate-rules validate --fail-on-warnings ./docs
    """
    try:
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
        files_to_validate = collect_files_to_validate(
            paths,
            config.include_patterns,
            config.exclude_patterns,
        )

        if not files_to_validate:
            console.print("No files found to validate!", style="yellow")
            raise typer.Exit(code=0)

        # Run validation
        results = asyncio.run(cli.validate_files(files_to_validate))

        # Print results
        console.print(f"\nValidated {len(files_to_validate)} files:")
        cli._print_results(results)

        # Exit with appropriate code
        if cli.should_fail(results):
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)


@APP.command()
def list_validators() -> None:
    """List available validators and their configurations.

    This command displays information about all available validators
    and their configuration options.

    Examples:
        $ contextforgectl migrate-rules list-validators
    """
    console.print("\n[bold]Available Validators:[/bold]")

    validators = [
        {
            "name": "frontmatter",
            "description": "Validates YAML frontmatter in MDC files",
            "checks": [
                "YAML syntax",
                "Schema validation",
                "Position validation",
                "Reference validation",
            ],
        },
        {
            "name": "annotations",
            "description": "Validates annotations in MDC files",
            "checks": [
                "JSON syntax",
                "Type validation",
                "Required annotations",
                "Content structure",
            ],
        },
        {
            "name": "content",
            "description": "Validates content structure in MDC files",
            "checks": [
                "Heading hierarchy",
                "Code block validation",
                "Section organization",
                "Formatting rules",
            ],
        },
        {
            "name": "xml_tags",
            "description": "Validates XML tags in MDC files",
            "checks": [
                "Tag structure",
                "Nesting validation",
                "Required tags",
                "Attribute validation",
            ],
        },
        {
            "name": "cross_refs",
            "description": "Validates cross-references in MDC files",
            "checks": [
                "Internal references",
                "External URLs",
                "Anchor validation",
                "File existence",
                "Path validation",
            ],
        },
    ]

    for validator in validators:
        console.print(f"\n[cyan]{validator['name']}[/cyan]")
        console.print(f"  Description: {validator['description']}")
        console.print("  Checks:")
        for check in validator["checks"]:
            console.print(f"    • {check}")

    console.print("\n[bold]Usage Example:[/bold]")
    console.print(
        "  contextforgectl migrate-rules validate --validator frontmatter --validator content ./docs"
    )


if __name__ == "__main__":
    APP()
