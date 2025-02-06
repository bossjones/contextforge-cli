# pyright: reportMissingTypeStubs=false
# pylint: disable=no-member
# pylint: disable=no-value-for-parameter
# pyright: reportAttributeAccessIssue=false
# pyright: reportImportCycles=false

"""contextforge_cli: A Python package for gooby things."""

from __future__ import annotations


from contextforge_cli.__version__ import __version__ as __version__


def main() -> None:
    print("Hello from contextforge-cli!")
