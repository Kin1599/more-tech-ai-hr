"""Пример потокового распознавания речи с использованием StreamingTranscriber.

Запуск:
  $env:GROQ_API_KEY не требуется для STT
  pip install tone
  python -m ml.example_stt
"""
from __future__ import annotations

from ml.stt import StreamingTranscriber

try:
    from tone import read_stream_example_audio  # type: ignore
except ImportError:
    raise SystemExit("Установите пакет tone: pip install tone")


def main() -> None:
    transcriber = StreamingTranscriber()
    print("Demo streaming STT...")
    for phrase in transcriber.transcribe_stream(read_stream_example_audio()):
        print("NEW:", phrase)
    for phrase in transcriber.finalize():
        print("FINAL:", phrase)


if __name__ == "__main__":
    main()
