"""Constants for the application.

This module contains all the constant values used throughout the application,
including paths, settings, and configuration values.
"""

from __future__ import annotations

import enum
import os
from pathlib import Path
from typing import Final

from contextforge_cli.aio_settings import aiosettings

# Project paths
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent
WORKSPACE_ROOT: Final[Path] = PROJECT_ROOT.parent

# LLM settings
MAX_TOKENS: Final[int] = aiosettings.llm_max_tokens
MAX_RETRIES: Final[int] = aiosettings.llm_max_retries
RETRY_DELAY: Final[float] = aiosettings.llm_retry_delay
RETRY_MULTIPLIER: Final[float] = aiosettings.llm_retry_multiplier
RETRY_MAX_DELAY: Final[float] = aiosettings.llm_retry_max_delay

# Resource limits
MAX_MEMORY_MB: Final[int] = aiosettings.max_memory_mb
MAX_TASKS: Final[int] = aiosettings.max_tasks
MAX_RESPONSE_SIZE_MB: Final[int] = aiosettings.max_response_size_mb
MAX_BUFFER_SIZE_KB: Final[int] = aiosettings.max_buffer_size_kb
TASK_TIMEOUT_SECONDS: Final[int] = aiosettings.task_timeout_seconds

# File paths
CONFIG_DIR: Final[Path] = PROJECT_ROOT / "config"
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
CACHE_DIR: Final[Path] = PROJECT_ROOT / "cache"

# Discord settings
PREFIX: Final[str] = aiosettings.prefix
CHANNEL_ID: Final[str] = "1240294186201124929"
CHAT_HISTORY_BUFFER: Final[int] = getattr(aiosettings, "chat_history_buffer", 10)

# Discord upload limits
MAX_BYTES_UPLOAD_DISCORD: Final[int] = 50000000
MAX_FILE_UPLOAD_IMAGES_IMGUR: Final[int] = 20000000
MAX_FILE_UPLOAD_VIDEO_IMGUR: Final[int] = 200000000
MAX_RUNTIME_VIDEO_IMGUR: Final[int] = 20  # seconds

# Twitter download commands
DL_SAFE_TWITTER_COMMAND: Final[str] = "gallery-dl --no-mtime {dl_uri}"
DL_TWITTER_THREAD_COMMAND: Final[str] = "gallery-dl --no-mtime --filter thread {dl_uri}"
DL_TWITTER_CARD_COMMAND: Final[str] = "gallery-dl --no-mtime --filter card {dl_uri}"

# Bot settings
SECONDS_DELAY_RECEIVING_MSG: Final[int] = (
    3  # give a delay for the bot to respond so it can catch multiple messages
)
MAX_THREAD_MESSAGES: Final[int] = 200
ACTIVATE_THREAD_PREFX: Final[str] = "💬✅"
INACTIVATE_THREAD_PREFIX: Final[str] = "💬❌"
MAX_CHARS_PER_REPLY_MSG: Final[int] = (
    1500  # discord has a 2k limit, we just break message into 1.5k
)

# Time constants
DAY_IN_SECONDS: Final[int] = 24 * 3600

# Numeric constants
ONE_MILLION: Final[int] = 1000000
FIVE_HUNDRED_THOUSAND: Final[int] = 500000
ONE_HUNDRED_THOUSAND: Final[int] = 100000
FIFTY_THOUSAND: Final[int] = 50000
THIRTY_THOUSAND: Final[int] = 30000
TWENTY_THOUSAND: Final[int] = 20000
TEN_THOUSAND: Final[int] = 10000
FIVE_THOUSAND: Final[int] = 5000


# Vector store settings
class SupportedVectorStores(str, enum.Enum):
    """Supported vector store types.

    This enum defines the supported vector store backends that can be used
    for storing and retrieving vector embeddings.

    Attributes:
        chroma: Chroma vector store
        milvus: Milvus vector store
        pgvector: PostgreSQL with pgvector extension
        pinecone: Pinecone vector store
        qdrant: Qdrant vector store
        weaviate: Weaviate vector store
    """

    chroma = "chroma"
    milvus = "milvus"
    pgvector = "pgvector"
    pinecone = "pinecone"
    qdrant = "qdrant"
    weaviate = "weaviate"


class SupportedEmbeddings(str, enum.Enum):
    """Supported embedding types.

    This enum defines the supported embedding models that can be used
    for generating vector embeddings.

    Attributes:
        openai: OpenAI embeddings
        cohere: Cohere embeddings
    """

    openai = "OpenAI"
    cohere = "Cohere"


# # FIXME: THIS IS NOT CONCURRENCY SAFE
# # Ensure directories exist
# for directory in [CONFIG_DIR, DATA_DIR, LOGS_DIR, CACHE_DIR]:
#     directory.mkdir(parents=True, exist_ok=True)
