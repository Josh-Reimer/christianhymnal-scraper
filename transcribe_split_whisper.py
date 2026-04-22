import subprocess
import sys
import pathlib
import whisper
import tempfile
import re

# ---------------- CONFIG ----------------
SILENCE_DB = -40        # silence threshold (dB)
SILENCE_DURATION = 1.0 # seconds of silence to split on
WHISPER_MODEL = "large"  # or "medium", "small"
LANGUAGE = "en"
# ----------------------------------------

def detect_silences(mp3_path):
    """
    Uses ffmpeg silencedetect to find silence end points
    """
    cmd = [
        "ffmpeg",
        "-i", str(mp3_path),
        "-af", f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_DURATION}",
        "-f", "null",
        "-"
    ]

    result = subprocess.run(
        cmd,
        stderr=subprocess.PIPE,
        text=True
    )

    silence_ends = []
    for line in result.stderr.splitlines():
        if "silence_end" in line:
            match = re.search(r"silence_end: ([0-9\.]+)", line)
            if match:
                silence_ends.append(float(match.group(1)))

    return silence_ends


def split_audio(mp3_path, silence_points, tmp_dir):
    chunks = []
    prev = 0.0

    for i, t in enumerate(silence_points):
        out = tmp_dir / f"chunk_{i:04d}.mp3"
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", str(mp3_path),
            "-ss", str(prev),
            "-to", str(t),
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "libmp3lame",
            "-b:a", "128k",
            str(out)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if out.exists() and out.stat().st_size > 1024:
            chunks.append(out)

        prev = t

    # final tail
    out = tmp_dir / f"chunk_{len(chunks):04d}.mp3"
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", str(mp3_path),
        "-ss", str(prev),
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        str(out)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if out.exists() and out.stat().st_size > 1024:
        chunks.append(out)

    return chunks



def transcribe_chunks(chunks):
    model = whisper.load_model(WHISPER_MODEL)
    transcript = []

    for chunk in chunks:
        print(f"→ Transcribing {chunk.name}")
        result = model.transcribe(
            str(chunk),
            language=LANGUAGE,
            condition_on_previous_text=False
        )

        text = result["text"].strip()
        if text:
            transcript.append(text)

    return "\n\n".join(transcript)


def main(mp3_path):
    mp3_path = pathlib.Path(mp3_path).resolve()
    output_txt = mp3_path.with_suffix(".txt")

    print("Detecting silence…")
    silences = detect_silences(mp3_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = pathlib.Path(tmp)

        print("Splitting audio…")
        chunks = split_audio(mp3_path, silences, tmp_dir)

        print(f"{len(chunks)} chunks created")
        print("Running Whisper…")

        full_text = transcribe_chunks(chunks)

    output_txt.write_text(full_text, encoding="utf-8")
    print(f"✓ Transcription written to {output_txt}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transcribe_split_whisper.py input.mp3")
        sys.exit(1)

    main(sys.argv[1])
