from __future__ import annotations

import asyncio
from typing import Any

import typer
from rich import print as rprint

APP = typer.Typer()


async def async_operation() -> str:
    """Perform an async operation.

    This is a sample async operation that simulates some work.

    Returns:
        str: Result of the operation
    """
    await asyncio.sleep(0.1)  # Simulate some async work
    return "success"


@APP.command()
async def async_command() -> None:
    """Execute an async command.

    This command demonstrates async/await functionality.
    """
    rprint("[green]Starting async operation...[/green]")
    result = await async_operation()
    rprint(f"[green]Async operation completed with result: {result}[/green]")
