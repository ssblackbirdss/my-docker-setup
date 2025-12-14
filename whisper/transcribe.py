#!/usr/bin/env python3

import argparse
import os
import sys
import time
import traceback
import shutil
import subprocess
from pathlib import Path

try:
    import whisper
except Exception:
    print("ERROR: whisper not installed.", file=sys.stderr)
    raise

# Supported audio extensions
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".aac"}
# Video extensions that can be converted
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}


def _unique_dest(path: Path) -> Path:
    """
    If path exists, return a new Path by appending _1, _2, ... before suffix.
    Example: file.mp4 -> file_1.mp4
    """
    if not path.exists():
        return path
    base = path.stem
    suffix = path.suffix
    parent = path.parent
    i = 1
    while True:
        candidate = parent / f"{base}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def safe_move(src: Path, dest_dir: Path) -> Path:
    """Move src into dest_dir safely (avoiding overwrite). Returns final destination Path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    dest = _unique_dest(dest)
    shutil.move(str(src), str(dest))
    return dest


def extract_audio_from_video(video_path: Path, audio_dir: Path) -> Path | None:
    """Extract audio from video using ffmpeg. Returns audio Path on success, else None."""
    audio_filename = video_path.stem + ".mp3"
    audio_path = audio_dir / audio_filename

    print(f"Extracting audio from: {video_path.name}")

    try:
        # Use ffmpeg to extract audio
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),
            "-q:a",
            "0",  # Best quality
            "-map",
            "a",
            str(audio_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ✗ FFmpeg error extracting from {video_path.name}: {result.stderr.strip()}")
            return None

        print(f"  ✓ Created audio: {audio_filename}")
        return audio_path

    except Exception as e:
        print(f"  ✗ Error extracting audio: {str(e)}")
        return None


def process_videos(video_dir: Path, audio_dir: Path, overwrite=False, move_processed=False, processed_dir: Path | None = None):
    """
    Convert video files to audio in the audio_dir.
    If move_processed is True and processed_dir is provided, move original video files into processed_dir
    after successful extraction or after skipping due to existing audio (when not overwriting).
    Returns list of created audio file Paths.
    """
    print("Looking for video files to convert...")

    video_files = []
    import glob

    for ext in VIDEO_EXTS:
        pattern = str(video_dir / f"*{ext}")
        video_files.extend(glob.glob(pattern))

    if not video_files:
        print("No video files found.")
        return []

    created_audio = []
    for video_path_str in video_files:
        video_path = Path(video_path_str)
        audio_filename = video_path.stem + ".mp3"
        audio_path = audio_dir / audio_filename

        # If audio already exists and we're not overwriting, skip extraction.
        if audio_path.exists() and not overwrite:
            print(f"Skipping {video_path.name} (audio {audio_filename} already exists)")
            # If requested, move the video to processed_dir to avoid reprocessing
            if move_processed and processed_dir is not None:
                try:
                    dest = safe_move(video_path, processed_dir)
                    print(f"Moved {video_path.name} -> {dest}")
                except Exception:
                    print(f"WARNING: failed to move {video_path} to {processed_dir}", file=sys.stderr)
                    traceback.print_exc()
            continue

        # Extract audio
        audio_file = extract_audio_from_video(video_path, audio_dir)
        if audio_file:
            created_audio.append(audio_file)
            # Move original video file after successful extraction (if requested)
            if move_processed and processed_dir is not None:
                try:
                    dest = safe_move(video_path, processed_dir)
                    print(f"Moved {video_path.name} -> {dest}")
                except Exception:
                    print(f"WARNING: failed to move {video_path} to {processed_dir}", file=sys.stderr)
                    traceback.print_exc()
        else:
            print(f"Failed to extract audio from {video_path.name}; leaving video in place.")

    return created_audio


def find_audio_files(directory: Path):
    """Find audio files in directory."""
    if not directory.exists():
        return []

    files = []
    for p in directory.iterdir():
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
            files.append(p)

    # Sort by modification time (oldest first)
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def transcribe_file(model, audio_path: Path, language: str | None, transcripts_dir: Path):
    """Transcribe audio file using whisper."""
    print(f"Transcribing: {audio_path} (language={language})")

    try:
        if language:
            result = model.transcribe(str(audio_path), language=language)
        else:
            result = model.transcribe(str(audio_path))
    except Exception:
        print(f"ERROR: transcription failed for {audio_path}", file=sys.stderr)
        traceback.print_exc()
        return None

    text = result.get("text", "").strip()
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = transcripts_dir / (audio_path.stem + ".txt")
    out_path.write_text(text, encoding="utf-8")
    print(f"Saved transcript: {out_path} (length {len(text)} chars)")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Auto-convert videos to audio and transcribe using whisper (CPU)"
    )
    parser.add_argument(
        "--audio-dir",
        default=os.environ.get("AUDIO_DIR", "/audio"),
        help="Directory for audio files (and where videos should be placed)",
    )
    parser.add_argument(
        "--model", default=os.environ.get("WHISPER_MODEL", "small"), help="Whisper model name"
    )
    parser.add_argument(
        "--language",
        default=os.environ.get("WHISPER_LANGUAGE", None),
        help="Force language code (e.g. en, fa)",
    )
    parser.add_argument(
        "--once", action="store_true", help="Process existing files then exit (no watcher)"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(os.environ.get("POLL_INTERVAL", "5")),
        help="Polling interval (seconds) when watching",
    )
    parser.add_argument(
        "--move-processed",
        action="store_true",
        default=os.environ.get("MOVE_PROCESSED", "1") == "1",
        help="Move processed files to processed-dir",
    )
    parser.add_argument(
        "--processed-dir",
        default=os.environ.get("PROCESSED_DIR", "/audio/processed"),
        help="Where to move processed files",
    )
    parser.add_argument(
        "--convert-videos",
        action="store_true",
        default=os.environ.get("CONVERT_VIDEOS", "1") == "1",
        help="Convert video files to audio before transcribing",
    )
    parser.add_argument(
        "--overwrite-audio",
        action="store_true",
        default=False,
        help="Overwrite existing audio files when converting videos",
    )

    args = parser.parse_args()

    audio_dir = Path(args.audio_dir)
    transcripts_dir = audio_dir / "transcripts"
    processed_dir = Path(args.processed_dir)

    if args.move_processed:
        processed_dir.mkdir(parents=True, exist_ok=True)

    print(f"Audio directory: {audio_dir}")
    print(f"Model: {args.model}")
    print(f"Language override: {args.language!r}")
    print(f"Convert videos: {args.convert_videos}")
    print(f"Mode: {'once' if args.once else 'watch'} (poll interval {args.poll_interval}s)")

    # Load model
    try:
        print(f"Loading model '{args.model}' on CPU...")
        model = whisper.load_model(args.model, device="cpu")
    except Exception:
        print("ERROR: failed to load model:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(3)

    # Main processing loop
    while True:
        # Convert videos to audio first (if enabled)
        if args.convert_videos:
            process_videos(
                audio_dir,
                audio_dir,
                args.overwrite_audio,
                move_processed=args.move_processed,
                processed_dir=processed_dir if args.move_processed else None,
            )

        # Find audio files to transcribe
        files = find_audio_files(audio_dir)

        # Exclude transcripts and processed dir files
        files = [
            f
            for f in files
            if f.parent != transcripts_dir and f.parent != processed_dir
        ]

        if files:
            for audio in files:
                try:
                    transcribe_file(model, audio, args.language, transcripts_dir)
                except Exception:
                    print(f"ERROR processing {audio}", file=sys.stderr)
                    traceback.print_exc()

                # Move the original audio file after transcription
                if args.move_processed:
                    try:
                        dest = safe_move(audio, processed_dir)
                        print(f"Moved {audio.name} -> {dest}")
                    except Exception:
                        print(f"WARNING: failed to move {audio}", file=sys.stderr)
                        traceback.print_exc()

            if args.once:
                print("Completed processing existing files. Exiting (once mode).")
                break

        else:
            if args.once:
                print("No audio files found. Exiting (once mode).")
                break

            # No files: poll again
            print(f"No audio files found in {audio_dir}. Polling again in {args.poll_interval}s...")
            time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
