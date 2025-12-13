# transcribe.py
import argparse
import whisper
import os
import sys
import traceback

def main():
    p = argparse.ArgumentParser(description="Transcribe audio with OpenAI Whisper (CPU)")
    p.add_argument("audio", nargs="?", default="/audio/input.wav", help="Path to audio file (default /audio/input.wav)")
    p.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "small"), help="Whisper model name (tiny, base, small, medium, large)")
    p.add_argument("--language", default=None, help="Optional: force language code (e.g. en)")
    args = p.parse_args()

    audio_path = args.audio
    if not os.path.isfile(audio_path):
        print(f"ERROR: audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(2)

    try:
        print(f"Loading model '{args.model}' on CPU...")
        model = whisper.load_model(args.model, device="cpu")
    except Exception as e:
        print("ERROR: failed to load model:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(3)

    try:
        print("Transcribing...")
        if args.language:
            result = model.transcribe(audio_path, language=args.language)
        else:
            result = model.transcribe(audio_path)
    except Exception:
        print("ERROR: transcription failed:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(4)

    print("\n--- TRANSCRIPT ---\n")
    print(result.get("text", ""))
    print("\n--- END ---\n")

if __name__ == "__main__":
    main()
