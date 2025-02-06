#!/usr/bin/env bash
# shellcheck disable=SC2034

if [ "${PYTHON_DEBUG:-0}" -gt 0 ] ; then
    set -x ;
fi

# Function for processing video file
process_video() {
    echo "Processing video file: $input_file"

    # Calculate bitrate based on input file duration
    duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input_file")

    # bitrate=$((23 * 8 * 1000 / duration))
    bitrate=$(python -c "duration=${duration}; print(int(23 * 8 * 1000 / duration))")

    echo "Video length: ${duration}s"
    echo ""Bitrate" target: ${bitrate}k"

    # Exit if target bitrate is under 150kbps
    if [ "$bitrate" -lt 150 ]; then
        echo "Target bitrate is under 150kbps."
        echo "Unable to compress."
        exit 1
    fi

    # Allocate bitrate based on video properties
    # video_bitrate=$((bitrate * 90 / 100))
    # audio_bitrate=$((bitrate * 10 / 100))
    video_bitrate=$(python -c "bitrate=${bitrate}; print(int(bitrate * 90 / 100))")
    audio_bitrate=$(python -c "bitrate=${bitrate}; print(int(bitrate * 10 / 100))")
    # video_bitrate=$((bitrate * 90 / 100))
    # audio_bitrate=$((bitrate * 10 / 100))

    echo "Video Bitrate: ${video_bitrate}k"
    echo ""Audio Bitrate": ${audio_bitrate}k"

    # Exit if target video bitrate is under 125kbps
    if [ "$video_bitrate" -lt 125 ]; then
        echo "Target video bitrate is under 125kbps."
        echo "Unable to compress."
        exit 1
    fi

    # Exit if target audio bitrate is under 32kbps
    if [ "$audio_bitrate" -lt 32 ]; then
        echo "Target audio bitrate is under 32."
        echo "Unable to compress."
        exit 1
    fi

    pushd "$input_directory"
    echo "Compressing video file using FFmpeg..."
    ffmpeg -hide_banner -loglevel warning -stats -threads 0 -hwaccel auto -i "$input_file" -preset slow -c:v libx264 -b:v ${video_bitrate}k -c:a aac -b:a ${audio_bitrate}k -bufsize ${bitrate}k -minrate 100k -maxrate ${bitrate}k "25MB_${input_file_name}.mp4"
    popd
}

# Function for processing audio file
process_audio() {
    echo "Processing audio file: $input_file"

    # Calculate input file duration
    duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input_file")

    # Calculate target bitrate based on input file duration
    # bitrate=$((25 * 8 * 1000 / duration))
    bitrate=$(python -c "duration=${duration}; print(int(25 * 8 * 1000 / duration))")
    echo "Audio duration: ${duration}s"
    echo "Bitrate target: ${bitrate}k"

    # Exit if target bitrate is under 32kbps
    if [ "$bitrate" -lt 32 ]; then
        echo "Target bitrate is under 32kbps."
        echo "Unable to compress."
        exit 1
    fi

    # Compress audio file using FFmpeg
    pushd "$input_directory"
    echo "Compressing audio file using FFmpeg..."
    ffmpeg -y -hide_banner -loglevel warning -stats -i "$input_file" -preset slow -c:a libmp3lame -b:a ${bitrate}k -bufsize ${bitrate}k -minrate 100k -maxrate ${bitrate}k "25MB_${input_file_name}.mp3"
    popd
}


# SOURCE: https://github.com/MyloBishop/discompress
# SOURCE: https://chatgpt.com/c/a091f983-7547-41a3-99e8-69718a92fc5f
# Get the directory and file extension of the input file
input_file="$1"
input_directory=$(dirname "$input_file")
input_extension="${input_file##*.}"

# Extract input file name without extension
input_file_name=$(basename "$input_file" ".$input_extension")

# Get current date and time
current_time=$(date +"%H%M%S")

# Convert the response to lowercase
input_extension_lower=$(echo "$input_extension" | tr '[:upper:]' '[:lower:]')

# Check if input file extension is valid for video
video_extensions="mp4 avi mkv mov flv wmv webm mpeg 3gp"
if echo "$video_extensions" | grep -qw "$input_extension_lower"; then
    process_video
    exit 0
fi

# Check if input file extension is valid for audio
audio_extensions="mp3 wav m4a flac aac ogg wma"
if echo "$audio_extensions" | grep -qw "$input_extension_lower"; then
    process_audio
    exit 0
fi

# If input file extension is not recognized, display error message and exit
echo "File type not supported."
echo "Terminating compression."
exit 1
