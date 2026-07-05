#!/usr/bin/env python3
"""SFA｜Limitlessログ時系列整列スクリプト。

Limitlessの書き出し（Web UI等）は、複数の録音セグメントを最新のものから
順に並べて書き出す場合があり、その結果raw logのタイムスタンプが前後に
入り乱れることがある。本スクリプトは各行の "Unknown (M/D/YY H:MM AM/PM): 発言"
形式からタイムスタンプを抽出し、実際の時刻順に安定ソートして書き出す。

同一分内の複数行は、抽出できる精度が「分」までのため、入力ファイル内での
出現順を保ったまま（安定ソート）並べる。

使い方:
  python3 scripts/sort_limitless_log.py <input_raw_log> <output_sorted_log>
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

LINE_PATTERN = re.compile(
    r"^-\s*Unknown\s*\((?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{2})\s+"
    r"(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*(?P<ampm>AM|PM)\):\s*(?P<content>.*)$"
)


def parse_entries(text: str) -> list[tuple[datetime, int, str]]:
    entries: list[tuple[datetime, int, str]] = []
    for index, raw_line in enumerate(text.splitlines()):
        match = LINE_PATTERN.match(raw_line.strip())
        if not match:
            continue
        year = 2000 + int(match.group("year"))
        month = int(match.group("month"))
        day = int(match.group("day"))
        hour = int(match.group("hour")) % 12
        if match.group("ampm") == "PM":
            hour += 12
        minute = int(match.group("minute"))
        timestamp = datetime(year, month, day, hour, minute)
        entries.append((timestamp, index, raw_line.strip()))
    return entries


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: sort_limitless_log.py <input_raw_log> <output_sorted_log>")

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    text = input_path.read_text(encoding="utf-8")
    entries = parse_entries(text)
    if not entries:
        raise SystemExit("タイムスタンプ付きの行が見つかりませんでした。フォーマットを確認してください。")

    entries.sort(key=lambda e: (e[0], e[1]))

    lines = [entry[2] for entry in entries]
    output_path.write_text("\n\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] {len(entries)} 件のエントリを時系列順に整列し、書き出しました: {output_path}")
    print(f"     期間: {entries[0][0]} 〜 {entries[-1][0]}")


if __name__ == "__main__":
    main()
