#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from tabulate import tabulate


class ProviderStats(TypedDict):
    requests: int
    total_tokens: int
    total_cost: float

class TokenStats(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    reasoning_tokens: int | None

class RequestData(TypedDict):
    timestamp: float
    provider: str
    model: str
    token_usage: TokenStats
    cost: float
    thinking_time: float

class SessionSummary(TypedDict):
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost: float
    total_thinking_time: float
    provider_stats: dict[str, ProviderStats]
    session_duration: float

class SessionData(TypedDict):
    session_id: str
    start_time: float
    requests: list[RequestData]
    summary: SessionSummary

@dataclass
class TokenUsage:
    """Token usage statistics for an API request.

    Attributes:
        prompt_tokens: Number of tokens in the prompt
        completion_tokens: Number of tokens in the completion
        total_tokens: Total number of tokens used
        reasoning_tokens: Optional number of tokens used for reasoning
    """
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    reasoning_tokens: int | None = None

@dataclass
class APIResponse:
    """Response from an API request with token usage information.

    Attributes:
        content: The response content
        token_usage: Token usage statistics
        cost: Cost of the API call
        thinking_time: Time taken to generate the response
        provider: The API provider (e.g., "openai", "anthropic")
        model: The model used for the request
    """
    content: str
    token_usage: TokenUsage
    cost: float
    thinking_time: float = 0.0
    provider: Literal["openai", "anthropic"] = "openai"
    model: str = "unknown"

class TokenTracker:
    """Token usage tracker for API requests.

    Attributes:
        session_id: Unique identifier for the tracking session
        session_start: Timestamp when the session started
        requests: List of tracked API requests
        _logs_dir: Directory for storing session logs
        _session_file: Path to the current session file
    """
    def __init__(self, session_id: str | None = None, logs_dir: Path | None = None) -> None:
        # If no session_id provided, use today's date
        self.session_id: str = session_id or datetime.now().strftime("%Y-%m-%d")
        self.session_start: float = time.time()
        self.requests: list[RequestData] = []

        # Create logs directory if it doesn't exist
        self._logs_dir: Path = logs_dir or Path("token_logs")
        self._logs_dir.mkdir(exist_ok=True)

        # Initialize session file
        self._session_file: Path = self._logs_dir / f"session_{self.session_id}.json"

        # Load existing session data if file exists
        if self._session_file.exists():
            try:
                with open(self._session_file) as f:
                    data: SessionData = json.load(f)
                    self.session_start = data.get('start_time', self.session_start)
                    self.requests = data.get('requests', [])
            except Exception as e:
                print(f"Error loading existing session file: {e}", file=sys.stderr)

        self._save_session()

    def _save_session(self) -> None:
        """Save current session data to file."""
        session_data: SessionData = {
            "session_id": self.session_id,
            "start_time": self.session_start,
            "requests": self.requests,
            "summary": self.get_session_summary()
        }
        with open(self._session_file, "w") as f:
            json.dump(session_data, f, indent=2)

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory path."""
        return self._logs_dir

    @logs_dir.setter
    def logs_dir(self, path: Path) -> None:
        """Set the logs directory path and update session file path.

        Args:
            path: New logs directory path
        """
        self._logs_dir = path
        self._logs_dir.mkdir(exist_ok=True)
        self.session_file = self._logs_dir / f"session_{self.session_id}.json"

    @property
    def session_file(self) -> Path:
        """Get the session file path."""
        return self._session_file

    @session_file.setter
    def session_file(self, path: Path) -> None:
        """Set the session file path and load data if it exists.

        Args:
            path: New session file path
        """
        old_file = self._session_file
        self._session_file = path

        # If we have data and the new file doesn't exist, save our data
        if old_file.exists() and not path.exists() and self.requests:
            self._save_session()
        # If the new file exists, load its data
        elif path.exists():
            try:
                with open(path) as f:
                    data: SessionData = json.load(f)
                    self.session_start = data.get('start_time', self.session_start)
                    self.requests = data.get('requests', [])
            except Exception as e:
                print(f"Error loading existing session file: {e}", file=sys.stderr)

    @staticmethod
    def calculate_openai_cost(
        prompt_tokens: int,
        completion_tokens: int,
        model: str
    ) -> float:
        """Calculate OpenAI API cost based on model and token usage.

        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            model: The OpenAI model name

        Returns:
            float: Calculated cost in USD

        Raises:
            ValueError: If the model is not supported
        """
        # Special models with per-million token pricing
        special_models = {
            "o1": (15.0, 60.0),  # $15/M input, $60/M output
            "gpt-4o": (10.0, 30.0),  # $10/M input, $30/M output
            "deepseek-chat": (0.2, 0.2),  # $0.20/M for both input and output
        }

        # Standard OpenAI models with per-1k token pricing
        standard_models = {
            "gpt-4": (0.03, 0.06),
            "gpt-4-0314": (0.03, 0.06),
            "gpt-4-0613": (0.03, 0.06),
            "gpt-4-32k": (0.06, 0.12),
            "gpt-4-32k-0314": (0.06, 0.12),
            "gpt-4-32k-0613": (0.06, 0.12),
            "gpt-3.5-turbo": (0.0015, 0.002),
            "gpt-3.5-turbo-0301": (0.0015, 0.002),
            "gpt-3.5-turbo-0613": (0.0015, 0.002),
            "gpt-3.5-turbo-16k": (0.003, 0.004),
            "gpt-3.5-turbo-16k-0613": (0.003, 0.004)
        }

        if model in special_models:
            # Calculate cost using per-million token pricing
            input_price, output_price = special_models[model]
            input_cost = (prompt_tokens / 1_000_000) * input_price
            output_cost = (completion_tokens / 1_000_000) * output_price
            return input_cost + output_cost
        elif model in standard_models:
            # Calculate cost using per-1k token pricing
            input_price, output_price = standard_models[model]
            input_cost = (prompt_tokens * input_price / 1000)
            output_cost = (completion_tokens * output_price / 1000)
            return input_cost + output_cost
        else:
            # For unknown models, use gpt-3.5-turbo pricing and warn
            print(f"Warning: Unknown model '{model}', using gpt-3.5-turbo pricing", file=sys.stderr)
            input_cost = (prompt_tokens * 0.0015 / 1000)
            output_cost = (completion_tokens * 0.002 / 1000)
            return input_cost + output_cost

    @staticmethod
    def calculate_claude_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Calculate Claude API cost based on model and token usage"""
        # Claude-3 Sonnet pricing per 1M tokens
        # Source: https://www.anthropic.com/claude/sonnet
        if model in ["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229"]:
            input_price_per_m = 3.0  # $3 per million input tokens
            output_price_per_m = 15.0  # $15 per million output tokens
        else:
            raise ValueError(f"Unsupported Claude model for cost calculation: {model}. Only claude-3-5-sonnet-20241022 and claude-3-sonnet-20240229 are supported.")

        input_cost = (prompt_tokens / 1_000_000) * input_price_per_m
        output_cost = (completion_tokens / 1_000_000) * output_price_per_m
        return input_cost + output_cost

    def track_request(
        self,
        response: APIResponse,
        save: bool = True
    ) -> None:
        """Track an API request and update session data.

        Args:
            response: API response data to track
            save: Whether to save the session data after tracking
        """
        request_data: RequestData = {
            "timestamp": time.time(),
            "provider": response.provider,
            "model": response.model,
            "token_usage": {
                "prompt_tokens": response.token_usage.prompt_tokens,
                "completion_tokens": response.token_usage.completion_tokens,
                "total_tokens": response.token_usage.total_tokens,
                "reasoning_tokens": response.token_usage.reasoning_tokens
            },
            "cost": response.cost,
            "thinking_time": response.thinking_time
        }
        self.requests.append(request_data)
        if save:
            self._save_session()

    def get_session_summary(self) -> SessionSummary:
        """Generate a summary of the current session.

        Returns:
            SessionSummary: Summary of token usage, costs, and other statistics
        """
        total_prompt_tokens: int = 0
        total_completion_tokens: int = 0
        total_tokens: int = 0
        total_cost: float = 0.0
        total_thinking_time: float = 0.0
        provider_stats: dict[str, ProviderStats] = {}

        for req in self.requests:
            total_prompt_tokens += req["token_usage"]["prompt_tokens"]
            total_completion_tokens += req["token_usage"]["completion_tokens"]
            total_tokens += req["token_usage"]["total_tokens"]
            total_cost += req["cost"]
            total_thinking_time += req["thinking_time"]

            # Update provider stats
            provider = req["provider"]
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            provider_stats[provider]["requests"] += 1
            provider_stats[provider]["total_tokens"] += req["token_usage"]["total_tokens"]
            provider_stats[provider]["total_cost"] += req["cost"]

        return {
            "total_requests": len(self.requests),
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "total_thinking_time": total_thinking_time,
            "provider_stats": provider_stats,
            "session_duration": time.time() - self.session_start
        }

    def format_cost(self, cost: float) -> str:
        """Format a cost value as a currency string.

        Args:
            cost: Cost value to format

        Returns:
            str: Formatted cost string (e.g., "$1.23")
        """
        return f"${cost:.3f}"

    def format_duration(self, seconds: float) -> str:
        """Format a duration in seconds as a human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            str: Formatted duration string (e.g., "1h 23m 45s")
        """
        hours: int = int(seconds // 3600)
        minutes: int = int((seconds % 3600) // 60)
        secs: int = int(seconds % 60)

        parts: list[str] = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")

        return " ".join(parts)

    def display_summary(self, detailed: bool = False) -> None:
        """Display a summary of the current session.

        Args:
            detailed: Whether to show detailed provider statistics
        """
        summary = self.get_session_summary()

        print("\nSession Summary:")
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Total Tokens: {summary['total_tokens']}")
        print(f"  - Prompt Tokens: {summary['total_prompt_tokens']}")
        print(f"  - Completion Tokens: {summary['total_completion_tokens']}")
        print(f"Total Cost: {self.format_cost(summary['total_cost'])}")
        print(f"Total Thinking Time: {self.format_duration(summary['total_thinking_time'])}")
        print(f"Session Duration: {self.format_duration(summary['session_duration'])}")

        if detailed and summary['provider_stats']:
            print("\nProvider Statistics:")
            for provider, stats in summary['provider_stats'].items():
                print(f"\n{provider.upper()}:")
                print(f"  Requests: {stats['requests']}")
                print(f"  Total Tokens: {stats['total_tokens']}")
                print(f"  Total Cost: {self.format_cost(stats['total_cost'])}")

    @staticmethod
    def calculate_anthropic_cost(
        model: str,
        token_usage: TokenUsage
    ) -> float:
        """Calculate the cost for an Anthropic API request.

        Args:
            model: The Anthropic model used
            token_usage: Token usage statistics

        Returns:
            float: Calculated cost in USD
        """
        # Cost per 1k tokens (input, output)
        model_costs: dict[str, tuple[float, float]] = {
            "claude-2": (0.01102, 0.03268),
            "claude-instant-1": (0.00163, 0.00551)
        }

        if model not in model_costs:
            print(f"Warning: Unknown model '{model}', using claude-2 pricing", file=sys.stderr)
            model = "claude-2"

        input_cost, output_cost = model_costs[model]
        total_cost: float = (
            (token_usage.prompt_tokens * input_cost / 1000) +
            (token_usage.completion_tokens * output_cost / 1000)
        )
        return total_cost

# Global token tracker instance
_token_tracker: TokenTracker | None = None

def get_token_tracker(session_id: str | None = None, logs_dir: Path | None = None) -> TokenTracker:
    """Get or create a global token tracker instance"""
    global _token_tracker
    current_date = datetime.now().strftime("%Y-%m-%d")

    # If no tracker exists, create one
    if _token_tracker is None:
        _token_tracker = TokenTracker(session_id or current_date, logs_dir=logs_dir)
        return _token_tracker

    # If no session_id provided, reuse current tracker
    if session_id is None:
        if logs_dir is not None:
            _token_tracker.logs_dir = logs_dir
        return _token_tracker

    # If session_id matches current tracker, reuse it
    if session_id == _token_tracker.session_id:
        if logs_dir is not None:
            _token_tracker.logs_dir = logs_dir
        return _token_tracker

    # Otherwise, create a new tracker
    _token_tracker = TokenTracker(session_id, logs_dir=logs_dir)
    return _token_tracker

# Viewing functionality (moved from view_usage.py)
def format_cost(cost: float) -> str:
    """Format a cost value in dollars"""
    return f"${cost:.6f}"

def format_duration(seconds: float) -> str:
    """Format duration in a human-readable format"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.2f}m"
    hours = minutes / 60
    return f"{hours:.2f}h"

def load_session(session_file: Path) -> SessionData | None:
    """Load a session file and return its contents.

    Args:
        session_file: Path to the session file to load

    Returns:
        Optional[SessionData]: The loaded session data if successful, None if loading fails

    Raises:
        FileNotFoundError: If the session file does not exist
        json.JSONDecodeError: If the session file contains invalid JSON
    """
    try:
        with open(session_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading session file {session_file}: {e}", file=sys.stderr)
        return None

def display_session_summary(session_data: SessionData, show_requests: bool = False) -> None:
    """Display a summary of the session with token usage and cost statistics.

    Args:
        session_data: Session data containing requests and summary information
        show_requests: Whether to display individual request details

    Note:
        This function prints formatted tables showing:
        - Session overview (ID, duration, total requests, cost)
        - Token usage statistics (prompt, completion, total tokens)
        - Provider statistics (requests, tokens, cost per provider)
        - Individual request details (if show_requests is True)
    """
    summary = session_data["summary"]

    # Print session overview
    print("\nSession Overview")
    print("===============")
    print(f"Session ID: {session_data['session_id']}")
    print(f"Duration: {format_duration(summary['session_duration'])}")
    print(f"Total Requests: {summary['total_requests']}")
    print(f"Total Cost: {format_cost(summary['total_cost'])}")

    # Print token usage
    print("\nToken Usage")
    print("===========")
    print(f"Prompt Tokens: {summary['total_prompt_tokens']:,}")
    print(f"Completion Tokens: {summary['total_completion_tokens']:,}")
    print(f"Total Tokens: {summary['total_tokens']:,}")

    # Print provider stats
    print("\nProvider Statistics")
    print("==================")
    provider_data: list[list[str | int]] = []
    for provider, stats in summary["provider_stats"].items():
        provider_data.append([
            provider,
            stats["requests"],
            f"{stats['total_tokens']:,}",
            format_cost(stats["total_cost"])
        ])
    print(tabulate(
        provider_data,
        headers=["Provider", "Requests", "Tokens", "Cost"],
        tablefmt="simple"
    ))

    # Print individual requests if requested
    if show_requests:
        print("\nIndividual Requests")
        print("==================")
        request_data: list[list[str | float]] = []
        for req in session_data["requests"]:
            request_data.append([
                req["provider"],
                req["model"],
                f"{req['token_usage']['total_tokens']:,}",
                format_cost(req["cost"]),
                f"{req['thinking_time']:.2f}s"
            ])
        print(tabulate(
            request_data,
            headers=["Provider", "Model", "Tokens", "Cost", "Time"],
            tablefmt="simple"
        ))

def list_sessions(logs_dir: Path):
    """List all available session files"""
    session_files = sorted(logs_dir.glob("session_*.json"))
    if not session_files:
        print("No session files found.")
        return

    for session_file in session_files:
        session_data = load_session(session_file)
        if session_data:
            summary = session_data["summary"]
            print(f"\nSession: {session_data['session_id']}")
            print(f"Duration: {format_duration(summary['session_duration'])}")
            print(f"Requests: {summary['total_requests']}")
            print(f"Total Cost: {format_cost(summary['total_cost'])}")
            print(f"Total Tokens: {summary['total_tokens']:,}")

def main():
    parser = argparse.ArgumentParser(description='View LLM API usage statistics')
    parser.add_argument('--session', type=str, help='Session ID to view details for')
    parser.add_argument('--requests', action='store_true', help='Show individual requests')
    args = parser.parse_args()

    logs_dir = Path("token_logs")
    if not logs_dir.exists():
        print("No logs directory found")
        return

    if args.session:
        session_file = logs_dir / f"session_{args.session}.json"
        if not session_file.exists():
            print(f"Session file not found: {session_file}")
            return

        session_data = load_session(session_file)
        if session_data:
            display_session_summary(session_data, args.requests)
    else:
        list_sessions(logs_dir)

if __name__ == "__main__":
    main()
