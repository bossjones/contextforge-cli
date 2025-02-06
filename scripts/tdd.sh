#!/usr/bin/env bash
#
# A Bash script to run a TDD loop for building a Python module to
# pass tests.
# USAGE: ./tdd.sh <tests_file> <code_file>
# EXAMPLE: ./tdd.sh tests.py application.py

# SOURCE: https://codeinthehole.com/tips/llm-tdd-loop-script/

set -euo pipefail

# How many times to loop.
ATTEMPTS=4

# The system prompt to use when creating the initial version.
INITIAL_PROMPT="
Write a Python module that will make these tests pass
and conforms to the passed conventions"

# The system prompt to use when creating subsequent versions.
RETRY_PROMPT="Tests are failing with this output. Try again."

function main {
    tests_file=$1
    code_file=$2

    # Create a temporary file to hold the test output.
    test_output_file=$(mktemp)

    # Print the tests file.
    printf "Making these tests (in %s) pass\n\n" "$tests_file" >&2
    bat "$tests_file"

    # Create initial version of application file.
    printf "\nGenerating initial version of %s\n\n" "$code_file" >&2
    files-to-prompt "$tests_file" conventions.txt | \
        llm prompt --system "$INITIAL_PROMPT" > "$code_file"

    # Loop until tests pass or we reach the maximum number of attempts.
    for i in $(seq 2 $ATTEMPTS)
    do
        # Print generated code file for review.
        bat "$code_file" >&2

        # Pause - otherwise everything flies past too quickly. It's useful
        # to eyeball the LLM-generated code before you execute it.
        echo >&2
        read -n 1 -s -r -p "Press any key to run tests..." >&2

        # Run tests and capture output.
        if pytest "$tests_file" > "$test_output_file"; then
            # Tests passed - we're done.
            echo "✅ " >&2
            exit 0
        else
            # Tests failed - print test output...
            printf "❌\n\n" >&2
            bat "$test_output_file" >&2

            # ...and create a new version of the application file.
            printf "\nGenerating v%s of %s\n\n" "$i" "$code_file" >&2
            uv run files-to-prompt "$tests_file" conventions.txt "$test_output_file" | \
                uv run llm prompt --continue --system "$RETRY_PROMPT" > "$code_file"
        fi
    done

    # If we get here, then no version passed the tests.
    echo "Failed to make the tests pass after $ATTEMPTS attempts" >&2
    exit 1
}

main "$@"
