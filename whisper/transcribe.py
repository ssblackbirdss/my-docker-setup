#!/usr/bin/env python3
"""
Auto-detect audio files in /audio, transcribe with whisper (CPU),
write transcripts to /audio/transcripts and move processed audio to /audio/processed.
"""

import argparse
import os
import sys
import time
import traceback
import shutil
from pathlib import Path

try:
    import whisper
except Exception:
    print("ERROR: whisper not installed.", file=sys.stderr)
    raise

# supported audio extensions
SUPPORTED_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm", ".aac"}


def find_audio_files(directory: Path):
    if not directory.exists():
        return []
    files = [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS]
    # sort oldest -> newest; change key to ctime if you prefer creation time
    files.sort(key=lambda p: p.stat().st_mtime)
    return files


def transcribe_file(model, audio_path: Path, language: str | None, transcripts_dir: Path):
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
    p = argparse.ArgumentParser(description="Auto-transcribe audio files in /audio using whisper (CPU)")
    p.add_argument("--audio-dir", default=os.environ.get("AUDIO_DIR", "/audio"), help="Directory to watch/process")
    p.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "small"), help="Whisper model name")
    p.add_argument("--language", default=os.environ.get("WHISPER_LANGUAGE", None), help="Force language code (e.g. en, fa)")
    p.add_argument("--once", action="store_true", help="Process existing files then exit (no watcher)")
    p.add_argument("--poll-interval", type=int, default=int(os.environ.get("POLL_INTERVAL", "5")), help="Polling interval (seconds) when watching")
    p.add_argument("--move-processed", action="store_true", default=os.environ.get("MOVE_PROCESSED", "1") == "1", help="Move processed audio to processed-dir")
    p.add_argument("--processed-dir", default=os.environ.get("PROCESSED_DIR", "/audio/processed"), help="Where to move processed audio")
    args = p.parse_args()

    audio_dir = Path(args.audio_dir)
    transcripts_dir = audio_dir / "transcripts"
    processed_dir = Path(args.processed_dir)

    if args.move_processed:
        processed_dir.mkdir(parents=True, exist_ok=True)

    print(f"Audio directory: {audio_dir}")
    print(f"Model: {args.model}")
    print(f"Language override: {args.language!r}")
    print(f"Mode: {'once' if args.once else 'watch'} (poll interval {args.poll_interval}s)")

    # load model once
    try:
        print(f"Loading model '{args.model}' on CPU...")
        model = whisper.load_model(args.model, device="cpu")
    except Exception:
        print("ERROR: failed to load model:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(3)

    # main loop
    while True:
        files = find_audio_files(audio_dir)

        # exclude transcripts and processed dir files
        files = [f for f in files if f.parent != transcripts_dir and f.parent != processed_dir]

        if files:
            for audio in files:
                try:
                    transcribe_file(model, audio, args.language, transcripts_dir)
                except Exception:
                    print(f"ERROR processing {audio}", file=sys.stderr)
                    traceback.print_exc()
                # move the original file after successful transcription (or even after failure, depending on needs)
                if args.move_processed:
                    try:
                        dest = processed_dir / audio.name
                        shutil.move(str(audio), str(dest))
                        print(f"Moved {audio.name} -> {dest}")
                    except Exception:
                        print(f"WARNING: failed to move {audio}", file=sys.stderr)
                        traceback.print_exc()
            if args.once:
                print("Completed processing existing files. Exiting (once mode).")
                break
            # loop to check for new files
        else:
            if args.once:
                print("No audio files found. Exiting (once mode).")
                break
            # No files: poll again after a short sleep
            print(f"No audio files found in {audio_dir}. Polling again in {args.poll_interval}s...")
            time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
