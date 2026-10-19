import os

from flask import current_app
from pydub import AudioSegment


def merge_audio_files(audio_paths, output_path, pause_seconds=1.5):
    """
    Merge multiple MP3 files into one, inserting a pause between each.
    Args:
        audio_paths (list of str): List of paths to MP3 files to merge in order.
        output_path (str): Path to save the merged MP3 file.
        pause_seconds (float): Seconds of silence between each audio file.
    Returns:
        str: Path to the merged audio file.
    """
    if not audio_paths:
        raise ValueError("No audio files provided for merging.")

    current_app.logger.info(
        f"merge_audio_files: Merging {len(audio_paths)} files into {output_path}"
    )
    for path in audio_paths:
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        current_app.logger.info(
            f"merge_audio_files: File: {path}, exists={exists}, size={size} bytes"
        )

    # Create a silent segment for the pause
    pause = AudioSegment.silent(duration=int(pause_seconds * 1000))

    merged = None
    for idx, path in enumerate(audio_paths):
        if not os.path.exists(path):
            current_app.logger.error(f"merge_audio_files: File not found: {path}")
            raise FileNotFoundError(f"Audio file not found: {path}")
        try:
            segment = AudioSegment.from_file(path, format="mp3")
        except Exception as e:
            current_app.logger.error(f"merge_audio_files: Failed to read {path}: {e}")
            raise
        if merged is None:
            merged = segment
        else:
            merged += pause + segment

    merged.export(output_path, format="mp3")
    current_app.logger.info(
        f"merge_audio_files: Merged file created: {output_path}, size={os.path.getsize(output_path)} bytes"
    )
    return output_path
