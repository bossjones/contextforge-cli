#!/usr/bin/env python3

# SOURCE: https://claude.ai/chat/6f981f76-5f20-450d-b2cc-7cef1f55ab1a
"""
The enhanced script now:

Uses a highly structured prompt template optimized for Claude 3.5 Sonnet
Includes clear XML tag guidelines
Provides explicit instructions for formatting and style
Allows customization through external style guides
Maintains consistent technical documentation standards

The output will be more structured, detailed, and aligned with best practices for technical documentation. Claude 3.5 Sonnet will use the XML tags consistently and provide thorough analysis with concrete examples.
Would you like me to explain any part in more detail or make additional enhancements to the script?


Example usage:

python expert_def_generator.py https://github.com/langchain-ai/langgraph \
    --version 0.2.61 \
    --files Dockerfile langgraph.json \
    --prompt "Analyze these configuration files for best practices and implementation patterns" \
    --output-dir ai_docs/prompts/data \
    --style custom_style.json \
    --verbose
"""

# ----------------

"""
Expert Definition Generator Script

This script automates the process of generating expert definitions from repository files
by combining the functionality of files-to-prompt and llm tools. It's specifically
optimized for use with Claude 3.5 Sonnet and implements best practices for prompt
engineering and documentation generation.

The script handles:
- Repository cloning and version management
- File analysis using files-to-prompt
- Structured prompt generation with XML tags
- Expert definition generation using llm
- Custom style guide integration
"""

import argparse
import json
import logging
import subprocess
import os
import sys
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExpertDefinitionGenerator:
    """
    A class to handle the generation of expert definitions from repository files.
    This provides a more organized way to manage the generation process and its dependencies.
    """

    def check_dependencies(self):
        """
        Verify that required external tools are installed.

        This function checks for the presence of fzf and bat, which are needed
        for interactive file selection and preview functionality. If any tool
        is missing, it provides installation instructions.

        Raises:
            SystemExit: If required dependencies are not found
        """
        missing_deps = []

        # Check for fzf
        try:
            self.run_command("which fzf")
        except subprocess.CalledProcessError:
            missing_deps.append("fzf")

        # Check for bat
        try:
            self.run_command("which bat")
        except subprocess.CalledProcessError:
            # On some systems, bat is installed as batcat
            try:
                self.run_command("which batcat")
            except subprocess.CalledProcessError:
                missing_deps.append("bat")

        if missing_deps:
            logger.error("Missing required dependencies: " + ", ".join(missing_deps))
            logger.error("\nPlease install the missing dependencies:")
            logger.error("  macOS: brew install " + " ".join(missing_deps))
            logger.error("  Ubuntu/Debian: sudo apt install " + " ".join(missing_deps))
            logger.error("  Other Linux: Use your distribution's package manager")
            sys.exit(1)

    def __init__(self, output_dir: str, style_guide: dict | None = None):
        """
        Initialize the generator with output directory and optional style guide.

        Args:
            output_dir: Directory where generated files will be saved
            style_guide: Optional dictionary containing custom style preferences
        """
        self.output_dir = Path(output_dir)
        self.style_guide = style_guide or {}
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.check_dependencies()

    def run_command(self, command: str) -> str:
        """
        Execute a shell command and return its output.

        Args:
            command: Shell command to execute

        Returns:
            Command output as string

        Raises:
            subprocess.CalledProcessError: If command execution fails
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing command: {command}")
            logger.error(f"Error output: {e.stderr}")
            raise

    def generate_xml_filename(self, repo_name: str, files: list[str]) -> str:
        """
        Generate a consistent filename for the XML output.

        Args:
            repo_name: Name of the repository
            files: List of files being analyzed

        Returns:
            Generated filename
        """
        base_name = '_'.join(files)
        if len(base_name) > 30:  # Truncate if too long
            base_name = base_name[:30]
        return f"{repo_name}_{base_name}.xml"

    def create_expert_prompt(self, xml_content: str, custom_prompt: str) -> str:
        """
        Create an enhanced expert definition prompt optimized for Claude 3.5 Sonnet.

        Args:
            xml_content: XML content from files-to-prompt
            custom_prompt: User-provided prompt for analysis

        Returns:
            Formatted prompt string
        """
        # Incorporate any custom tags from style guide
        custom_tags = self.style_guide.get('tags', {}).get('custom_tags', [])
        custom_tag_str = '\n'.join([f"- Use <{tag}> tags for {tag}-related information"
                                   for tag in custom_tags])

        prompt_template = f"""<system>
You are Claude 3.5 Sonnet, an expert at analyzing code, documentation, and technical specifications. You excel at providing detailed, well-structured analysis while maintaining clear organization through XML tags. Your responses should be thorough, educational, and precisely formatted.
</system>

<context>
The following documents contain source code and configuration files that need expert analysis. The analysis should help developers understand and implement best practices.
</context>

<documents>
{xml_content}
</documents>

<instructions>
1. Analyze the provided documents thoroughly, paying special attention to patterns, best practices, and implementation details.
2. Structure your response using clear XML tags to separate different types of information.
3. When providing analysis, include specific examples from the source code to support your points.
4. Consider both explicit statements and implicit patterns in the code.
5. Focus on actionable insights that developers can implement.
6. Maintain a clear, educational tone appropriate for technical documentation.
</instructions>

<task>
{custom_prompt}
</task>

<output_format>
Your response should use the following XML structure:
- Use <quotes> tags for relevant excerpts from the source
- Use <info> tags for analytical insights and recommendations
- Use <examples> tags when providing concrete examples
- Use <best_practices> tags when summarizing recommended approaches
- Use <implementation> tags when discussing specific implementation details
{custom_tag_str}
</output_format>

<style_preferences>
- Write in clear, professional prose
- Use complete sentences and proper technical terminology
- Provide detailed explanations with concrete examples
- Include relevant context to support understanding
- Structure information logically and hierarchically
{self.style_guide.get('preferences', {}).get('additional_preferences', '')}
</style_preferences>"""
        return prompt_template

    def get_files_from_directory(self, directory: Path, base_dir: Path) -> list[str]:
        """
        Use fzf to interactively select files from a directory.

        Args:
            directory: Directory to search for files
            base_dir: Base directory for relative paths

        Returns:
            List of selected file paths relative to base_dir
        """
        try:
            # Get all files recursively in the directory
            all_files = []
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(base_dir)
                    all_files.append(str(relative_path))

            # Write files to temporary file for fzf
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as temp_file:
                temp_file.write('\n'.join(all_files))
                temp_file.flush()

                try:
                    # Run fzf for file selection with improved preview
                    preview_cmd = (
                        'bat --color=always --style=numbers --line-range :500 {} 2>/dev/null || '
                        'tree -C {} 2>/dev/null || '
                        'echo "No preview available for {}"'
                    )
                    result = self.run_command(
                        f'cat {temp_file.name} | fzf --multi '
                        f'--preview "cd {base_dir} && {preview_cmd}" '
                        '--preview-window=right:60%:wrap '
                        '--bind="ctrl-/:change-preview-window(down|hidden|)" '
                        '--header="TAB to select multiple files, ENTER to confirm, CTRL-/ to toggle preview"'
                    )
                    selected_files = [line.strip() for line in result.splitlines() if line.strip()]
                    return selected_files
                except subprocess.CalledProcessError:
                    logger.error("Error running fzf. Make sure it's installed: brew install fzf bat")
                    sys.exit(1)
        except Exception as e:
            logger.error(f"Error during file selection: {e}")
            sys.exit(1)

    def validate_files(self, files: list[str], base_dir: Path) -> list[str]:
        """
        Validate that all specified files exist and are accessible.

        This function checks each file path to ensure it exists and is readable
        before proceeding with the analysis. It handles both individual files
        and directories.

        Args:
            files: List of file paths to validate
            base_dir: Base directory for relative paths

        Returns:
            List of validated file paths

        Raises:
            FileNotFoundError: If any specified file cannot be found
            PermissionError: If any file cannot be accessed
        """
        validated_files = []
        for file_path in files:
            full_path = base_dir / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            if not os.access(full_path, os.R_OK):
                raise PermissionError(f"Cannot read file: {file_path}")
            validated_files.append(file_path)
        return validated_files

    def generate_definition(self, repo_url: str, version: str | None,
                          files: list[str], prompt: str) -> tuple[str, str]:
        """
        Generate the expert definition from repository files.

        Args:
            repo_url: URL of the repository
            version: Optional version/tag to checkout
            files: List of files to analyze
            prompt: Custom prompt for expert definition

        Returns:
            Tuple of (xml_path, expert_def_path)
        """
        repo_name = repo_url.split('/')[-1].replace('.git', '')

        with tempfile.TemporaryDirectory() as temp_dir:
            logger.info(f"Created temporary directory: {temp_dir}")

            # Clone repository
            clone_cmd = f"git clone {repo_url} {temp_dir}"
            self.run_command(clone_cmd)

            # Checkout specific version if provided
            if version:
                checkout_cmd = f"cd {temp_dir} && git checkout {version}"
                self.run_command(checkout_cmd)

            temp_dir_path = Path(temp_dir)

            # Validate input files
            try:
                files = self.validate_files(files, temp_dir_path)
            except (FileNotFoundError, PermissionError) as e:
                logger.error(f"File validation error: {e}")
                sys.exit(1)

            # Generate XML filename and paths
            xml_filename = self.generate_xml_filename(repo_name, files)
            xml_path = self.output_dir / xml_filename
            expert_def_path = xml_path.with_suffix('.md')

            # Process files and handle directories
            final_files = []
            temp_dir_path = Path(temp_dir)

            for file_path in files:
                path = temp_dir_path / file_path
                if path.is_dir():
                    logger.info(f"\nDirectory detected: {file_path}")
                    logger.info("Please select files using fzf (press TAB to select multiple, ENTER to confirm):")
                    selected_files = self.get_files_from_directory(path, temp_dir_path)
                    final_files.extend(selected_files)
                else:
                    final_files.append(file_path)

            if not final_files:
                logger.error("No files selected for analysis")
                sys.exit(1)

            # Generate XML using files-to-prompt
            files_str = ' '.join(final_files)
            files_to_prompt_cmd = f"cd {temp_dir} && uv run files-to-prompt {files_str} --cxml -o {xml_path}"
            self.run_command(files_to_prompt_cmd)

            # Read the generated XML
            xml_content = xml_path.read_text()

            # Create the expert definition prompt
            expert_prompt = self.create_expert_prompt(xml_content, prompt)

            # Use llm to generate the expert definition
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as temp_prompt:
                temp_prompt.write(expert_prompt)
                temp_prompt.flush()

                llm_cmd = f'cat {temp_prompt.name} | llm > "{expert_def_path}"'
                self.run_command(llm_cmd)

            return str(xml_path), str(expert_def_path)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Generate expert definitions from repository files',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('repo_url', help='GitHub repository URL')
    parser.add_argument('--version', help='Repository version/tag to checkout')
    parser.add_argument('--files', nargs='+', help='Files to analyze', required=True)
    parser.add_argument('--prompt', help='Custom prompt for expert definition', required=True)
    parser.add_argument('--output-dir', help='Output directory', default='ai_docs/prompts/data')
    parser.add_argument('--style', help='Path to custom style guide JSON file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Load custom style guide if provided
    style_guide = {}
    if args.style:
        try:
            with open(args.style) as f:
                style_guide = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load style guide: {e}")
            logger.warning("Using default style guide")

    # Initialize and run generator
    generator = ExpertDefinitionGenerator(args.output_dir, style_guide)
    try:
        xml_path, expert_def_path = generator.generate_definition(
            args.repo_url,
            args.version,
            args.files,
            args.prompt
        )
        logger.info("\nExpert definition generated successfully!")
        logger.info(f"XML output: {xml_path}")
        logger.info(f"Expert definition: {expert_def_path}")
    except Exception as e:
        logger.error(f"Error generating expert definition: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
