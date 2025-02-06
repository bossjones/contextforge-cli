"""AI documentation generation commands"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Annotated

import structlog
import typer
from rich import print as rprint
from typer import Typer

from contextforge_cli.asynctyper import AsyncTyperImproved
from contextforge_cli.utils.ai_docs_utils.extract_repo import extract_local_directory
from contextforge_cli.utils.ai_docs_utils.generate_docs import (
    agenerate_docs_from_local_repo,
    agenerate_module_docs,
    generate_module_docs,
)

logger = structlog.get_logger(__name__)

APP = Typer(help="ai docs command")


@APP.command("generate")
def cli_generate_docs(
    directory_path: Annotated[
        str, typer.Argument(help="Path to local repository directory")
    ],
) -> None:
    """Generate documentation for a local repository.

    Args:
        directory_path: Path to the local repository directory
    """
    path = Path(directory_path)
    if not path.exists():
        rprint(f"[red]Directory does not exist: {directory_path}[/red]")
        raise typer.Exit(1)
    if not path.is_dir():
        rprint(f"[red]Not a directory: {directory_path}[/red]")
        raise typer.Exit(1)

    try:
        # Run in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(agenerate_docs_from_local_repo(str(path)))
        loop.close()

        rprint(f"[green]Documentation generated for {directory_path}[/green]")
    except Exception as ex:
        logger.error("Error generating documentation", error=str(ex))
        rprint(f"[red]Error: {ex!s}[/red]")
        raise typer.Exit(1)


@APP.command("extract")
def cli_extract_repo(
    directory_path: Annotated[
        str, typer.Argument(help="Path to local repository directory")
    ],
) -> None:
    """Extract repository contents to a text file.

    Args:
        directory_path: Path to the local repository directory
    """
    path = Path(directory_path)
    if not path.exists():
        rprint(f"[red]Directory does not exist: {directory_path}[/red]")
        raise typer.Exit(1)
    if not path.is_dir():
        rprint(f"[red]Not a directory: {directory_path}[/red]")
        raise typer.Exit(1)

    try:
        output_file = extract_local_directory(str(path))
        rprint(f"[green]Repository extracted to {output_file}[/green]")
    except Exception as ex:
        logger.error("Error extracting repository", error=str(ex))
        rprint(f"[red]Error: {ex!s}[/red]")
        raise typer.Exit(1)


@APP.command("generate-async")
async def aio_cli_generate_docs(
    directory_path: Annotated[
        str, typer.Argument(help="Path to local repository directory")
    ],
) -> None:
    """Generate documentation for a local repository asynchronously.

    Args:
        directory_path: Path to the local repository directory
    """
    path = Path(directory_path)
    if not path.exists():
        rprint(f"[red]Directory does not exist: {directory_path}[/red]")
        raise typer.Exit(1)
    if not path.is_dir():
        rprint(f"[red]Not a directory: {directory_path}[/red]")
        raise typer.Exit(1)

    try:
        await agenerate_docs_from_local_repo(str(path))
        rprint(f"[green]Documentation generated for {directory_path}[/green]")
    except Exception as ex:
        logger.error("Error generating documentation", error=str(ex))
        rprint(f"[red]Error: {ex!s}[/red]")
        raise typer.Exit(1)


@APP.command("extract-async")
async def aio_cli_extract_repo(
    directory_path: Annotated[
        str, typer.Argument(help="Path to local repository directory")
    ],
) -> None:
    """Extract repository contents to a text file asynchronously.

    Args:
        directory_path: Path to the local repository directory
    """
    path = Path(directory_path)
    if not path.exists():
        rprint(f"[red]Directory does not exist: {directory_path}[/red]")
        raise typer.Exit(1)
    if not path.is_dir():
        rprint(f"[red]Not a directory: {directory_path}[/red]")
        raise typer.Exit(1)

    try:
        output_file = extract_local_directory(str(path))  # This function isn't async
        rprint(f"[green]Repository extracted to {output_file}[/green]")
    except Exception as ex:
        logger.error("Error extracting repository", error=str(ex))
        rprint(f"[red]Error: {ex!s}[/red]")
        raise typer.Exit(1)


@APP.command("generate-module")
def cli_generate_module_docs(
    module_path: Annotated[
        str, typer.Argument(help="Path to Python module file or directory")
    ],
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-r",
            help="Recursively process all Python files in directory",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Skip confirmation for recursive generation"
        ),
    ] = False,
) -> None:
    """Generate detailed documentation for Python modules including test examples.

    Args:
        module_path: Path to the Python module file or directory
        recursive: If True and module_path is a directory, recursively process all Python files
        force: If True, skip confirmation when processing multiple files recursively

    The command will:
    1. For single files: Generate documentation directly
    2. For directories with --recursive:
       - List all Python files found
       - Prompt for confirmation (unless --force is used)
       - Generate documentation for each confirmed file
    """
    path = Path(module_path)
    if not path.exists():
        rprint(f"[red]Path does not exist: {module_path}[/red]")
        raise typer.Exit(1)

    try:
        if path.is_file():
            if path.suffix != ".py":
                rprint(
                    f"[red]Path must be a Python file or directory: {module_path}[/red]"
                )
                raise typer.Exit(1)
            generate_module_docs(str(path))
            rprint(f"[green]Module documentation generated for {module_path}[/green]")
        elif path.is_dir():
            # Get all Python files in directory
            python_files = list(path.rglob("*.py") if recursive else path.glob("*.py"))

            if not python_files:
                rprint(f"[yellow]No Python files found in: {module_path}[/yellow]")
                raise typer.Exit(1)

            # Print found files
            rprint("\n[bold]Found Python files:[/bold]")
            for i, file in enumerate(python_files, 1):
                rprint(f"{i}. {file}")

            # Process files
            if force:
                rprint(
                    "\n[yellow]Forcing documentation generation for all files...[/yellow]"
                )
            else:
                confirm = typer.confirm("\nGenerate documentation for these files?")
                if not confirm:
                    rprint("[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(0)

            # Generate docs for each file
            for file in python_files:
                try:
                    rprint(f"\nProcessing: {file}")
                    generate_module_docs(str(file))
                    rprint(f"[green]✓ Documentation generated for {file}[/green]")
                except Exception as ex:
                    logger.error(
                        "Error generating documentation for file",
                        file=str(file),
                        error=str(ex),
                    )
                    rprint(f"[red]Error processing {file}: {ex}[/red]")
                    if not force:
                        continue_on_error = typer.confirm(
                            "Continue with remaining files?"
                        )
                        if not continue_on_error:
                            raise typer.Exit(1)

            rprint("\n[green]Documentation generation complete![/green]")
        else:
            rprint(f"[red]Path must be a Python file or directory: {module_path}[/red]")
            raise typer.Exit(1)

    except Exception as ex:
        logger.error("Error generating module documentation", error=str(ex))
        rprint(f"[red]Error: {ex!s}[/red]")
        raise typer.Exit(1)


@APP.command("generate-module-async")
async def aio_cli_generate_module_docs(
    module_path: Annotated[
        str, typer.Argument(help="Path to Python module file or directory")
    ],
    recursive: Annotated[
        bool,
        typer.Option(
            "--recursive",
            "-r",
            help="Recursively process all Python files in directory",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force", "-f", help="Skip confirmation for recursive generation"
        ),
    ] = False,
) -> None:
    """Generate detailed documentation for Python modules including test examples asynchronously.

    Args:
        module_path: Path to the Python module file or directory
        recursive: If True and module_path is a directory, recursively process all Python files
        force: If True, skip confirmation when processing multiple files recursively

    The command will:
    1. For single files: Generate documentation directly
    2. For directories with --recursive:
       - List all Python files found
       - Prompt for confirmation (unless --force is used)
       - Generate documentation for each confirmed file
    """
    path = Path(module_path)
    if not path.exists():
        rprint(f"[red]Path does not exist: {module_path}[/red]")
        raise typer.Exit(1)

    try:
        if path.is_file():
            if path.suffix != ".py":
                rprint(
                    f"[red]Path must be a Python file or directory: {module_path}[/red]"
                )
                raise typer.Exit(1)
            await agenerate_module_docs(str(path))
            rprint(f"[green]Module documentation generated for {module_path}[/green]")
        elif path.is_dir():
            # Get all Python files in directory
            python_files = list(path.rglob("*.py") if recursive else path.glob("*.py"))

            if not python_files:
                rprint(f"[yellow]No Python files found in: {module_path}[/yellow]")
                raise typer.Exit(1)

            # Print found files
            rprint("\n[bold]Found Python files:[/bold]")
            for i, file in enumerate(python_files, 1):
                rprint(f"{i}. {file}")

            # Process files
            if force:
                rprint(
                    "\n[yellow]Forcing documentation generation for all files...[/yellow]"
                )
            else:
                confirm = typer.confirm("\nGenerate documentation for these files?")
                if not confirm:
                    rprint("[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(0)

            # Generate docs for each file
            for file in python_files:
                try:
                    rprint(f"\nProcessing: {file}")
                    await agenerate_module_docs(str(file))
                    rprint(f"[green]✓ Documentation generated for {file}[/green]")
                except Exception as ex:
                    logger.error(
                        "Error generating documentation for file",
                        file=str(file),
                        error=str(ex),
                    )
                    rprint(f"[red]Error processing {file}: {ex}[/red]")
                    if not force:
                        continue_on_error = typer.confirm(
                            "Continue with remaining files?"
                        )
                        if not continue_on_error:
                            raise typer.Exit(1)
                        continue
                    continue

            rprint("\n[green]Documentation generation complete![/green]")
        else:
            rprint(f"[red]Path must be a Python file or directory: {module_path}[/red]")
            raise typer.Exit(1)

    except Exception as ex:
        logger.error("Error generating module documentation", error=str(ex))
        rprint(f"[red]Error: {ex!s}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    APP()
