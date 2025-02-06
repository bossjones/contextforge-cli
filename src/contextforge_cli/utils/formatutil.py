"""A set of functions to format text."""

# SOURCE: https://github.com/CrosswaveOmega/NikkiBot/blob/main/utility/formatutil.py
from __future__ import annotations

import os
import re
from typing import Any

import aiohttp
from langchain_text_splitters import CharacterTextSplitter
from PyPDF2 import PdfReader

bar_emoji = {
    "1e": "<a:emptyleft:1118209186917011566>",
    "1h": "<a:halfleft:1118209195683094639>",
    "1f": "<a:fullleft:1118209191845318806>",
    "e": "<a:emptymiddle:1118209505973522584>",
    "h": "<a:halfmiddle:1118209197486645269>",
    "f": "<a:fullmiddle:1118209193221029982>",
    "2e": "<a:emptyright:1118209190553460866>",
    "2h": "<a:halfright:1118209198967238716>",
    "2f": "<a:fullright:1118209194257031230>",
}


def chunk_list(sentences: list[Any], chunk_size: int = 10) -> list[list[str]]:
    """
    Summary:
    Chunk a list into blocks of a specified size. Chunk list into blocks of 10.

    Explanation:
    This function takes a list of 'sentences' and divides it into blocks of size 'chunk_size'. It returns a list of lists where each inner list contains a chunk of sentences based on the specified chunk size.

    Args:
    ----
    - sentences (List[Any]): The list of items to be chunked.
    - chunk_size (int): The size of each chunk. Default is 10.

    Returns:
    -------
    - List[List[str]]: A list of lists where each inner list represents a chunk of sentences.

    """
    return [sentences[i : i + chunk_size] for i in range(0, len(sentences), chunk_size)]


def progress_bar(current: int, total: int, width: int = 5):
    """Print a progress bar."""
    current = min(current, total)
    # if current > total:
    #     current = total
    fraction = float(current / total)
    filled_width = int(fraction * width)
    half_width = int(fraction * width * 2) % 2
    empty_width = width - filled_width - half_width
    bar = f"{'f' * filled_width}{'h' * half_width}{'e' * empty_width}"
    if len(bar) <= 1:
        return f"{bar_emoji['1e']}{bar_emoji['2e']}"
    middle = "".join(bar_emoji[i] for i in bar[1:-1])
    return f"{bar_emoji[f'1{bar[0]}']}{middle}{bar_emoji[f'2{bar[-1]}']}"


# https://github.com/darren-rose/DiscordDocChatBot/blob/63a2f25d2cb8aaace6c1a0af97d48f664588e94e/main.py#L28
def extract_url(s: str):
    # Regular expression to match URLs
    """
    Summary:
    Extract URLs from a given string.

    Explanation:
    This function uses a regular expression pattern to extract URLs from the input string 's'. It then returns a list of URLs found in the string.

    Args:
    ----
    - s (str): The input string from which URLs need to be extracted.

    Returns:
    -------
    - List[str]: A list of URLs extracted from the input string.

    """
    url_pattern = re.compile(
        r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    return re.findall(url_pattern, s)


async def download_html(url: str, filepath: str):
    """
    Summary:
    Download HTML content from a URL and save it to a file.

    Explanation:
    This asynchronous function downloads the HTML content from the specified URL using a GET request. It then writes the HTML content to the file specified by 'filepath'. If the GET request is unsuccessful, it prints an error message.

    Args:
    ----
    - url (str): The URL from which to download the HTML content.
    - filepath (str): The file path where the HTML content will be saved.

    Returns:
    -------
    - None

    """
    # Send a GET request to the URL
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # Check that the GET request was successful
            if response.status == 200:
                # Write the response content (the HTML) to a file
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(response.text)
            else:
                print(f"Failed to download {url}: status code {response.status}")


def get_pdf_text(path: str):
    # define the path
    """
    Summary:
    Extract text content from PDF files in a specified directory.

    Explanation:
    This function iterates through the files in the provided directory 'path' and extracts text content from PDF files. It reads each PDF file, extracts text from each page, and concatenates the text from all pages into a single string that is returned.

    Args:
    ----
    - path (str): The directory path containing the PDF files to extract text from.

    Returns:
    -------
    - str: The concatenated text content extracted from all PDF files in the directory.

    """
    for filename in os.listdir(path):
        # check if the file is a pdf
        if filename.endswith(".pdf"):
            text = ""
            with open(os.path.join(path, filename), "rb") as pdf_doc:
                pdf_reader = PdfReader(pdf_doc)
                for page in pdf_reader.pages:
                    text += page.extract_text()
                # os.remove(os.path.join(path, filename))
            return text


def get_text_chunks(text: str):
    """
    Summary:
    Split text into chunks based on specified parameters.

    Explanation:
    This function takes a text input and splits it into chunks using a CharacterTextSplitter object with defined parameters such as separator, chunk size, chunk overlap, and length function. It returns a list of text chunks based on the splitting criteria.

    Args:
    ----
    - text (str): The input text to be split into chunks.

    Returns:
    -------
    - List[str]: A list of text chunks split based on the specified parameters.

    """
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len
    )
    return text_splitter.split_text(text)
