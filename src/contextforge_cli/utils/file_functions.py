"""contextforge_cli.file_functions"""
# pyright: reportGeneralTypeIssues=false
# pyright: reportOperatorIssue=false
# pyright: reportOptionalIterable=false

from __future__ import annotations

import glob
import json
import os
import os.path
import pathlib
import string
import sys
from typing import TYPE_CHECKING

import aiofiles
import pandas as pd
import rich
import structlog

logger = structlog.get_logger(__name__)
from rich.console import Console
from rich.table import Table

from contextforge_cli.constants import (
    FIFTY_THOUSAND,
    FIVE_HUNDRED_THOUSAND,
    MAX_BYTES_UPLOAD_DISCORD,
    ONE_HUNDRED_THOUSAND,
    ONE_MILLION,
    TEN_THOUSAND,
    THIRTY_THOUSAND,
    TWENTY_THOUSAND,
)

if TYPE_CHECKING:
    from pandas import DataFrame


PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

# https://gist.github.com/wassname/1393c4a57cfcbf03641dbc31886123b8
# python convert string to safe filename
VALID_FILENAME_CHARS = f"-_.() {string.ascii_letters}{string.digits}"
CHAR_LIMIT = 255

JSON_EXTENSIONS = [".json", ".JSON"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".MP4", ".MOV"]
AUDIO_EXTENSIONS = [".mp3", ".MP3"]
GIF_EXTENSIONS = [".gif", ".GIF"]
MKV_EXTENSIONS = [".mkv", ".MKV"]
M3U8_EXTENSIONS = [".m3u8", ".M3U8"]
WEBM_EXTENSIONS = [".webm", ".WEBM"]
IMAGE_EXTENSIONS = [".png", ".jpeg", ".jpg", ".gif", ".PNG", ".JPEG", ".JPG", ".GIF"]
TORCH_MODEL_EXTENSIONS = [".pth", ".PTH"]
PDF_EXTENSIONS = [".pdf", ".PDF"]
TXT_EXTENSIONS = [".txt", ".TXT"]


async def aio_read_jsonfile(jsonfile: str) -> dict:
    """
    Read a JSON file asynchronously.

    Args:
    ----
        jsonfile (str): Path to the JSON file.

    Returns:
    -------
        dict: Parsed JSON data.

    """
    print(f" [aio_read_jsonfile] jsonfile -> {jsonfile}")
    async with aiofiles.open(jsonfile, encoding="utf-8") as f:
        contents = await f.read()
    json_data = json.loads(contents)
    print(f" [aio_read_jsonfile] json_data -> {json_data}")
    return json_data


async def aio_json_loads(uri: str) -> dict:
    """
    Load JSON data from a file asynchronously.

    Args:
    ----
        uri (str): Path to the JSON file.

    Returns:
    -------
        dict: Parsed JSON data.

    """
    return json.loads(await (await aiofiles.open(uri)).read())


async def run_aio_json_loads(uri: str) -> dict:
    """
    Run the aio_json_loads function.

    Args:
    ----
        uri (str): Path to the JSON file.

    Returns:
    -------
        dict: Parsed JSON data.

    """
    return await aio_json_loads(uri=uri)


# SOURCE: https://stackoverflow.com/questions/168409/how-do-you-get-a-directory-listing-sorted-by-creation-date-in-python
def sort_dir_by_mtime(dirpath: str) -> list[pathlib.Path]:
    """
    Sort directory contents by modification time.

    Args:
    ----
        dirpath (str): Path to the directory.

    Returns:
    -------
        list[pathlib.Path]: List of sorted paths.

    """
    return sorted(pathlib.Path(dirpath).iterdir(), key=os.path.getmtime)


# SOURCE: https://stackoverflow.com/questions/168409/how-do-you-get-a-directory-listing-sorted-by-creation-date-in-python
def sort_dir_by_ctime(dirpath: str) -> list[pathlib.Path]:
    """
    Sort directory contents by creation time.

    Args:
    ----
        dirpath (str): Path to the directory.

    Returns:
    -------
        list[pathlib.Path]: List of sorted paths.

    """
    return sorted(pathlib.Path(dirpath).iterdir(), key=os.path.getctime)


def get_all_media_files_to_upload(tmpdirname: str) -> list[str]:
    """
    Get all media files to upload from a directory.

    Args:
    ----
        tmpdirname (str): Path to the temporary directory.

    Returns:
    -------
        list[str]: List of media file paths.

    """
    # top level function that grabs all media files
    tree_list = tree(pathlib.Path(f"{tmpdirname}"))
    rich.print(tree_list)

    file_to_upload_list = [f"{p}" for p in tree_list]
    logger.debug(
        f"get_all_media_files_to_upload -> file_to_upload_list = {file_to_upload_list}"
    )
    rich.print(file_to_upload_list)

    return filter_media(file_to_upload_list)


def filter_pth(working_dir: list[str]) -> list[str]:
    """
    Filter .pth files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of .pth file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in TORCH_MODEL_EXTENSIONS
    ]


def filter_json(working_dir: list[str]) -> list[str]:
    """
    Filter JSON files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of JSON file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in JSON_EXTENSIONS
    ]


def rename_without_cachebuster(working_dir: list[str]) -> list[str]:
    """
    Rename files to remove cache buster query parameters.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of renamed file paths.

    """
    working_dir_only = []
    for f in working_dir:
        if ("?updatedAt" in f"{f}") and (pathlib.Path(f"{f}").is_file()):
            orig = pathlib.Path(f"{f}").absolute()
            # tweetpik now adds cache buster, lets work around it
            without_cb = f"{orig}".split("?updatedAt")[0]
            orig.rename(f"{without_cb}")
            working_dir_only.append(f"{without_cb}")
    return working_dir_only


def filter_videos(working_dir: list[str]) -> list[str]:
    """
    Filter video files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of video file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in VIDEO_EXTENSIONS
    ]


def filter_audio(working_dir: list[str]) -> list[str]:
    """
    Filter audio files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of audio file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in AUDIO_EXTENSIONS
    ]


def filter_gif(working_dir: list[str]) -> list[str]:
    """
    Filter GIF files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of GIF file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in GIF_EXTENSIONS
    ]


def filter_mkv(working_dir: list[str]) -> list[str]:
    """
    Filter MKV files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of MKV file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in MKV_EXTENSIONS
    ]


def filter_m3u8(working_dir: list[str]) -> list[str]:
    """
    Filter M3U8 files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of M3U8 file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in M3U8_EXTENSIONS
    ]


def filter_webm(working_dir: list[str]) -> list[str]:
    """
    Filter WEBM files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of WEBM file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in WEBM_EXTENSIONS
    ]


def filter_images(working_dir: list[str]) -> list[str]:
    """
    Filter image files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of image file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in IMAGE_EXTENSIONS
    ]


def filter_pdfs(working_dir: list[str]) -> list[pathlib.PosixPath]:
    """
    Filter PDF files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of PDF file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in PDF_EXTENSIONS
    ]


def filter_txts(working_dir: list[str]) -> list[pathlib.PosixPath]:
    """
    Filter TXT files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of TXT file paths.

    """
    return [
        f
        for f in working_dir
        if (pathlib.Path(f"{f}").is_file())
        and pathlib.Path(f"{f}").suffix.lower() in TXT_EXTENSIONS
    ]


def filter_media(working_dir: list[str]) -> list[str]:
    """
    Filter image and video files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of image and video file paths.

    """
    imgs = filter_images(working_dir)
    videos = filter_videos(working_dir)
    return imgs + videos


def filter_pdf(working_dir: list[str]) -> list[pathlib.PosixPath]:
    """
    Filter PDF files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of PDF file paths.

    """
    return filter_pdfs(working_dir)


def get_dataframe_from_csv(
    filename: str, return_parent_folder_name: bool = False
) -> DataFrame | tuple[DataFrame, str]:
    """
    Open a CSV file and return a DataFrame.

    Args:
    ----
        filename (str): Path to the CSV file.
        return_parent_folder_name (bool, optional): Whether to return the parent folder name. Defaults to False.

    Returns:
    -------
        DataFrame | tuple[DataFrame, str]: DataFrame or tuple of DataFrame and parent folder name.

    """
    """Open csv files and return a dataframe from pandas

    Args:
        filename (str): path to file
    """
    src: pathlib.Path = pathlib.Path(f"{filename}").resolve()
    df: DataFrame = pd.read_csv(f"{src}")

    # import bpdb
    # bpdb.set_trace()

    return (df, f"{src.parent.stem}") if return_parent_folder_name else df


def sort_dataframe(
    df: DataFrame, columns: list[str] | None = None, ascending: tuple[bool, ...] = ()
) -> DataFrame:
    """
    Sort a DataFrame by specified columns.

    Args:
    ----
        df (DataFrame): DataFrame to sort.
        columns (list[str], optional): Columns to sort by. Defaults to None.
        ascending (tuple[bool, ...], optional): Sort order for each column. Defaults to ().

    Returns:
    -------
        DataFrame: Sorted DataFrame.

    """
    """Return dataframe sorted via columns

    Args:
        df (DataFrame): existing dataframe
        columns (list, optional): [description]. Defaults to []. Eg. ["Total Followers", "Total Likes", "Total Comments", "ERDay", "ERpost"]
        ascending (Tuple, optional): [description]. Defaults to (). Eg. (False, False, False, False, False)

    Returns:
        DataFrame: [description]
    """
    if columns is None:
        columns = []  # type: ignore
    df = df.sort_values(by=columns, ascending=list(ascending))
    return df


def rich_format_followers(val: int) -> str:
    """
    Format follower count with rich text.

    Args:
    ----
        val (int): Follower count.

    Returns:
    -------
        str: Formatted follower count.

    """
    """Given a arbritary int, return a 'rich' string formatting

    Args:
        val (int): eg. followers = 4366347347457

    Returns:
        str: [description] eg. "[bold bright_yellow]4366347347457[/bold bright_yellow]"
    """

    if val > ONE_MILLION:
        return f"[bold bright_yellow]{val}[/bold bright_yellow]"
    elif FIVE_HUNDRED_THOUSAND < val < ONE_MILLION:
        return f"[bold dark_orange]{val}[/bold dark_orange]"
    elif ONE_HUNDRED_THOUSAND < val < FIVE_HUNDRED_THOUSAND:
        return f"[bold orange_red1]{val}[/bold orange_red1]"

    elif FIFTY_THOUSAND < val < ONE_HUNDRED_THOUSAND:
        return f"[bold dodger_blue2]{val}[/bold dodger_blue2]"
    elif THIRTY_THOUSAND < val < FIFTY_THOUSAND:
        return f"[bold purple3]{val}[/bold purple3]"
    elif TWENTY_THOUSAND < val < THIRTY_THOUSAND:
        return f"[bold rosy_brown]{val}[/bold rosy_brown]"
    elif TEN_THOUSAND < val < TWENTY_THOUSAND:
        return f"[bold green]{val}[/bold green]"
    else:
        return f"[bold bright_white]{val}[/bold bright_white]"


def rich_likes_or_comments(val: int) -> str:
    """
    Format likes or comments count with rich text.

    Args:
    ----
        val (int): Likes or comments count.

    Returns:
    -------
        str: Formatted likes or comments count.

    """
    """Given a arbritary int, return a 'rich' string formatting

    Args:
        val (int): eg. followers = 4366347347457

    Returns:
        str: [description] eg. "[bold bright_yellow]4366347347457[/bold bright_yellow]"
    """

    if val <= TEN_THOUSAND:
        return f"[bold bright_yellow]{val}[/bold bright_yellow]"
    elif FIFTY_THOUSAND < val < ONE_HUNDRED_THOUSAND:
        return f"[bold dodger_blue2]{val}[/bold dodger_blue2]"
    elif THIRTY_THOUSAND < val < FIFTY_THOUSAND:
        return f"[bold purple3]{val}[/bold purple3]"
    elif TWENTY_THOUSAND < val < THIRTY_THOUSAND:
        return f"[bold rosy_brown]{val}[/bold rosy_brown]"
    elif TEN_THOUSAND < val < TWENTY_THOUSAND:
        return f"[bold green]{val}[/bold green]"
    else:
        return f"[bold bright_white]{val}[/bold bright_white]"


def rich_display_meme_pull_list(df: DataFrame) -> None:
    """
    Display meme pull list in a rich table format.

    Args:
    ----
        df (DataFrame): DataFrame containing meme pull list data.

    """
    console = Console()

    table = Table(show_header=True, header_style="bold magenta")

    table.add_column("Account")
    table.add_column("Social")
    table.add_column("Total Followers")
    table.add_column("Total Likes")
    table.add_column("Total Comments")
    table.add_column("Total Posts")
    table.add_column("Start Date")
    table.add_column("End Date")
    table.add_column("ERDay")
    table.add_column("ERpost")
    table.add_column("Average Likes")
    table.add_column("Average Comments")
    table.add_column("Links")

    for _index, row in df.iterrows():
        account = f"[bold blue]{row['Account']}[/bold blue]"
        social = f"[bold]{row['Social']}[/bold]"
        total_followers = rich_format_followers(row["Total Followers"])
        total_likes = f"[bold]{row['Total Likes']}[/bold]"
        total_comments = f"[bold]{row['Total Comments']}[/bold]"
        total_posts = f"[bold]{row['Total Posts']}[/bold]"
        start_date = f"[bold]{row['Start Date']}[/bold]"
        end_date = f"[bold]{row['End Date']}[/bold]"
        erday = f"[bold]{row['ERDay']}[/bold]"
        erpost = f"[bold]{row['ERpost']}[/bold]"
        average_likes = f"[bold]{row['Average Likes']}[/bold]"
        average_comments = f"[bold]{row['Average Comments']}[/bold]"
        links = f"[bold]{row['Links']}[/bold]"

        table.add_row(
            account,
            social,
            total_followers,
            total_likes,
            total_comments,
            total_posts,
            start_date,
            end_date,
            erday,
            erpost,
            average_likes,
            average_comments,
            links,
        )

    console.print(table)


def rich_display_popstars_analytics(df: DataFrame) -> None:
    """
    Display popstars analytics in a rich table format.

    Args:
    ----
        df (DataFrame): DataFrame containing popstars analytics data.

    """
    console = Console()

    table = Table(show_header=True, header_style="bold magenta")

    table.add_column("Social")
    table.add_column("Author")
    table.add_column("Url")
    table.add_column("Likes")
    table.add_column("Comments")
    table.add_column("ER")
    table.add_column("Text")
    table.add_column("Date")
    table.add_column("Media 1")

    for _index, row in df.iterrows():
        social = f"[bold]{row['Social']}[/bold]"
        author = f"[bold]{row['Author']}[/bold]"
        url = f"[bold]{row['Url']}[/bold]"
        likes = f"[bold]{rich_likes_or_comments(row['Likes'])}[/bold]"
        comments = f"[bold]{rich_likes_or_comments(row['Comments'])}[/bold]"
        er = f"[bold]{row['ER']}[/bold]"
        text = f"[bold]{row['Text']}[/bold]"
        date = f"[bold]{row['Date']}[/bold]"
        media = f"[bold]{row['Media 1']}[/bold]"

        table.add_row(social, author, url, likes, comments, er, text, date, media)

    console.print(table)


def glob_file_by_extension(
    working_dir: str, extension: str = "*.mp4", recursive: bool = False
) -> list[str]:
    """
    Find files by extension using glob.

    Args:
    ----
        working_dir (str): Directory to search in.
        extension (str, optional): File extension to search for. Defaults to "*.mp4".
        recursive (bool, optional): Whether to search recursively. Defaults to False.

    Returns:
    -------
        list[str]: List of file paths.

    """
    print(f"Searching dir -> {working_dir}/{extension}")

    if recursive:
        # NOTE: When recursive is set True "**"" followed by path separator('./**/') will match any files or directories.
        expression = f"{working_dir}/**/{extension}"
    else:
        expression = f"{working_dir}/{extension}"
    return glob.glob(expression, recursive=recursive)


def print_and_append(
    dir_listing: list[str], tree_str: str, silent: bool = False
) -> None:
    """
    Print and append directory listing.

    Args:
    ----
        dir_listing (list[str]): List to append to.
        tree_str (str): String to print and append.
        silent (bool, optional): Whether to suppress printing. Defaults to False.

    """
    if not silent:
        print(tree_str)
    dir_listing.append(tree_str)


def tree(directory: str | pathlib.Path, silent: bool = False) -> list[pathlib.Path]:
    """
    Generate a tree structure of a directory.

    Args:
    ----
        directory (pathlib.Path): Path to the directory.
        silent (bool, optional): Whether to suppress printing. Defaults to False.

    Returns:
    -------
        list[pathlib.Path]: List of file paths in the directory.

    """
    logger.debug(f"directory -> {directory}")
    if isinstance(directory, str):
        directory = fix_path(directory)
        logger.debug(f"directory -> {directory}")
        directory = pathlib.Path(directory)
        logger.debug(f"directory -> {directory}")
    try:
        assert directory.is_dir()
    except:
        raise OSError(f"{directory} is not a directory.")

    # from ffmpeg_tools import fileobject
    file_system: list[pathlib.Path]
    file_system = []
    _tree = []
    print_and_append(_tree, f"+ {directory}", silent=silent)
    for path in sorted(directory.rglob("*")):
        file_system.append(pathlib.Path(f"{path.resolve()}"))
        try:
            depth = len(path.resolve().relative_to(directory.resolve()).parts)
        except ValueError:
            continue
        spacer = "    " * depth
        print_and_append(_tree, f"{spacer}+ {path.name}", silent=silent)

    return sorted(file_system, key=os.path.getmtime)


# SOURCE: https://python.hotexamples.com/site/file?hash=0xda3708e60cd1ddb3012abd7dba205f48214aee7366f452e93807887c6a04db42&fullName=spring_cleaning.py&project=pambot/SpringCleaning
def format_size(a_file: int) -> str:
    """
    Format file size in human-readable format.

    Args:
    ----
        a_file (int): File size in bytes.

    Returns:
    -------
        str: Formatted file size.

    """
    if a_file >= 1024**3:
        return f"{a_file / float(1024**3):.2f} GB"
    elif a_file >= 1024**2:
        return f"{a_file / float(1024**2):.2f} MB"
    elif a_file >= 1024:
        return f"{a_file / float(1024):.2f} KB"
    else:
        return f"{a_file:.0f} B"


async def aiowrite_file(
    data: str, dl_dir: str = "./", fname: str = "", ext: str = ""
) -> None:
    """
    Write data to a file asynchronously.

    Args:
    ----
        data (str): Data to write.
        dl_dir (str, optional): Directory to write to. Defaults to "./".
        fname (str, optional): File name. Defaults to "".
        ext (str, optional): File extension. Defaults to "".

    """
    p_dl_dir = pathlib.Path(dl_dir)
    full_path_dl_dir = f"{p_dl_dir.absolute()}"
    p_new = pathlib.Path(f"{full_path_dl_dir}/{fname}.{ext}")
    logger.debug(f"Writing to {p_new.absolute()}")
    async with aiofiles.open(p_new.absolute(), mode="w") as f:
        await f.write(data)
    # await logger.complete()


async def aioread_file(dl_dir: str = "./", fname: str = "", ext: str = "") -> str:
    """
    Read data from a file asynchronously.

    Args:
    ----
        dl_dir (str, optional): Directory to read from. Defaults to "./".
        fname (str, optional): File name. Defaults to "".
        ext (str, optional): File extension. Defaults to "".

    Returns:
    -------
        str: The content of the file.

    """
    p_dl_dir = pathlib.Path(dl_dir)
    full_path_dl_dir = f"{p_dl_dir.absolute()}"
    p_new = pathlib.Path(f"{full_path_dl_dir}/{fname}.{ext}")
    logger.debug(f"Reading from {p_new.absolute()}")
    async with aiofiles.open(p_new.absolute()) as f:
        content = await f.read()
    # await logger.complete()
    return content


def check_file_size(a_file: str) -> tuple[bool, str]:
    """
    Check if a file size exceeds the maximum allowed size.

    Args:
    ----
        a_file (str): Path to the file.

    Returns:
    -------
        tuple[bool, str]: Tuple containing a boolean indicating if the file size exceeds the limit and a message.

    """
    p = pathlib.Path(a_file)
    file_size = p.stat().st_size
    logger.debug(
        f"File: {p} | Size(bytes): {file_size} | Size(type): {type(file_size)}"
    )
    check = file_size > MAX_BYTES_UPLOAD_DISCORD
    msg = f"Is file size greater than {MAX_BYTES_UPLOAD_DISCORD}: {check}"
    logger.debug(msg)
    return check, msg


# ------------------------------------------------------------
# NOTE: MOVE THIS TO A FILE UTILITIES LIBRARY
# ------------------------------------------------------------
# SOURCE: https://github.com/tgbugs/pyontutils/blob/05dc32b092b015233f4a6cefa6c157577d029a40/ilxutils/tools.py
def is_file(path: str) -> bool:
    """
    Check if a path points to a file.

    Args:
    ----
        path (str): Path to check.

    Returns:
    -------
        bool: True if the path points to a file, False otherwise.

    """
    """Check if path contains a file

    Args:
        path (_type_): _description_

    Returns:
        _type_: _description_
    """
    return pathlib.Path(path).is_file()


def is_directory(path: str) -> bool:
    """
    Check if a path points to a directory.

    Args:
    ----
        path (str): Path to check.

    Returns:
    -------
        bool: True if the path points to a directory, False otherwise.

    """
    """Check if path contains a dir

    Args:
        path (str): _description_

    Returns:
        _type_: _description_
    """
    return pathlib.Path(path).is_dir()


def is_a_symlink(path: str) -> bool:
    """
    Check if a path points to a symlink.

    Args:
    ----
        path (str): Path to check.

    Returns:
    -------
        bool: True if the path points to a symlink, False otherwise.

    """
    """Check if path contains a dir

    Args:
        path (str): _description_

    Returns:
        _type_: _description_
    """
    return pathlib.Path(path).is_symlink()


def expand_path_str(path: str) -> pathlib.Path:
    """
    Expand a path string to a full path.

    Args:
    ----
        path (str): Path string to expand.

    Returns:
    -------
        pathlib.Path: Expanded path.

    """
    """_summary_

    Args:
        path (str): _description_

    Returns:
        pathlib.PosixPath: _description_
    """
    return pathlib.Path(tilda(path))


def tilda(obj: str | list[str]) -> str | list[str]:
    """
    Expand tilde to home directory in a path.

    Args:
    ----
        obj (str | list[str]): Path string or list of path strings.

    Returns:
    -------
        str | list[str]: Expanded path string or list of expanded path strings.

    """
    """wrapper for linux ~/ shell notation

    Args:
        obj (_type_): _description_

    Returns:
        _type_: _description_
    """
    if isinstance(obj, list):
        return [
            str(pathlib.Path(o).expanduser()) if isinstance(o, str) else o for o in obj
        ]
    elif isinstance(obj, str):
        return str(pathlib.Path(obj).expanduser())
    else:
        return obj


def fix_path(path: str) -> str | list[str]:
    """
    Automatically convert path to fully qualified file URI.

    Args:
    ----
        path (str): Path string to fix.

    Returns:
    -------
        str | list[str]: Fixed path string or list of fixed path strings.

    """

    def __fix_path(path):
        if not isinstance(path, str):
            return path
        elif path[0] == "~":
            tilda_fixed_path = tilda(path)
            if is_file(tilda_fixed_path):
                return tilda_fixed_path
            else:
                exit(path, ": does not exit.")
        elif is_file(pathlib.Path.home() / path) or is_directory(
            pathlib.Path.home() / path
        ):
            return str(pathlib.Path().home() / path)
        else:
            return path

    if isinstance(path, str):
        return __fix_path(path)
    elif isinstance(path, list):
        return [__fix_path(p) for p in path]
    else:
        return path


def unlink_orig_file(a_filepath: str) -> str:
    """
    _summary_

    Args:
    ----
        a_filepath (str): _description_

    Returns:
    -------
        _type_: _description_

    """
    logger.debug(f"deleting ... {a_filepath}")
    rich.print(f"deleting ... {a_filepath}")
    os.unlink(f"{a_filepath}")
    return a_filepath


def get_files_to_upload(tmpdirname: str) -> list[str]:
    """
    Get directory and iterate over files to upload

    Args:
    ----
        tmpdirname (str): _description_

    Returns:
    -------
        _type_: _description_

    """
    tree_list = tree(pathlib.Path(f"{tmpdirname}"))
    rich.print(tree_list)

    file_to_upload_list = [f"{p}" for p in tree_list]
    logger.debug(f"get_files_to_upload -> file_to_upload_list = {file_to_upload_list}")
    rich.print(file_to_upload_list)

    file_to_upload = filter_media(file_to_upload_list)

    logger.debug(f"get_files_to_upload -> file_to_upload = {file_to_upload}")

    rich.print(file_to_upload)
    return file_to_upload


def run_tree(tmpdirname: str) -> list[str]:
    """
    run_tree

    Args:
    ----
        tmpdirname (str): _description_

    Returns:
    -------
        _type_: _description_

    """
    # Now that we are finished processing, we can upload the files to discord

    tree_list = tree(pathlib.Path(f"{tmpdirname}"))
    rich.print("tree_list ->")
    rich.print(tree_list)

    file_to_upload_list = [f"{p}" for p in tree_list]
    logger.debug(f"compress_video-> file_to_upload_list = {file_to_upload_list}")
    rich.print(file_to_upload_list)

    file_to_upload = filter_media(file_to_upload_list)

    return file_to_upload


# smoke tests


async def aprint_and_append(
    dir_listing: list[str], tree_str: str, silent: bool = False
) -> None:
    """
    Async version of print_and_append function.

    Args:
    ----
        dir_listing (list[str]): List to append to.
        tree_str (str): String to print and append.
        silent (bool, optional): Whether to suppress printing. Defaults to False.

    """
    if not silent:
        print(tree_str)  # We keep print since it's not blocking
    dir_listing.append(tree_str)


async def atree(
    directory: str | pathlib.Path, silent: bool = False
) -> list[pathlib.Path]:
    """
    Async version of tree function to generate a tree structure of a directory.

    Args:
    ----
        directory (pathlib.Path): Path to the directory.
        silent (bool, optional): Whether to suppress printing. Defaults to False.

    Returns:
    -------
        list[pathlib.Path]: List of file paths in the directory.

    """
    logger.debug(f"directory -> {directory}")
    if isinstance(directory, str):
        directory = fix_path(directory)
        logger.debug(f"directory -> {directory}")
        directory = pathlib.Path(directory)
        logger.debug(f"directory -> {directory}")
    try:
        assert directory.is_dir()
    except:
        raise OSError(f"{directory} is not a directory.")

    file_system: list[pathlib.Path] = []
    _tree = []
    await aprint_and_append(_tree, f"+ {directory}", silent=silent)

    # Get all paths using rglob synchronously since it's a generator
    paths = sorted(directory.rglob("*"))

    for path in paths:
        file_system.append(pathlib.Path(f"{path.resolve()}"))
        try:
            depth = len(path.resolve().relative_to(directory.resolve()).parts)
        except ValueError:
            continue
        spacer = "    " * depth
        await aprint_and_append(_tree, f"{spacer}+ {path.name}", silent=silent)

    return sorted(file_system, key=os.path.getmtime)


async def afilter_images(working_dir: list[str]) -> list[str]:
    """
    Async version of filter_images function.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of image file paths.

    """
    filtered = []
    for f in working_dir:
        path = pathlib.Path(f"{f}")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            filtered.append(f)
    return filtered


async def afilter_videos(working_dir: list[str]) -> list[str]:
    """
    Async version of filter_videos function.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of video file paths.

    """
    filtered = []
    for f in working_dir:
        path = pathlib.Path(f"{f}")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            filtered.append(f)
    return filtered


async def afilter_media(working_dir: list[str]) -> list[str]:
    """
    Async version of filter_media function.
    Filters image and video files from a directory.

    Args:
    ----
        working_dir (list[str]): List of file paths.

    Returns:
    -------
        list[str]: List of image and video file paths.

    """
    imgs = await afilter_images(working_dir)
    videos = await afilter_videos(working_dir)
    return imgs + videos


async def aget_files_to_upload(tmpdirname: str) -> list[str]:
    """
    Async version of get_files_to_upload.
    Get directory and iterate over files to upload.

    Args:
    ----
        tmpdirname (str): Directory path to process.

    Returns:
    -------
        list[str]: List of files to upload.

    """
    tree_list = await atree(pathlib.Path(f"{tmpdirname}"))
    rich.print(tree_list)

    file_to_upload_list = [f"{p}" for p in tree_list]
    logger.debug(f"aget_files_to_upload -> file_to_upload_list = {file_to_upload_list}")
    rich.print(file_to_upload_list)

    file_to_upload = await afilter_media(file_to_upload_list)

    logger.debug(f"aget_files_to_upload -> file_to_upload = {file_to_upload}")

    rich.print(file_to_upload)
    return file_to_upload


async def arun_tree(tmpdirname: str) -> list[str]:
    """
    Async version of run_tree.

    Args:
    ----
        tmpdirname (str): Directory path to process.

    Returns:
    -------
        list[str]: List of media files found.

    """
    # Now that we are finished processing, we can upload the files to discord
    tree_list = await atree(pathlib.Path(f"{tmpdirname}"))
    rich.print("tree_list ->")
    rich.print(tree_list)

    file_to_upload_list = [f"{p}" for p in tree_list]
    logger.debug(f"compress_video-> file_to_upload_list = {file_to_upload_list}")
    rich.print(file_to_upload_list)

    file_to_upload = await afilter_media(file_to_upload_list)

    return file_to_upload
