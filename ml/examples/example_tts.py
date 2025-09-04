"""Пример синтеза речи с использованием ESpeechTTS.

Требуется подготовить короткий референсный аудиофайл (<= ~12 сек) и его текстовую транскрипцию.
Формат WAV 16-bit PCM предпочтителен.

Запуск (PowerShell):
  pip install -r ml/requirements.txt
  python -m ml.example_tts --ref-audio ref.wav --ref-text "Привет это эталон" --text "Привет! Это тест синтеза речи."

Результат: out.wav
"""
from __future__ import annotations

import argparse
import sys
import soundfile as sf  # type: ignore

from ml.tts import ESpeechTTS


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ESpeech TTS example")
    p.add_argument("--ref-audio", required=True, help="Путь к референсному wav")
    p.add_argument("--ref-text", required=True, help="Текст соответствующий референсному аудио")
    p.add_argument("--text", required=True, help="Текст для синтеза")
    p.add_argument("--out", default="out.wav", help="Выходной wav (default: out.wav)")
    p.add_argument("--speed", type=float, default=1.0, help="Скорость речи (default 1.0)")
    p.add_argument("--steps", type=int, default=32, help="NFE steps (default 32)")
    p.add_argument("--seed", type=int, default=None, help="Зерно для детерминированности")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    tts = ESpeechTTS()
    sr, audio = tts.synthesize(
        text=args.text,
        ref_audio_path=args.ref_audio,
        ref_text=args.ref_text,
        nfe_step=args.steps,
        speed=args.speed,
        seed=args.seed,
    )
    sf.write(args.out, audio, sr)
    print(f"Синтез завершён. Файл сохранён: {args.out} (sr={sr}, длительность ~{len(audio)/sr:.2f}s)")


if __name__ == "__main__":  # pragma: no cover
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
