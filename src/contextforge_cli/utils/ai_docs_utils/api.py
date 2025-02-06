# pylint: disable=no-member
# pylint: disable=no-name-in-module
# pylint: disable=no-value-for-parameter
# pylint: disable=possibly-used-before-assignment
# pyright: reportAttributeAccessIssue=false
# pyright: reportInvalidTypeForm=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUndefinedVariable=false

from __future__ import annotations

import os
import sys

import anthropic
import structlog
from anthropic.types import Message as AnthropicMessage
from dotenv import find_dotenv, load_dotenv
from transformers.models.gpt2 import GPT2Tokenizer

from contextforge_cli.aio_settings import aiosettings

# from transformers import GPT2Tokenizer
# SOURCE: https://github.com/connor-john/ai-docs

load_dotenv(find_dotenv())

logger = structlog.get_logger(__name__)

CLIENT = anthropic.Anthropic(api_key=aiosettings.anthropic_api_key.get_secret_value())
ASYNC_CLIENT = anthropic.AsyncAnthropic(
    api_key=aiosettings.anthropic_api_key.get_secret_value()
)

PULL_REQUEST_SYSTEM_PROMPT = """Your job is to act as a expert software engineer and provide outlined comprehensive feedback for merge requests in a appraochable and understanding way.
Key criteria outlined are:
Does this code change accomplish what it is supposed to do?
Can this solution be simplified?
Does this change add unwanted compile-time or run-time dependencies?
Is a framework, API, library, or service used that should not be used?
Could an additional framework, API, library, or service improve the solution?
Is the code at the right abstraction level?
Is the code modular enough?
Can a better solution be found in terms of maintainability, readability, performance, or security?
Does similar functionality already exist in the codebase? If yes, why isnt it reused?
Are there any best practices, design patterns or language-specific patterns that could substantially improve this code?
Does this code adhere to Object-Oriented Analysis and Design Principles, like the Single Responsibility Principle, Open-Close Principle, Liskov Substitution Principle, Interface Segregation, or Dependency Injection?
Can you think of any use case in which the code does not behave as intended?
Can you think of any inputs or external events that could break the code?
You will receive both a description of the changes, an outline of the changes and the existing codebase.
"""

BASIC_DOCS_SYSTEM_PROMPT = """Your job is to act as the expert software engineer and provide detailed technical documentation broken into readbile formats.
You will be able to read the majority of a code repository given as a converted single text with the Prefix "#File:" declaring the start of the new file e.g., # File: masters-and-sons-main/src/components/ArrowTable.tsx.
Typescipt projects are required to use pnpm for commands, python project if they have a pyproject.toml will be using poetry. MySQL databases are typically planetscale, and in that case we follow planetscales recommended use of prisma (if prisms ORM is used).
Documentation should be broken down into:
Introduction:
- Provide a brief overview of the project.
- Mention the purpose and core functionality of the code repository.
- Highlight the key features and potential use cases.
Codebase Overview:
- Provide an in-depth overview of the codebase architecture and design patterns used.
- Detail the modules, components, and their interactions within the application.
Development Environment Setup:
- Step-by-step instructions for setting up the development environment, including necessary tools and dependencies.
- Include guidelines for configuring IDEs, linters, and other development tools.
Code Repository Structure:
- Explain the repository structure, detailing the purpose of different directories and files.
- Document naming conventions, file organization, and any specific standards followed in the codebase.
Key Points of Complexity:
- Outline each keypoint of complexity
    - Breakdown each keypoint
Installation and Setup:
- Offer detailed instructions on installing and setting up the project.
- Include any prerequisites or dependencies required.
Getting Started:
- Guide users through a simple, initial setup or quick-start process.
- Include basic examples or a simple tutorial to help users begin using the project quickly.
The output should be detailed in standard markdown, using headers to improve readability.
"""

REFINED_DOCS_FOLLOW_UP_PROMPT = """You are instructed to further refine the documentation, there is no need to repeat basic content. Focus on delivering expert value insights for internal development handover outlined in the below criteria.
In-Depth Architecture Overview:
- Provide comprehensive diagrams and descriptions of the system architecture, including data flow, service interactions, and external dependencies.
- Detail the critical architectural decisions and their justifications, discussing the trade-offs and alternatives considered.
Advanced Codebase Insights:
- Delve into complex modules and components, explaining intricate details that are crucial for understanding system behavior.
- Document any non-obvious implementation strategies and optimizations, explaining why they were necessary and how they impact the system.
Environment and Toolchain Deep Dive:
- Offer a detailed guide on the development, testing, and production environments, including specific configurations, underlying infrastructure details, and environment parity practices.
- Describe the complete toolchain, including build systems, deployment pipelines, and any custom tooling.
Critical Dependency Analysis:
- Provide an exhaustive overview of external libraries, frameworks, and services the system depends on, including versioning, patching strategies, and known issues.
- Discuss how dependencies are managed, potential risks associated with them, and mitigation strategies.
Performance Considerations:
- Document performance benchmarks, profiling methods, and optimization strategies.
- Include case studies of past performance issues, their analysis, and the solutions implemented.
Security Protocols:
- Detail the security measures and protocols in place, including authentication, authorization, data encryption, and any proprietary security frameworks or libraries.
- Discuss security best practices, known vulnerabilities (and their mitigations), and any relevant security audits.
Testing and Quality Assurance:
- Elaborate on the testing strategy, including unit, integration, and end-to-end tests, highlighting any test-driven development (TDD) practices.
- Document the approach to continuous integration/continuous deployment (CI/CD), test automation, and quality benchmarks.
Troubleshooting and Debugging Guide:
- Provide a detailed guide for troubleshooting common issues, including debugging tips, logging best practices, and monitoring tools used.
- Share real-world incidents or outages, post-mortem analyses, and lessons learned.
Data Management and Migration:
- Explain the data architecture, schema design, and any data migration strategies or scripts.
- Discuss backup strategies, data integrity checks, and disaster recovery plans.
Developer Onboarding:
- Create a comprehensive onboarding guide for new developers, including step-by-step setup instructions, key contacts, and resources for getting up to speed.
- Include a glossary of terms, acronyms, and jargon used within the project to aid in understanding the documentation and codebase.
"""

PYTHON_MODULE_DOCS_PROMPT = """Your task is to create comprehensive documentation for a Python module, focusing on practical usage, implementation details, and testing examples. Structure your response using the following sections:

Module Overview:
- Explain the module's purpose, core functionality, and key features
- Describe the problems it solves and its target use cases
- List any key dependencies or requirements

Installation and Setup:
- Provide step-by-step installation instructions
- Detail any environment setup requirements
- List all required dependencies with version specifications
- Include any necessary configuration steps

Usage Guide:
- Provide detailed examples of common use cases
- Include code snippets demonstrating key functionality
- Explain important classes, methods, and functions
- Document any configuration options or settings
- Show example outputs where relevant

Testing Guide:
For each test case, provide:
1. Test purpose and description
2. Required test fixtures and their setup
3. Complete test implementation
4. Expected outcomes and assertions

Example Test Case Format:
```python
# Example test file: test_module.py
from __future__ import annotations

import pytest
from typing import AsyncGenerator, Generator
from pytest_mock import MockerFixture
from _pytest.logging import LogCaptureFixture

@pytest.fixture
def sample_fixture() -> Generator[dict, None, None]:
    \"\"\"Provide test data for sample tests.

    Returns:
        Generator[dict, None, None]: Test data dictionary
    \"\"\"
    data = {"key": "value"}
    yield data

@pytest.mark.asyncio
async def test_sample_async_function(
    mocker: MockerFixture,
    sample_fixture: dict,
    caplog: LogCaptureFixture
) -> None:
    \"\"\"Test async function behavior.

    Args:
        mocker: Pytest mocker fixture
        sample_fixture: Sample test data
        caplog: Log capture fixture
    \"\"\"
    # Test setup
    mock_dependency = mocker.patch("module.dependency")
    mock_dependency.return_value = "mocked_value"

    # Execute test
    result = await my_async_function(sample_fixture["key"])

    # Assertions
    assert result == "expected_value"
    assert "Expected log message" in caplog.text
```

Testing Best Practices:
- Use pytest as the primary testing framework
- Implement proper type annotations in all tests
- Create reusable fixtures for common test data
- Use appropriate pytest markers (e.g., @pytest.mark.asyncio)
- Implement proper mocking strategies
- Use structlog's capture_logs for testing log output
- Test both success and error cases
- Include edge case testing
- Document test coverage requirements

Common Test Fixtures:
- Document standard fixtures (tmp_path, caplog, etc.)
- Explain custom fixtures and their purposes
- Show fixture factory patterns when needed
- Demonstrate fixture scope usage

Error Handling and Edge Cases:
- Document expected exceptions and error states
- Show how to test error conditions
- Provide examples of boundary testing
- Include validation testing examples

Performance Testing:
- Show examples of performance test cases
- Document benchmarking approaches
- Include load testing examples if relevant

Integration Testing:
- Demonstrate testing with external dependencies
- Show database integration testing
- Include API integration test examples
- Document mock vs. real dependency testing

Debugging and Troubleshooting:
- Provide debugging strategies
- Document common issues and solutions
- Include logging and monitoring guidance
- Show debugging tool usage (pdb, ipdb, etc.)

Remember to:
- Include docstrings for all test functions
- Add type annotations for all parameters
- Document fixture dependencies
- Show proper assertion patterns
- Include cleanup handling
- Demonstrate proper test isolation
"""


def check_prompt_token_size(prompt: str) -> int:
    """Use GPT-2 to check the approximate number of tokens in a prompt.

    Args:
        prompt: The text prompt to tokenize

    Returns:
        int: Number of tokens in the prompt
    """
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    print(f"tokenizer: {tokenizer}")
    print(f"tokenizer type: {type(tokenizer)}")
    tokens = tokenizer.encode(prompt, add_special_tokens=False)
    print(f"tokens: {tokens}")
    print(f"tokens type: {type(tokens)}")
    return len(tokens)


async def arequest_message(
    system_prompt: str, messages: list[dict[str, str]]
) -> anthropic.types.Message:
    """Send a message to Anthropic API asynchronously.

    Args:
        system_prompt: The system prompt to use
        messages: List of message dictionaries with role and content

    Returns:
        anthropic.types.Message: The API response message

    Raises:
        anthropic.APIError: If the API request fails
        anthropic.APIConnectionError: If connection to API fails
        anthropic.AuthenticationError: If authentication fails
        anthropic.RateLimitError: If rate limit is exceeded
        anthropic.APIStatusError: If API returns an error status
    """
    logger.info("Sending message to Anthropic API", num_messages=len(messages))

    try:
        response = await ASYNC_CLIENT.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            messages=messages,
            max_tokens=4096,
        )

        logger.info(
            "Received response from Anthropic API",
            message_id=response.id,
            model=response.model,
            stop_reason=response.stop_reason,
            usage=response.usage,
        )
        logger.debug(
            "Response details",
            message_id=response.id,
            model=response.model,
            content=response.content,
            role=response.role,
            type=response.type,
        )

        return response

    except (
        anthropic.APIError,
        anthropic.APIConnectionError,
        anthropic.AuthenticationError,
        anthropic.RateLimitError,
        anthropic.APIStatusError,
    ) as e:
        logger.error(
            "Anthropic API request failed",
            error=str(e),
            error_type=type(e).__name__,
            messages=messages,
        )
        raise


def request_message(
    system_prompt: str, messages: list[dict[str, str]]
) -> anthropic.types.Message:
    """Send message to Anthropic synchronously.

    Args:
        system_prompt: The system prompt to use for the message
        messages: List of message dictionaries containing role and content

    Returns:
        anthropic.types.Message: Response from the Anthropic API

    Raises:
        anthropic.APIError: If the API request fails
        anthropic.APIConnectionError: If connection to API fails
        anthropic.AuthenticationError: If authentication fails
        anthropic.RateLimitError: If rate limit is exceeded
        anthropic.APIStatusError: If API returns an error status
    """
    logger.info("Sending message to Anthropic API", num_messages=len(messages))

    try:
        response: AnthropicMessage = CLIENT.messages.create(
            model=aiosettings.ai_docs_model,
            system=system_prompt,
            max_tokens=4096,
            messages=messages,
        )

        logger.info(
            "Received response from Anthropic API",
            message_id=response.id,
            model=response.model,
            stop_reason=response.stop_reason,
            usage=response.usage,
        )
        logger.debug(
            "Response details",
            message_id=response.id,
            model=response.model,
            content=response.content,
            role=response.role,
            type=response.type,
        )

        return response

    except (
        anthropic.APIError,
        anthropic.APIConnectionError,
        anthropic.AuthenticationError,
        anthropic.RateLimitError,
        anthropic.APIStatusError,
    ) as e:
        logger.error(
            "Anthropic API request failed",
            error=str(e),
            error_type=type(e).__name__,
            messages=messages,
        )
        raise


def read_file(file_path: str) -> str | None:
    """Read the text file containing the repo content.

    Args:
        file_path: Path to the file to read

    Returns:
        Optional[str]: Contents of the file if it exists, None otherwise

    Raises:
        FileNotFoundError: If the file does not exist
    """
    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as file:
            repo_content = file.read()
            return repo_content
    else:
        print("Error: The file does not exist.")
        raise FileNotFoundError(f"File not found: {file_path}")


def _generate_docs(file_path: str) -> None:
    """Generate docs for the provided repo using Claude Opus.

    Args:
        file_path: Path to the file containing repository content

    Raises:
        SystemExit: If user chooses not to proceed with doc generation
        FileNotFoundError: If the input file does not exist
    """
    repo_name = str(os.path.splitext(os.path.basename(file_path))[0]).replace(
        "_code", ""
    )
    file_content = read_file(file_path)
    input_prompt = f"Given this repo. \n{file_content}\ncomplete your instruction"
    token_size = check_prompt_token_size(input_prompt)

    proceed_check = input(
        f"Input token size is: {token_size}. Do you wish to proceed? (Y/N)"
    )
    if str(proceed_check).upper() != "Y":
        print("Exiting")
        sys.exit(1)

    messages = [
        {"role": "user", "content": input_prompt},
    ]
    response: AnthropicMessage = request_message(BASIC_DOCS_SYSTEM_PROMPT, messages)

    message = response.content[0].text
    with open(f"{repo_name}-docs.md", "w", encoding="utf-8") as file:
        file.write(message)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python api.py <txt file path>")
        sys.exit(1)

    _generate_docs(sys.argv[1])
