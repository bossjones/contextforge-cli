"""contextforge_cli.models.loggers"""
# pylint: disable=no-member
# pylint: disable=no-name-in-module
# pylint: disable=no-value-for-parameter
# pylint: disable=possibly-used-before-assignment
# pyright: reportAttributeAccessIssue=false
# pyright: reportInvalidTypeForm=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUndefinedVariable=false
# pyright: reportAssignmentType=false
# pyright: strictParameterNoneValue=false
# pylint: disable=no-name-in-module

# SOURCE: https://blog.bartab.fr/fastapi-logging-on-the-fly/
from __future__ import annotations

from typing import Any, ForwardRef, List, Optional

from pydantic import BaseModel, Field

LoggerModel = ForwardRef("LoggerModel")


class LoggerPatch(BaseModel):
    name: str
    level: str


class LoggerModel(BaseModel):  # noqa: F811
    name: str
    level: int | None
    # children: Optional[List["LoggerModel"]] = None
    # fixes: https://github.com/samuelcolvin/pydantic/issues/545
    children: list[Any] | None = None
    # children: ListLoggerModel = None


LoggerModel.model_rebuild()
