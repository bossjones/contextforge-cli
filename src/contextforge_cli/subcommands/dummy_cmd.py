"""Generate dspy.Signatures"""

from __future__ import annotations

import asyncio

from typer import Typer

from contextforge_cli.asynctyper import AsyncTyperImproved

APP = Typer(help="dummy command")


@APP.command("dummy")
def cli_dummy_cmd(prompt: str):
    """Generate a new dspy.Module. Example: dspygen sig new 'text -> summary'"""
    return f"dummy cmd: {prompt}"


@APP.command()
async def aio_cli_dummy_cmd() -> str:
    """Returns information about the bot."""
    await asyncio.sleep(1)
    return "slept for 1 second"


if __name__ == "__main__":
    APP()
