#!/usr/bin/env python3
"""SFA｜受信箱（00_inbox）用の汎用テキスト変換スクリプト。

Limitless以外の情報源（他社からもらった音声ファイル、文字起こし済みのWord文書、
すでにテキスト化されたメモなど）を、SFAパイプラインの入力として使える
プレーンテキストに変換する。ファイル形式ごとの変換のみを行い、
どのファイルをどのセッションにまとめるか・メタデータの聞き取りといった
意味判断はここでは行わない（sfa-runスキル側でClaudeが行う）。

対応形式:
  - 音声（.m4a/.mp3/.wav/.mp4/.mov 等）: scripts/transcribe_audio.py を呼び出す
  - Word（.docx）: markitdown でテキスト抽出
  - テキスト（.txt/.md）: そのまま読み込む（Limitless形式ならそのまま解釈可能）

使い方:
  python3 scripts/intake_convert.py SFA/00_inbox/onsei.m4a --output /tmp/out.txt
  python3 scripts/intake_convert.py SFA/00_inbox/memo.docx
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".mp4", ".mov", ".aac", ".flac", ".ogg"}
DOCX_EXTENSIONS = {".docx"}
TEXT_EXTENSIONS = {".txt", ".md"}

SCRIPT_DIR = Path(__file__).resolve().parent


def convert_audio(path: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "transcribe_audio.py"), str(path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"音声文字起こしに失敗しました: {path}\n{result.stderr}")
    return result.stdout.strip() + "\n"


def convert_docx(path: Path) -> str:
    from markitdown import MarkItDown

    md = MarkItDown()
    return md.convert(str(path)).text_content


def convert_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def convert(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in AUDIO_EXTENSIONS:
        return convert_audio(path)
    if ext in DOCX_EXTENSIONS:
        return convert_docx(path)
    if ext in TEXT_EXTENSIONS:
        return convert_text(path)
    raise SystemExit(
        f"未対応のファイル形式です: {path} (拡張子 {ext})\n"
        f"対応形式: 音声({', '.join(sorted(AUDIO_EXTENSIONS))}) / "
        f"Word(.docx) / テキスト(.txt, .md)"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", type=Path, help="変換対象ファイル（SFA/00_inbox/ 配下推奨）")
    parser.add_argument("--output", type=Path, default=None, help="出力先テキストファイル（省略時は標準出力）")
    args = parser.parse_args()

    if not args.input_file.exists():
        raise SystemExit(f"ファイルが見つかりません: {args.input_file}")

    text = convert(args.input_file)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"[OK] 変換結果を書き出しました: {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
