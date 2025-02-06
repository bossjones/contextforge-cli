# pylint: disable=no-member
# pylint: disable=no-name-in-module
# pylint: disable=no-value-for-parameter
# pylint: disable=possibly-used-before-assignment
# pyright: reportAttributeAccessIssue=false
# pyright: reportConstantRedefinition=true
# pyright: reportInvalidTypeForm=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUndefinedVariable=false

from __future__ import annotations

import enum
import pathlib
from datetime import timedelta, timezone
from typing import Any, Literal

from pydantic import (
    Field,
    Json,
    PostgresDsn,
    RedisDsn,
    SecretStr,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console


def democracy_user_agent() -> str:
    """Get a common user agent"""
    return "contextforge-cli/0.0.1"


# Get rid of warning
# USER_AGENT environment variable not set, consider setting it to identify your requests.
# os.environ["USER_AGENT"] = democracy_user_agent()

TIMEZONE = timezone(timedelta(hours=-5), name="America/New_York")


class SettingsError(Exception):
    """Base exception for all settings-related errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the settings error.

        Args:
            message: The error message
            context: Additional context about the error
        """
        self.context = context or {}
        super().__init__(message)


class ValidationError(SettingsError):
    """Raised when settings validation fails."""

    def __init__(
        self,
        message: str,
        field_name: str,
        invalid_value: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the validation error.

        Args:
            message: The error message
            field_name: Name of the field that failed validation
            invalid_value: The value that failed validation
            context: Additional context about the error
        """
        self.field_name = field_name
        self.invalid_value = invalid_value
        super().__init__(
            f"{message} (field: {field_name}, value: {invalid_value})", context
        )


class ModelConfigError(SettingsError):
    """Raised when there are issues with model configuration."""

    def __init__(
        self, message: str, model_name: str, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize the model configuration error.

        Args:
            message: The error message
            model_name: Name of the model with configuration issues
            context: Additional context about the error
        """
        self.model_name = model_name
        super().__init__(f"{message} (model: {model_name})", context)


class SecurityError(SettingsError):
    """Raised when there are security-related issues with settings."""

    def __init__(
        self, message: str, setting_name: str, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize the security error.

        Args:
            message: The error message
            setting_name: Name of the setting with security issues
            context: Additional context about the error
        """
        self.setting_name = setting_name
        super().__init__(
            f"Security error with setting '{setting_name}': {message}", context
        )


class ConfigurationError(SettingsError):
    """Raised when there are issues with the overall configuration."""

    def __init__(
        self, message: str, config_section: str, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize the configuration error.

        Args:
            message: The error message
            config_section: Section of configuration with issues
            context: Additional context about the error
        """
        self.config_section = config_section
        super().__init__(
            f"Configuration error in section '{config_section}': {message}", context
        )


def normalize_settings_path(file_path: str) -> str:
    """Normalize file paths with tilde expansion.

    Converts paths starting with ~ to absolute paths using the user's home directory.

    Args:
        file_path: Path to normalize, may start with ~

    Returns:
        str: Normalized absolute path
    """
    return (
        str(pathlib.Path(file_path).expanduser())
        if file_path.startswith("~")
        else file_path
    )


class LogLevel(str, enum.Enum):
    """Possible log levels for application logging.

    Standard Python logging levels used throughout the application.
    """

    NOTSET = "NOTSET"  # 0
    DEBUG = "DEBUG"  # 10
    INFO = "INFO"  # 20
    WARNING = "WARNING"  # 30
    ERROR = "ERROR"  # 40
    FATAL = "FATAL"  # 50


class AioSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CONTEXTFORGE_CLI_CONFIG_",
        env_file=(".env", ".envrc"),
        env_file_encoding="utf-8",
        extra="allow",
        arbitrary_types_allowed=True,
        json_schema_extra={
            "properties": {
                "llm_retriever_type": {
                    "type": "string",
                    "default": "vector_store",
                    "description": "Type of retriever to use",
                }
            }
        },
    )

    # OpenAI settings
    openai_api_key: SecretStr = Field(
        default=SecretStr(""), description="OpenAI API key"
    )

    cohere_api_key: SecretStr = Field(
        env="COHERE_API_KEY", description="cohere api key", default=SecretStr("")
    )
    anthropic_api_key: SecretStr = Field(
        env="ANTHROPIC_API_KEY", description="claude api key", default=SecretStr("")
    )
    # Development settings
    dev_mode: bool = Field(
        default=False,
        description="Enable development mode for additional debugging and error handling",
    )
    better_exceptions: int = Field(
        default=1, description="Enable better exception formatting"
    )
    pythonasynciodebug: bool = Field(
        env="PYTHONASYNCIODEBUG",
        description="enable or disable asyncio debugging",
        default=0,
    )

    # Monitor settings
    monitor_host: str = Field(
        default="localhost", description="Host for monitoring server"
    )
    monitor_port: int = Field(default=50102, description="Port for monitoring server")

    # Debug settings
    debug_langchain: bool | None = Field(
        default=False, description="Enable LangChain debug logging"
    )

    # Audit settings
    audit_log_send_channel: str = Field(
        default="", description="Channel ID for audit log messages"
    )

    # OpenCommit settings
    oco_openai_api_key: SecretStr = Field(
        env="OCO_OPENAI_API_KEY",
        default=SecretStr(""),
        description="OpenAI API key for OpenCommit",
    )
    oco_tokens_max_input: int = Field(
        env="OCO_TOKENS_MAX_INPUT",
        default=4096,
        description="Maximum input tokens for OpenCommit",
    )
    oco_tokens_max_output: int = Field(
        env="OCO_TOKENS_MAX_OUTPUT",
        default=500,
        description="Maximum output tokens for OpenCommit",
    )
    oco_model: str = Field(
        env="OCO_MODEL",
        default="gpt-4o-mini-2024-07-18",
        description="Model to use for OpenCommit",
    )
    oco_language: str = Field(
        env="OCO_LANGUAGE", default="en", description="Language for OpenCommit messages"
    )
    oco_prompt_module: str = Field(
        env="OCO_PROMPT_MODULE",
        default="conventional-commit",
        description="Prompt module for OpenCommit",
    )
    oco_ai_provider: str = Field(
        env="OCO_AI_PROVIDER",
        default="openai",
        description="AI provider for OpenCommit",
    )

    # OpenAI specific settings
    openai_embeddings_model: str = Field(
        default="text-embedding-3-large", description="OpenAI model for embeddings"
    )

    # LLM retriever settings
    llm_retriever_type: str = Field(
        default="vector_store", description="Type of retriever to use"
    )

    # Development settings
    dev_mode: bool = Field(
        default=False,
        description="Enable development mode for additional debugging and error handling",
    )
    better_exceptions: int = Field(
        default=1, description="Enable better exception formatting"
    )
    pythonasynciodebug: bool = Field(
        env="PYTHONASYNCIODEBUG",
        description="enable or disable asyncio debugging",
        default=0,
    )

    # Bot settings
    prefix: str = Field(default="?", description="Command prefix for the Discord bot")
    discord_command_prefix: str = "?"
    discord_client_id: int | str = Field(
        default=0, description="Discord application client ID"
    )
    discord_client_secret: SecretStr = Field(
        default=SecretStr(""), description="Discord application client secret"
    )
    discord_token: SecretStr = Field(
        default=SecretStr(""), description="Discord bot token"
    )
    discord_admin_user_id: int = Field(
        default=3282, description="Discord user ID of the bot administrator"
    )
    discord_general_channel: int = Field(
        default=908894727779258390,
        description="Discord channel ID for general messages",
    )
    discord_admin_user_invited: bool = Field(
        default=False, description="Whether the admin user has been invited to the bot"
    )
    enable_ai: bool = Field(default=True, description="Enable AI features")
    rate_limit_rate: int = Field(
        default=10, description="Number of commands allowed per time period"
    )
    rate_limit_per: float = Field(
        default=12.0, description="Time period in seconds for rate limiting"
    )

    max_queue_size: int = Field(
        default=1000, description="Maximum size of the command queue"
    )
    num_workers: int = Field(default=3, description="Number of worker threads")

    enable_resource_management: bool = Field(
        default=False, description="Enable resource management"
    )
    # Resource management settings
    max_memory_mb: int = Field(
        default=8192, description="Maximum memory usage in megabytes"
    )
    max_tasks: int = Field(
        default=100, description="Maximum number of concurrent tasks"
    )
    max_response_size_mb: int = Field(
        default=8, description="Maximum response size in megabytes"
    )
    max_buffer_size_kb: int = Field(
        default=128, description="Maximum buffer size in kilobytes"
    )
    task_timeout_seconds: int = Field(
        default=300, description="Task timeout in seconds"
    )

    # LLM settings
    llm_model_name: str = Field(
        default="gpt-4o-mini", description="The chat model to use"
    )
    llm_temperature: float = Field(
        default=0.0, description="Temperature for LLM sampling"
    )
    llm_max_tokens: int = Field(
        default=1024, description="Maximum tokens for LLM response"
    )
    llm_top_p: float = Field(default=1.0, description="Top p for nucleus sampling")
    llm_frequency_penalty: float = Field(
        default=0.0, description="Frequency penalty for token generation"
    )
    llm_presence_penalty: float = Field(
        default=0.0, description="Presence penalty for token generation"
    )
    llm_stop: list[str] = Field(
        default_factory=list, description="Stop sequences for LLM"
    )

    # LLM retry settings
    llm_max_retries: int = Field(
        default=3, description="Maximum number of retry attempts for LLM calls"
    )
    llm_retry_delay: int = Field(
        default=1, description="Initial retry delay in seconds"
    )
    llm_retry_max_delay: int = Field(
        default=60, description="Maximum retry delay in seconds"
    )
    llm_retry_multiplier: float = Field(
        default=2.0, description="Multiplier for retry delay"
    )
    llm_retry_codes: list[int] = Field(
        default_factory=list, description="HTTP status codes to retry on"
    )
    llm_retry_methods: list[str] = Field(
        default_factory=list, description="HTTP methods to retry"
    )
    llm_retry_backoff: bool = Field(
        default=True, description="Use exponential backoff for retries"
    )
    llm_retry_jitter: bool = Field(
        default=True, description="Add jitter to retry delays"
    )

    # QA settings
    qa_no_chat_history: bool = Field(
        default=False, description="Disable chat history for QA"
    )
    qa_followup_sim_threshold: float = Field(
        default=0.735, description="Similarity threshold for followup questions"
    )
    qa_retriever: dict[str, Any] = Field(
        default_factory=dict, description="QA retriever configuration"
    )

    # Global settings
    globals_try_patchmatch: bool = Field(
        default=True, description="Try patch matching in global scope"
    )
    globals_always_use_cpu: bool = Field(
        default=False, description="Force CPU usage for operations"
    )
    globals_internet_available: bool = Field(
        default=True, description="Whether internet access is available"
    )
    globals_full_precision: bool = Field(
        default=False, description="Use full precision for calculations"
    )
    globals_ckpt_convert: bool = Field(default=False, description="Convert checkpoints")
    globals_log_tokenization: bool = Field(
        default=False, description="Log tokenization details"
    )

    # Additional debug settings
    debug_langchain: bool = Field(
        default=True, description="Enable LangChain debug logging"
    )
    python_debug: bool = Field(default=False, description="Enable Python debug mode")
    pythondevmode: bool = Field(
        env="PYTHONDEVMODE",
        description="The Python Development Mode introduces additional runtime checks that are too expensive to be enabled by default. It should not be more verbose than the default if the code is correct; new warnings are only emitted when an issue is detected.",
        default=0,
    )
    local_test_debug: bool = Field(
        default=False, description="Enable local test debugging"
    )
    local_test_enable_evals: bool = Field(
        default=False, description="Enable evaluation tests locally"
    )
    http_client_debug_enabled: bool = Field(
        default=False, description="Enable HTTP client debugging"
    )

    # LLM streaming settings
    llm_streaming: bool = Field(
        default=False, description="Whether to use streaming responses from LLM"
    )

    # LLM Provider settings
    llm_provider: str = Field(
        default="openai",
        description="The LLM provider to use (openai, anthropic, etc.)",
    )
    llm_document_loader_type: str = Field(
        default="pymupdf", description="The document loader type to use"
    )
    llm_embedding_model_type: str = Field(
        default="text-embedding-3-large", description="The embedding model type to use"
    )
    # Feature flags
    rag_answer_hallucination_feature_flag: bool = Field(
        default=False, description="Enable RAG answer hallucination detection"
    )

    enable_sentry: bool = Field(
        default=False, description="Enable Sentry error tracking"
    )

    experimental_redis_memory: bool = Field(
        default=False, description="Enable experimental Redis memory features"
    )

    rag_doc_relevance_and_hallucination_feature_flag: bool = Field(
        default=False,
        description="Enable RAG document relevance and hallucination detection",
    )

    # OpenAI settings
    openai_api_key: SecretStr = Field(
        default=SecretStr(""), description="OpenAI API key"
    )

    chatbot_type: Literal["terminal", "discord"] = Field(
        env="CHATBOT_TYPE", description="chatbot type", default="terminal"
    )

    cohere_api_key: SecretStr = Field(
        env="COHERE_API_KEY", description="cohere api key", default=SecretStr("")
    )
    anthropic_api_key: SecretStr = Field(
        env="ANTHROPIC_API_KEY", description="claude api key", default=SecretStr("")
    )

    chat_history_buffer: int = Field(
        default=10, description="Number of messages to keep in chat history"
    )

    chat_model: str = Field(default="gpt-4o-mini", description="The chat model to use")

    vision_model: str = Field(
        env="VISION_MODEL", description="vision model", default="gpt-4o"
    )

    eval_max_concurrency: int = Field(
        default=4, description="Maximum number of concurrent evaluation tasks"
    )

    groq_api_key: SecretStr = Field(
        env="GROQ_API_KEY", description="groq api key", default=SecretStr("")
    )

    langchain_api_key: SecretStr = Field(
        default=SecretStr(""), description="API key for LangChain"
    )

    langchain_debug_logs: bool = Field(
        env="LANGCHAIN_DEBUG_LOGS",
        description="enable or disable langchain debug logs",
        default=0,
    )

    langchain_hub_api_key: SecretStr = Field(
        default=SecretStr(""), description="API key for LangChain Hub"
    )
    langchain_tracing_v2: bool = Field(
        default=False, description="Enable LangChain tracing v2"
    )
    llm_embedding_model_name: str = Field(
        default="text-embedding-3-large", description="The embedding model to use"
    )

    # LangChain Integration Settings
    langchain_endpoint: str = Field(
        env="LANGCHAIN_ENDPOINT",
        description="langchain endpoint",
        default="https://api.smith.langchain.com",
    )
    langchain_hub_api_url: str = Field(
        env="LANGCHAIN_HUB_API_URL",
        description="langchain hub api url for langsmith",
        default="https://api.hub.langchain.com",
    )
    langchain_project: str = Field(
        env="LANGCHAIN_PROJECT",
        description="langsmith project name",
        default="contextforge_cli",
    )

    tavily_api_key: SecretStr = Field(
        env="TAVILY_API_KEY", description="Tavily API key", default=SecretStr("")
    )
    brave_search_api_key: SecretStr = Field(
        env="BRAVE_SEARCH_API_KEY",
        description="Brave Search API key",
        default=SecretStr(""),
    )
    unstructured_api_key: SecretStr = Field(
        env="UNSTRUCTURED_API_KEY",
        description="unstructured api key",
        default=SecretStr(""),
    )
    unstructured_api_url: str = Field(
        env="UNSTRUCTURED_API_URL",
        description="unstructured api url",
        default="https://api.unstructured.io/general/v0/general",
    )

    debug_aider: bool = Field(
        env="DEBUG_AIDER",
        description="debug tests stuff written by aider",
        default=False,
    )
    debug_langgraph_studio: bool = Field(
        env="DEBUG_LANGGRAPH_STUDIO",
        description="enable langgraph studio debug",
        default=False,
    )

    python_fault_handler: bool = Field(
        env="PYTHONFAULTHANDLER", description="enable fault handler", default=False
    )

    editor: str = Field(env="EDITOR", description="EDITOR", default="vim")
    visual: str = Field(env="VISUAL", description="VISUAL", default="vim")
    git_editor: str = Field(env="GIT_EDITOR", description="GIT_EDITOR", default="vim")

    ai_docs_model: str = Field(
        env="AI_DOCS_MODEL",
        description="AI Docs model",
        # default="claude-3-opus-20240229"
        default="claude-3-5-sonnet-20241022",
    )

    logging_environment: Literal["testing", "development", "production"] = Field(
        env="LOGGING_ENVIRONMENT",
        description="Logging environment",
        default="development",
    )

    tool_allowlist: list[str] = ["tavily_search", "magic_function"]

    tavily_search_max_results: int = 3

    debug: bool = True
    log_pii: bool = True

    sentry_dsn: SecretStr = Field(default=SecretStr(""), description="Sentry DSN")
    enable_sentry: bool = False

    changelogs_github_api_token: SecretStr = Field(
        env="CHANGELOGS_GITHUB_API_TOKEN",
        description="GitHub API token for Changelogs",
        default=SecretStr(""),
    )

    gemini_api_key: SecretStr = Field(
        env="GEMINI_API_KEY", description="gemini api key", default=SecretStr("")
    )

    firecrawl_api_key: SecretStr = Field(
        env="FIRECRAWL_API_KEY", description="Firecrawl API key", default=SecretStr("")
    )

    # Model-specific settings
    max_tokens: int = Field(
        env="MAX_TOKENS",
        description="Maximum number of tokens for the model",
        default=900,
    )
    max_retries: int = Field(
        env="MAX_RETRIES",
        description="Maximum number of retries for API calls",
        default=9,
    )

    chunk_size: int = Field(
        env="CHUNK_SIZE", description="Size of each text chunk", default=1000
    )
    chunk_overlap: int = Field(
        env="CHUNK_OVERLAP", description="Overlap between text chunks", default=200
    )

    dataset_name: str = Field(
        env="DATASET_NAME",
        description="Name of the dataset to use for evaluation",
        default="Climate Change Q&A",
    )
    default_search_kwargs: dict[str, int] = Field(
        env="DEFAULT_SEARCH_KWARGS",
        description="Default arguments for similarity search",
        default_factory=lambda: {"k": 2},
    )

    localfilestore_root_path: str = Field(
        env="LOCALFILESTORE_ROOT_PATH",
        description="root path for local file store",
        default="./local_file_store",
    )
    log_level: int = 10  # logging.DEBUG
    thirdparty_lib_loglevel: str = "INFO"

    provider: str = Field(
        env="PROVIDER",
        description="AI provider (openai or anthropic)",
        default="openai",
    )

    retry_stop_after_attempt: int = 3
    retry_wait_exponential_multiplier: int | float = 2
    retry_wait_exponential_max: int | float = 5
    retry_wait_exponential_min: int | float = 1
    retry_wait_fixed: int | float = 15

    setup_timeout: float = Field(
        default=30.0, description="Timeout in seconds for bot setup"
    )


def get_rich_console() -> Console:
    """Get a Rich console instance for formatted output.

    Returns:
        Console: A configured Rich console instance for formatted terminal output
    """
    return Console()


# Global settings instance
aiosettings = AioSettings()
# avoid-global-variables
# In-place reloading
aiosettings.__init__()
