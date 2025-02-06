# #!/usr/bin/env python3
# # pylint: disable=no-member
# # pylint: disable=consider-using-tuple
# # pyright: ignore[reportOperatorIssue]
# # pyright: ignore[reportOptionalIterable]
# from __future__ import annotations

# import contextvars
# import json
# import logging
# import re
# import sys

# from datetime import UTC, datetime, timezone
# from pprint import pformat
# from sys import stdout
# from typing import TYPE_CHECKING, Any, Literal, Optional, Union

# import langsmith
# import loguru


import structlog
logger = structlog.get_logger(__name__)
# from tqdm import tqdm


# if TYPE_CHECKING:
#     from loguru._logger import Logger as _Logger


# LOGLEVEL_MAPPING = {
#     50: "CRITICAL",
#     40: "ERROR",
#     30: "WARNING",
#     20: "INFO",
#     10: "DEBUG",
#     0: "NOTSET",
# }

# LOGURU_CONSOLE_FORMAT = (
#     "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
#     "<level>{level}</level> | "
#     "<cyan>{module}</cyan>:<cyan>{line}</cyan> | "
#     "<level>{extra[room_id]}</level> - "
#     "<level>{message}</level>"
# )

# LOGURU_FILE_FORMAT = (
#     "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
#     "<level>{level}</level> | "
#     "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
#     "<level>{extra[room_id]}</level> - "
#     "<level>{message}</level>"
# )

# # NOTE: this is the default format for loguru
# _LOGURU_FORMAT = (
#     "LOGURU_FORMAT",
#     str,
#     "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
#     "<level>{level: <8}</level> | "
#     "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
# )

# # NOTE: this is the new format for loguru
# NEW_logger_FORMAT = (
#     "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
#     "<level>{level: <8}</level> | "
#     "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
#     "<magenta>{file}:{line}</magenta> | "
#     "<level>{message}</level> | {extra}"
# )


# LOG_LEVEL = Literal[
#     "TRACE",
#     "DEBUG",
#     "INFO",
#     "SUCCESS",
#     "WARNING",
#     "ERROR",
#     "CRITICAL",
# ]


# # SOURCE: https://github.com/acgnhiki/blrec/blob/975fa2794a3843a883597acd5915a749a4e196c8/src/blrec/logging/configure_logging.py#L21
# class TqdmOutputStream:
#     def write(self, string: str = "") -> None:
#         tqdm.write(string, file=sys.stderr, end="")

#     def isatty(self) -> bool:
#         return sys.stderr.isatty()


# _console_handler_id: int | None = None
# _file_handler_id: int | None = None

# _old_log_dir: str | None = None
# _old_console_log_level: LOG_LEVEL | None = None
# _old_backup_count: int | None = None

# # ###################################################################################################
# # # NOTE: Make sure we don't log secrets
# # # SOURCE: https://github.com/Delgan/loguru/issues/537#issuecomment-986259036
# # def obfuscate_message(message: str):
# #     """Obfuscate sensitive information."""
# #     result = re.sub(r"pass: .*", "pass: xxx", s)
# #     return result
# #
# # def formatter(record):
# #     record["extra"]["obfuscated_message"] = obfuscate_message(record["message"])
# #     return "[{level}] {extra[obfuscated_message]}\n{exception}"
# #
# # logger.add(sys.stderr, format=formatter)
# # ###################################################################################################


# # SOURCE: https://github.com/bossjones/sandbox/blob/8ad412d9726e8ffc76ea8822f32e18a0cb5fc84f/dancedetector/dancedetector/dbx_logger/__init__.py
# # References
# # Solution comes from:
# #   https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
# #   https://github.com/pahntanapat/Unified-FastAPI-Gunicorn-Log
# #   https://github.com/Delgan/loguru/issues/365
# #   https://loguru.readthedocs.io/en/stable/api/logger.html#sink

# # request_id_contextvar is a context variable that will store the request id
# # ContextVar works with asyncio out of the box.
# # see https://docs.python.org/3/library/contextvars.html
# REQUEST_ID_CONTEXTVAR = contextvars.ContextVar("request_id", default=None)

# # initialize the context variable with a default value
# REQUEST_ID_CONTEXTVAR.set("notset")


# def set_log_extras(record: dict[str, Any]) -> None:
#     """Set extra log fields in the log record.

#     Args:
#         record: The log record to modify.
#     """
#     record["extra"]["datetime"] = datetime.now(UTC)


# # SOURCE: https://github.com/joint-online-judge/fastapi-rest-framework/blob/b0e93f0c0085597fcea4bb79606b653422f16700/fastapi_rest_framework/logging.py#L43
# def format_record(record: dict[str, Any]) -> str:
#     """Custom format for loguru loggers.

#     Uses pformat for log any data like request/response body during debug.
#     Works with logging if loguru handler it.

#     Args:
#         record: The log record.

#     Returns:
#         The formatted log record.
#     """
#     # """
#     # Custom format for loguru loggers.
#     # Uses pformat for log any data like request/response body during debug.
#     # Works with logging if loguru handler it.

#     # Example:
#     # -------
#     # >>> payload = [{"users":[{"name": "Nick", "age": 87, "is_active": True},
#     # >>>     {"name": "Alex", "age": 27, "is_active": True}], "count": 2}]
#     # >>> logger.bind(payload=).debug("users payload")
#     # >>> [   {   'count': 2,
#     # >>>         'users': [   {'age': 87, 'is_active': True, 'name': 'Nick'},
#     # >>>                      {'age': 27, 'is_active': True, 'name': 'Alex'}]}]

#     # """
#     format_string = NEW_logger_FORMAT
#     if record["extra"].get("payload") is not None:
#         record["extra"]["payload"] = pformat(record["extra"]["payload"], indent=4, compact=True, width=88)
#         format_string += "\n<level>{extra[payload]}</level>"

#     format_string += "{exception}\n"
#     return format_string


# class InterceptHandler(logging.Handler):
#     """
#     Intercept all logging calls (with standard logging) into our Loguru Sink
#     See: https://github.com/Delgan/loguru#entirely-compatible-with-standard-logging
#     """

#     loglevel_mapping = {
#         logging.CRITICAL: "CRITICAL",
#         logging.ERROR: "ERROR",
#         logging.FATAL: "FATAL",
#         logging.WARNING: "WARNING",
#         logging.INFO: "INFO",
#         logging.DEBUG: "DEBUG",
#         1: "DUMMY",
#         0: "NOTSET",
#     }

#     # from logging import DEBUG
#     # from logging import ERROR
#     # from logging import FATAL
#     # from logging import INFO
#     # from logging import WARN
#     # https://issueexplorer.com/issue/tiangolo/fastapi/4026
#     def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover
#         # Get corresponding Loguru level if it exists
#         try:
#             level = loguru.logger.level(record.levelname).name
#         except ValueError:
#             # DISABLED 12/10/2021 # level = str(record.levelno)
#             level = record.levelno

#         # Find caller from where originated the logged message
#         frame, depth = logging.currentframe(), 2
#         while frame.f_code.co_filename == logging.__file__:
#             frame = frame.f_back
#             # DISABLED 12/10/2021 # frame = cast(FrameType, frame.f_back)
#             depth += 1

#         loguru.logger.opt(depth=depth, exception=record.exc_info).log(
#             level,
#             record.getMessage(),
#         )


# def get_logger(
#     name: str,
#     provider: str | None = None,
#     level: int = logging.INFO,
#     logger: logging.Logger = logger,
# ) -> logging.Logger:
#     return logger


# def request_id_filter(record: dict[str, Any]):
#     """
#     Inject the request id from the context var to the log record. The logging
#     config format is defined in logger_config.yaml and has request_id as a field.
#     """
#     record["extra"]["request_id"] = REQUEST_ID_CONTEXTVAR.get()


# def reset_logging(log_dir: str, *, console_log_level: LOG_LEVEL = "INFO", backup_count: int | None = None) -> None:
#     global _console_handler_id, _file_handler_id
#     global _old_log_dir, _old_console_log_level, _old_backup_count
#     logger.configure(extra={"room_id": ""})

#     if console_log_level != _old_console_log_level:
#         if _console_handler_id is not None:
#             logger.remove(_console_handler_id)
#         else:
#             logger.remove()  # remove the default stderr handler

#         _console_handler_id = logger.add(sys.stderr, level=console_log_level, format=LOGURU_CONSOLE_FORMAT)

#         _old_console_log_level = console_log_level


# # @pysnooper.snoop()
# # @pysnooper.snoop(thread_info=True)
# # FIXME: https://github.com/abnerjacobsen/fastapi-mvc-loguru-demo/blob/main/mvc_demo/core/loguru_logs.py
# # SOURCE: https://loguru.readthedocs.io/en/stable/api/logger.html#loguru._logger.Logger
# def global_log_config(log_level: str | int = logging.DEBUG, json: bool = False) -> _Logger:
#     """Configure global logging settings.

#     Args:
#         log_level: The log level to use. Defaults to logging.DEBUG.
#         json: Whether to format logs as JSON. Defaults to False.

#     Returns:
#         The configured logger instance.
#     """

#     # SOURCE: https://github.com/acgnhiki/blrec/blob/975fa2794a3843a883597acd5915a749a4e196c8/src/blrec/logging/configure_logging.py#L21
#     global _console_handler_id, _file_handler_id
#     global _old_log_dir, _old_console_log_level, _old_backup_count
#     # SOURCE: https://github.com/acgnhiki/blrec/blob/975fa2794a3843a883597acd5915a749a4e196c8/src/blrec/logging/configure_logging.py#L21

#     if isinstance(log_level, str) and (log_level in logging._nameToLevel):
#         log_level = logging.DEBUG

#     intercept_handler = InterceptHandler()
#     # logging.basicConfig(handlers=[intercept_handler], level=LOG_LEVEL)
#     # logging.root.handlers = [intercept_handler]
#     logging.root.setLevel(log_level)

#     seen = set()
#     for name in [
#         *logging.root.manager.loggerDict.keys(),  # pylint: disable=no-member
#         "asyncio",
#         "discord",
#         "discord.client",
#         "discord.gateway",
#         "discord.http",
#         "chromadb",
#         "langchain_chroma",
#     ]:
#         if name not in seen:
#             seen.add(name.split(".")[0])
#             logging.getLogger(name).handlers = [intercept_handler]

#     logger.configure(
#         handlers=[
#             {
#                 # sink (file-like object, str, pathlib.Path, callable, coroutine function or logging.Handler) - An object in charge of receiving formatted logging messages and propagating them to an appropriate endpoint.
#                 "sink": stdout,
#                 # serialize (bool, optional) - Whether the logged message and its records should be first converted to a JSON string before being sent to the sink.
#                 "serialize": False,
#                 # format (str or callable, optional) - The template used to format logged messages before being sent to the sink. If a callable is passed, it should take a logging.Record as its first argument and return a string.
#                 "format": format_record,
#                 # diagnose (bool, optional) - Whether the exception trace should display the variables values to eases the debugging. This should be set to False in production to avoid leaking sensitive
#                 "diagnose": True,
#                 # backtrace (bool, optional) - Whether the exception trace formatted should be extended upward, beyond the catching point, to show the full stacktrace which generated the error.
#                 "backtrace": True,
#                 # enqueue (bool, optional) - Whether the messages to be logged should first pass through a multiprocessing-safe queue before reaching the sink. This is useful while logging to a file through multiple processes. This also has the advantage of making logging calls non-blocking.
#                 "enqueue": True,
#                 # catch (bool, optional) - Whether errors occurring while sink handles logs messages should be automatically caught. If True, an exception message is displayed on sys.stderr but the exception is not propagated to the caller, preventing your app to crash.
#                 "catch": True,
#             }
#         ],
#         # extra={"request_id": REQUEST_ID_CONTEXTVAR.get()},
#     )
#     print(f"Logger set up with log level: {log_level}")

#     setup_uvicorn_logger()
#     setup_gunicorn_logger()

#     # logger.disable("sentry_sdk")

#     return logger


# def setup_uvicorn_logger():
#     loggers = (logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("uvicorn."))
#     for uvicorn_logger in loggers:
#         uvicorn_logger.handlers = []
#     logging.getLogger("uvicorn").handlers = [InterceptHandler()]


# def setup_gunicorn_logger():
#     logging.getLogger("gunicorn.error").handlers = [InterceptHandler()]
#     logging.getLogger("gunicorn.access").handlers = [InterceptHandler()]


# def obfuscate_message(message: str) -> str:
#     """Obfuscate sensitive information in a message.

#     Args:
#         message: The message to obfuscate.

#     Returns:
#         The obfuscated message.
#     """
#     obfuscation_patterns = [
#         (r"email: .*", "email: ******"),
#         (r"password: .*", "password: ******"),
#         (r"newPassword: .*", "newPassword: ******"),
#         (r"resetToken: .*", "resetToken: ******"),
#         (r"authToken: .*", "authToken: ******"),
#         (r"located at .*", "located at ******"),
#         (r"#token=.*", "#token=******"),
#     ]
#     for pattern, replacement in obfuscation_patterns:
#         message = re.sub(pattern, replacement, message)

#     return message


# def formatter(record: dict[str, Any]) -> str:
#     """Format a log record.

#     Args:
#         record: The log record to format.

#     Returns:
#         The formatted log record.
#     """
#     record["extra"]["obfuscated_message"] = record["message"]
#     return (
#         "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> <level>[{level}]</level> - "
#         "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
#         "<level>{extra[obfuscated_message]}</level>\n{exception}"
#     )


# def formatter_sensitive(record: dict[str, Any]) -> str:
#     """Format a log record with sensitive information obfuscated.

#     Args:
#         record: The log record to format.

#     Returns:
#         The formatted log record with sensitive information obfuscated.
#     """
#     record["extra"]["obfuscated_message"] = obfuscate_message(record["message"])
#     return (
#         "<green>[{time:YYYY-MM-DD HH:mm:ss}]</green> <level>[{level}]</level> - "
#         "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
#         "<level>{extra[obfuscated_message]}</level>\n{exception}"
#     )

# # initalize logging
# global_log_config(
#     log_level=logging.getLevelName("DEBUG"),
#     json=False,
# )




# # Load the example inputs from q_a.json
# with open("datasets/q_a.json") as file:
#     example_inputs = [
#         (item["question"], item["answer"])
#         for item in json.load(file)
#     ]

# client = langsmith.Client()
# dataset_name = "Sandbox - Climate Change Q&A"

# # import bpdb
# # bpdb.set_trace()

# # Storing inputs in a dataset lets us
# # run chains and LLMs over a shared set of examples.
# dataset = client.create_dataset(
#     dataset_name=dataset_name,
#     description="Questions and answers about climate change.",
# )
# for input_prompt, output_answer in example_inputs:
#     client.create_example(
#         inputs={"input_question": input_prompt},
#         outputs={"output_answer": output_answer},
#         metadata={"source": "Various"},
#         dataset_id=dataset.id,
#     )
