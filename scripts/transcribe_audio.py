#!/usr/bin/env python3
"""SFA｜音声ファイル文字起こしスクリプト（OpenAI Whisper API使用）。

他社からもらった音声ファイルや、Limitless以外のアプリで録音した音声を、
SFAパイプラインが読み込める生テキストに変換する。

- 話者分離（誰が話したか）は行わない。全発言をタイムスタンプ付きの地の文として書き出す。
  必要であれば、後続のSFA Session化の工程で人手・Claudeの判断により話者を補う。
- OpenAI Whisper APIは1リクエストあたり25MBまでの制限があるため、
  それを超える音声ファイルはffmpegで分割してから順にAPIへ送り、結果を連結する。

依存:
  - ffmpeg（`brew install ffmpeg`）
  - openai (`pip install openai`)
  - 環境変数 OPENAI_API_KEY、または ~/.openai_key ファイル（1行目にキーのみ）
    ※ APIキーは絶対にリポジトリ内のファイルに書き込まないこと。

使い方:
  python3 scripts/transcribe_audio.py path/to/audio.m4a --output SFA/00_raw_logs/SFA-XXXX_raw.txt
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Whisper APIの実質的なアップロード上限（25MB）に対して安全マージンを取る
MAX_CHUNK_BYTES = 24 * 1024 * 1024
CHUNK_SECONDS = 600  # 分割時の1チャンクの長さ（秒）。25MB制限に収まるよう十分小さく取る


def load_api_key() -> str:
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key:
        return env_key

    key_file = Path.home() / ".openai_key"
    if key_file.exists():
        key = key_file.read_text(encoding="utf-8").strip()
        if key:
            return key

    raise SystemExit(
        "OpenAI APIキーが見つかりません。環境変数 OPENAI_API_KEY を設定するか、"
        "~/.openai_key にキーのみを1行で書いたファイルを作成してください。"
    )


def probe_duration_seconds(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def split_audio(audio_path: Path, chunk_seconds: int, workdir: Path) -> list[Path]:
    """ffmpegで音声を等間隔チャンクに分割する（音声・映像の再エンコードなし＝高速）。"""
    pattern = workdir / "chunk_%03d.m4a"
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(audio_path),
            "-f", "segment", "-segment_time", str(chunk_seconds),
            "-c", "copy", "-reset_timestamps", "1", str(pattern),
        ],
        check=True,
    )
    return sorted(workdir.glob("chunk_*.m4a"))


def transcribe_chunk(client, chunk_path: Path, model: str) -> str:
    with open(chunk_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=model,
            file=f,
            language="ja",
            response_format="text",
        )
    # response_format="text" のとき、SDKはプレーン文字列 or .text 属性のいずれかを返す
    return result if isinstance(result, str) else getattr(result, "text", str(result))


def transcribe_audio(audio_path: Path, model: str = "whisper-1") -> str:
    from openai import OpenAI

    client = OpenAI(api_key=load_api_key())

    size_bytes = audio_path.stat().st_size
    if size_bytes <= MAX_CHUNK_BYTES:
        print(f"[INFO] {audio_path.name} ({size_bytes / 1_000_000:.1f}MB) をそのまま送信します。", file=sys.stderr)
        return transcribe_chunk(client, audio_path, model).strip()

    print(
        f"[INFO] {audio_path.name} ({size_bytes / 1_000_000:.1f}MB) は25MBを超えるため、"
        f"{CHUNK_SECONDS}秒単位に分割して送信します。",
        file=sys.stderr,
    )
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        chunks = split_audio(audio_path, CHUNK_SECONDS, workdir)
        texts = []
        for i, chunk in enumerate(chunks, start=1):
            print(f"[INFO]  チャンク {i}/{len(chunks)} を文字起こし中...", file=sys.stderr)
            texts.append(transcribe_chunk(client, chunk, model).strip())
        return "\n\n".join(texts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("audio_file", type=Path, help="文字起こし対象の音声ファイル")
    parser.add_argument("--model", default="whisper-1", help="使用するWhisperモデル（既定: whisper-1）")
    parser.add_argument("--output", type=Path, default=None, help="出力先テキストファイル（省略時は標準出力）")
    args = parser.parse_args()

    if not args.audio_file.exists():
        raise SystemExit(f"音声ファイルが見つかりません: {args.audio_file}")

    text = transcribe_audio(args.audio_file, model=args.model)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
        print(f"[OK] 文字起こし結果を書き出しました: {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
