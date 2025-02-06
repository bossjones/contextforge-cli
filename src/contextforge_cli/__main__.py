#!/usr/bin/env python
"""contextforge_cli.main."""

from __future__ import annotations

import logging

from contextforge_cli.cli import main


rootlogger = logging.getLogger()
handler_logger = logging.getLogger("handler")

name_logger = logging.getLogger(__name__)
logging.getLogger("asyncio").setLevel(logging.DEBUG)  # type: ignore


main()
