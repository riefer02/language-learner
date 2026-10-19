"""Audio staging, commit, and orphan auditing.

Files are generated in a private staging directory. They are moved into the
public audio directory only after every generation step succeeds, and the
caller is responsible for deleting moved files if the database transaction
fails. A crash between the move and the commit can still leave an orphan; the
``media-gc`` CLI command exists to clean those up safely.
"""

import os
import shutil
import tempfile
from contextlib import contextmanager


class MediaError(RuntimeError):
    """Raised when staging or committing an audio artifact fails."""


def ensure_directory(path):
    os.makedirs(path, exist_ok=True)
    return path


class AudioBatch:
    """Owns a temporary directory for one logical audio generation job."""

    def __init__(self, media_root):
        ensure_directory(media_root)
        self._root = media_root
        self._dir = tempfile.mkdtemp(prefix="batch-", dir=media_root)
        self._files = []

    def path(self, filename):
        """Return a staging path for ``filename`` (basename only)."""
        safe_name = os.path.basename(filename)
        if not safe_name or safe_name in {".", ".."}:
            raise MediaError("Audio filename must be a safe basename")
        path = os.path.join(self._dir, safe_name)
        self._files.append(path)
        return path

    def commit_to(self, destination_dir, mapping):
        """Move staged files into ``destination_dir``.

        ``mapping`` is an iterable of ``(staged_path, final_filename)``. Returns
        a list of final absolute paths. If any move fails, files already moved
        are deleted before the error is raised.
        """
        ensure_directory(destination_dir)
        moved = []
        try:
            for staged_path, final_filename in mapping:
                safe_name = os.path.basename(final_filename)
                if not safe_name:
                    raise MediaError("Audio filename must not be empty")
                final_path = os.path.join(destination_dir, safe_name)
                shutil.move(staged_path, final_path)
                moved.append(final_path)
            return moved
        except Exception:
            remove_files(moved)
            raise

    def cleanup(self):
        shutil.rmtree(self._dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.cleanup()
        return False


@contextmanager
def staged_audio(media_root, filename):
    """Yield a temporary path, removing it when the block exits."""
    batch = AudioBatch(media_root)
    try:
        yield batch.path(filename)
    finally:
        batch.cleanup()


def remove_files(paths):
    """Remove files, ignoring missing paths and logging nothing."""
    for path in paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


def safe_audio_filename(text, prefix="", max_length=30):
    """Build a filesystem-safe filename stem from user/model text."""
    cleaned = "".join(
        char
        for char in str(text).lower().replace(" ", "_")
        if char.isalnum() or char == "_"
    )
    cleaned = cleaned[:max_length] or "audio"
    return f"{prefix}{cleaned}"


def referenced_audio_filenames(*path_groups):
    """Normalize stored URL paths from any number of source tables."""
    referenced = set()
    for paths in path_groups:
        for path in paths:
            if not path:
                continue
            referenced.add(os.path.basename(str(path)))
    return referenced


def list_audio_files(audio_dir):
    if not os.path.isdir(audio_dir):
        return []
    return sorted(
        name
        for name in os.listdir(audio_dir)
        if os.path.isfile(os.path.join(audio_dir, name))
    )


def audit_media(audio_dir, referenced):
    """Return ``(orphans, missing_references)`` as sorted filename lists."""
    present = set(list_audio_files(audio_dir))
    orphans = sorted(present - referenced)
    missing = sorted(referenced - present)
    return orphans, missing
