"""Entry point for the contextforge-cli."""

from __future__ import annotations

import asyncio

import structlog

logger = structlog.get_logger(__name__)


async def main():
    logger.info("Starting contextforge-cli")


if __name__ == "__main__":
    asyncio.run(main())
