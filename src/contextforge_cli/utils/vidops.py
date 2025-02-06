# pylint: disable=possibly-used-before-assignment
# pylint: disable=consider-using-from-import
# https://github.com/universityofprofessorex/ESRGAN-Bot

# Creative Commons may be contacted at creativecommons.org.
# NOTE: For more examples tqdm + aiofile, search https://github.com/search?l=Python&q=aiofile+tqdm&type=Code
# pylint: disable=no-member

from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import pathlib
import sys
import traceback
from pathlib import Path

import structlog

from contextforge_cli import shell
from contextforge_cli.shell import _aio_run_process_and_communicate
from contextforge_cli.utils.file_functions import VIDEO_EXTENSIONS, unlink_orig_file

logger = structlog.get_logger(__name__)

# https://github.com/universityofprofessorex/ESRGAN-Bot


async def get_duration(input_file: Path) -> float:
    """
    Get duration of a file using FFmpeg.

    Args:
    ----
        input_file (Path): The path to the input audio file.

    """
    logger.debug(f"Processing audio file: {input_file}")

    # Calculate input file duration
    duration_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_file),
    ]
    logger.debug(f"duration_cmd = {duration_cmd}")
    duration = float(await _aio_run_process_and_communicate(duration_cmd))
    logger.debug(f"duration = {duration}")
    # await logger.complete()
    return duration


def calculate_bitrate(duration: float, multiplier: int) -> int:
    """
    Calculate bitrate based on duration and multiplier.

    Args:
    ----
        duration (float): The duration of the media file in seconds.
        multiplier (int): A multiplier to adjust the bitrate calculation.

    Returns:
    -------
        int: The calculated bitrate in kbps.

    """
    bitrate = int(multiplier * 8 * 1000 / duration)
    logger.debug(f"bitrate = {bitrate}")
    return bitrate


async def process_video(input_file: Path) -> None:
    """
    Process and compress a video file using FFmpeg.

    This function calculates the appropriate bitrate based on the video duration,
    then compresses the video using FFmpeg with the calculated bitrate.

    Args:
    ----
        input_file (Path): The path to the input video file.

    Returns:
    -------
        None

    """
    logger.debug(f"Processing video file: {input_file}")

    # Calculate bitrate based on input file duration
    duration_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(input_file),
    ]
    duration = await get_duration(input_file)
    bitrate = calculate_bitrate(duration, 23)

    logger.debug(f"Video length: {duration}s")
    logger.debug(f"Bitrate target: {bitrate}k")

    # Exit if target bitrate is under 150kbps
    if bitrate < 150:
        logger.debug("Target bitrate is under 150kbps.")
        logger.debug("Unable to compress.")
        # await logger.complete()
        return

    video_bitrate = int(bitrate * 90 / 100)
    audio_bitrate = int(bitrate * 10 / 100)

    logger.debug(f"Video Bitrate: {video_bitrate}k")
    logger.debug(f"Audio Bitrate: {audio_bitrate}k")

    # Exit if target video bitrate is under 125kbps
    if video_bitrate < 125:
        logger.debug("Target video bitrate is under 125kbps.")
        logger.debug("Unable to compress.")
        # await logger.complete()
        return

    # Exit if target audio bitrate is under 32kbps
    if audio_bitrate < 32:
        logger.debug("Target audio bitrate is under 32.")
        logger.debug("Unable to compress.")
        # await logger.complete()
        return

    logger.debug("Compressing video file using FFmpeg...")
    output_file = input_file.parent / f"25MB_{input_file.stem}.mp4"
    compress_cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-stats",
        "-threads",
        "0",
        "-hwaccel",
        "auto",
        "-i",
        str(input_file),
        "-preset",
        "slow",
        "-c:v",
        "libx264",
        "-b:v",
        f"{video_bitrate}k",
        "-c:a",
        "aac",
        "-b:a",
        f"{audio_bitrate}k",
        "-bufsize",
        f"{bitrate}k",
        "-minrate",
        "100k",
        "-maxrate",
        f"{bitrate}k",
        str(output_file),
    ]
    logger.debug(f"compress_cmd = {compress_cmd}")
    await _aio_run_process_and_communicate(compress_cmd)
    # await logger.complete()


async def process_audio(input_file: Path) -> None:
    """
    Process and compress an audio file using FFmpeg.

    This function calculates the appropriate bitrate based on the audio duration,
    then compresses the audio using FFmpeg with the calculated bitrate.

    Args:
    ----
        input_file (Path): The path to the input audio file.

    Returns:
    -------
        None

    """
    duration = await get_duration(input_file)
    bitrate = calculate_bitrate(duration, 25)

    logger.debug(f"Audio duration: {duration}s")
    logger.debug(f"Bitrate target: {bitrate}k")

    # Exit if target bitrate is under 32kbps
    if bitrate < 32:
        logger.debug("Target bitrate is under 32kbps.")
        logger.debug("Unable to compress.")
        # await logger.complete()
        return

    logger.debug("Compressing audio file using FFmpeg...")
    output_file = input_file.parent / f"25MB_{input_file.stem}.mp3"
    compress_cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-stats",
        "-i",
        str(input_file),
        "-preset",
        "slow",
        "-c:a",
        "libmp3lame",
        "-b:a",
        f"{bitrate}k",
        "-bufsize",
        f"{bitrate}k",
        "-minrate",
        "100k",
        "-maxrate",
        f"{bitrate}k",
        str(output_file),
    ]
    logger.debug(f"compress_cmd = {compress_cmd}")
    await _aio_run_process_and_communicate(compress_cmd)
    # await logger.complete()


async def aio_compress_video(tmpdirname: str, file_to_compress: str) -> bool:
    """
    _summary_

    Args:
    ----
        tmpdirname (str): _description_
        file_to_compress (str): _description_
        bot (Any): _description_
        ctx (Any): _description_

    Returns:
    -------
        List[str]: _description_

    """
    if (pathlib.Path(f"{file_to_compress}").is_file()) and pathlib.Path(
        f"{file_to_compress}"
    ).suffix in VIDEO_EXTENSIONS:
        logger.debug(f"compressing file -> {file_to_compress}")
        ######################################################
        # compress the file if it is too large
        ######################################################
        compress_command = [
            "./scripts/compress-discord.sh",
            f"{file_to_compress}",
        ]

        loop = asyncio.get_running_loop()

        try:
            _ = await shell._aio_run_process_and_communicate(
                compress_command, cwd=f"{tmpdirname}"
            )

            logger.debug(
                f"compress_video: new file size for {file_to_compress} = {pathlib.Path(file_to_compress).stat().st_size}"
            )

            ######################################################
            # nuke the uncompressed version
            ######################################################

            logger.info(f"nuking uncompressed: {file_to_compress}")

            # nuke the originals
            unlink_func = functools.partial(unlink_orig_file, f"{file_to_compress}")

            # 2. Run in a custom thread pool:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                unlink_result = await loop.run_in_executor(pool, unlink_func)

            # await logger.complete()
            return True
        except Exception as ex:
            print(ex)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(f"Error Class: {ex.__class__!s}")
            output = f"[UNEXPECTED] {type(ex).__name__}: {ex}"
            logger.warning(output)
            logger.error(f"exc_type: {exc_type}")
            logger.error(f"exc_value: {exc_value}")
            traceback.print_tb(exc_traceback)
            # await logger.complete()

    else:
        logger.debug(f"no videos to process in {tmpdirname}")
        # await logger.complete()
        return False


def compress_video(tmpdirname: str, file_to_compress: str) -> bool:
    """
    _summary_

    Args:
    ----
        tmpdirname (str): _description_
        file_to_compress (str): _description_
        bot (Any): _description_
        ctx (Any): _description_

    Returns:
    -------
        List[str]: _description_

    """
    if (pathlib.Path(f"{file_to_compress}").is_file()) and pathlib.Path(
        f"{file_to_compress}"
    ).suffix in VIDEO_EXTENSIONS:
        logger.debug(f"compressing file -> {file_to_compress}")
        ######################################################
        # compress the file if it is too large
        ######################################################
        compress_command = [
            "./scripts/compress-discord.sh",
            f"{file_to_compress}",
        ]

        try:
            _ = shell.pquery(compress_command, cwd=f"{tmpdirname}")

            logger.debug(
                f"compress_video: new file size for {file_to_compress} = {pathlib.Path(file_to_compress).stat().st_size}"
            )

            logger.info(f"nuking uncompressed: {file_to_compress}")

            # nuke the originals
            unlink_orig_file(f"{file_to_compress}")
            # logger.complete()()
            return True
        except Exception as ex:
            print(ex)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.error(f"Error Class: {ex.__class__!s}")
            output = f"[UNEXPECTED] {type(ex).__name__}: {ex}"
            logger.warning(output)
            logger.error(f"exc_type: {exc_type}")
            logger.error(f"exc_value: {exc_value}")
            traceback.print_tb(exc_traceback)
            # logger.complete()()

    else:
        logger.debug(f"no videos to process in {tmpdirname}")
        # logger.complete()()
        return False
