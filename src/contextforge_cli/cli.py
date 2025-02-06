# pylint: disable=no-member
# pylint: disable=no-name-in-module
# pylint: disable=no-value-for-parameter
# pylint: disable=possibly-used-before-assignment
# pyright: reportAttributeAccessIssue=false
# pyright: reportInvalidTypeForm=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUndefinedVariable=false
# SOURCE: https://github.com/tiangolo/typer/issues/88#issuecomment-1732469681

"""contextforge_cli.cli
Usage:
    Run commands using the CLI:
    $ contextforgectl [command] [options]

    Example:
    $ contextforgectl run-bot
    $ contextforgectl version --verbose
"""

from __future__ import annotations

import os
import signal
import sys
from importlib import import_module
from importlib.metadata import version as importlib_metadata_version
from pathlib import Path
from typing import Annotated

import asyncer
import rich
import structlog
import typer
from langchain.globals import set_debug, set_verbose
from rich.console import Console
from typer import Typer

import contextforge_cli
from contextforge_cli.aio_settings import aiosettings
from contextforge_cli.asynctyper import AsyncTyperImproved

logger = structlog.get_logger(__name__)


# from contextforge_cli.utils.collections_io import export_collection_data, import_collection_data
# SOURCE: https://python.langchain.com/v0.2/docs/how_to/debugging/
if aiosettings.debug_langchain:
    # Setting the global debug flag will cause all LangChain components with callback support (chains, models, agents, tools, retrievers) to print the inputs they receive and outputs they generate. This is the most verbose setting and will fully log raw inputs and outputs.
    set_debug(True)
    # Setting the verbose flag will print out inputs and outputs in a slightly more readable format and will skip logging certain raw outputs (like the token usage stats for an LLM call) so that you can focus on application logic.
    set_verbose(True)


# Load existing subcommands
def load_commands(directory: str = "subcommands") -> None:
    """
    Load subcommands from the specified directory.

    This function loads subcommands from the specified directory and adds them to the main Typer app.
    It iterates over the files in the directory, imports the modules that end with "_cmd.py", and adds
    their Typer app to the main app if they have one.

    Args:
        directory (str, optional): The directory to load subcommands from. Defaults to "subcommands".

    Returns:
        None
    """
    script_dir = Path(__file__).parent
    subcommands_dir = script_dir / directory

    logger.debug(f"Loading subcommands from {subcommands_dir}")

    for filename in os.listdir(subcommands_dir):
        logger.debug(f"Filename: {filename}")
        if filename.endswith("_cmd.py"):
            module_name = f"{__name__.split('.')[0]}.{directory}.{filename[:-3]}"
            logger.debug(f"Loading subcommand: {module_name}")
            module = import_module(module_name)
            if hasattr(module, "APP"):
                logger.debug(f"Adding subcommand: {filename[:-7]}")
                APP.add_typer(module.APP, name=filename[:-7])


async def aload_commands(directory: str = "subcommands") -> None:
    """
    Asynchronously load subcommands from the specified directory.

    This function asynchronously loads subcommands from the specified directory and adds them to the main Typer app.
    It iterates over the files in the directory, imports the modules that end with "_cmd.py", and adds
    their Typer app to the main app if they have one.

    Args:
        directory (str, optional): The directory to load subcommands from. Defaults to "subcommands".

    Returns:
        None
    """
    script_dir = Path(__file__).parent
    subcommands_dir = script_dir / directory

    logger.debug(f"Loading subcommands from {subcommands_dir}")

    async with asyncer.create_task_group() as tg:
        for filename in os.listdir(subcommands_dir):
            logger.debug(f"Filename: {filename}")
            if filename.endswith("_cmd.py"):
                module_name = f"{__name__.split('.')[0]}.{directory}.{filename[:-3]}"
                logger.debug(f"Loading subcommand: {module_name}")

                async def _load_module(module_name: str, cmd_name: str) -> None:
                    module = import_module(module_name)
                    if hasattr(module, "APP"):
                        logger.debug(f"Adding subcommand: {cmd_name}")
                        APP.add_typer(module.APP, name=cmd_name)

                tg.start_soon(_load_module, module_name, filename[:-7])


# APP = AsyncTyperImproved()
APP = Typer()
console = Console()
cprint = console.print
load_commands()


def version_callback(version: bool) -> None:
    """Print the version of contextforge_cli."""
    if version:
        rich.print(f"contextforge_cli version: {contextforge_cli.__version__}")
        raise typer.Exit()


@APP.command()
def version(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Show detailed version info")
    ] = False,
) -> None:
    """Display version information."""
    rich.print(f"contextforge_cli version: {contextforge_cli.__version__}")
    if verbose:
        rich.print(f"Python version: {sys.version}")


@APP.command()
def deps() -> None:
    """Deps command"""
    rich.print(f"contextforge_cli version: {contextforge_cli.__version__}")
    rich.print(f"langchain_version: {importlib_metadata_version('langchain')}")
    rich.print(
        f"langchain_community_version: {importlib_metadata_version('langchain_community')}"
    )
    rich.print(
        f"langchain_core_version: {importlib_metadata_version('langchain_core')}"
    )
    rich.print(
        f"langchain_openai_version: {importlib_metadata_version('langchain_openai')}"
    )
    rich.print(
        f"langchain_text_splitters_version: {importlib_metadata_version('langchain_text_splitters')}"
    )
    rich.print(
        f"langchain_chroma_version: {importlib_metadata_version('langchain_chroma')}"
    )
    rich.print(f"chromadb_version: {importlib_metadata_version('chromadb')}")
    rich.print(f"langsmith_version: {importlib_metadata_version('langsmith')}")
    rich.print(f"pydantic_version: {importlib_metadata_version('pydantic')}")
    rich.print(
        f"pydantic_settings_version: {importlib_metadata_version('pydantic_settings')}"
    )
    rich.print(f"ruff_version: {importlib_metadata_version('ruff')}")


@APP.command()
def about() -> None:
    """About command"""
    typer.echo("This is GoobBot CLI")


@APP.command()
def show() -> None:
    """Show command"""
    cprint("\nShow contextforge_cli", style="yellow")


# @pysnooper.snoop(thread_info=True, max_variable_length=None, watch=["APP"], depth=10)
def main():
    APP()
    load_commands()


# @pysnooper.snoop(thread_info=True, max_variable_length=None, depth=10)
def entry():
    """Required entry point to enable hydra to work as a console_script."""
    main()  # pylint: disable=no-value-for-parameter


@APP.command()
def run_load_commands() -> None:
    """Load subcommands"""
    typer.echo("Loading subcommands....")
    load_commands()


@APP.command()
def go() -> None:
    """Main entry point for DemocracyBot"""
    typer.echo("Starting up DemocracyBot")
    # NOTE: This is the approved way to run the bot, via asyncio.run.
    # asyncio.run(run_bot())


def handle_sigterm(signo, frame):
    sys.exit(128 + signo)  # this will raise SystemExit and cause atexit to be called


signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    APP()
