#!/usr/bin/env python3
"""SFA｜Limitlessライフログ取得スクリプト。

Limitless API から指定日(・時間帯)のライフログを取得し、`clean_limitless_log.py`
がそのまま読める「- 話者 (M/D/YY H:MM AM/PM): 発言」形式の raw log テキストとして
標準出力（または --output 指定時はファイル）に書き出す。

APIキーは環境変数 LIMITLESS_API_KEY、または ~/.limitless_keys
(`LIMITLESS_API_KEY=...` の1行を含むファイル) から読み込む。
このスクリプト自体にAPIキーを埋め込まないこと(このリポジトリは公開リポジトリ)。

使い方:
  python3 scripts/fetch_lifelog.py --date 2026-07-14 \\
      --start 14:00 --end 17:30 \\
      --output SFA/00_raw_logs/SFA-20260714-001_yaoichi_group-c-2nd-reflection_raw.txt

依存: requests (pip install requests)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import requests

CONFIG_FILE = os.path.expanduser("~/.limitless_keys")


def load_api_key() -> str:
    key = os.environ.get("LIMITLESS_API_KEY")
    if key:
        return key
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith("LIMITLESS_API_KEY="):
                    return line.split("=", 1)[1].strip()
    raise SystemExit(
        "LIMITLESS_API_KEY が見つかりません。環境変数を設定するか、"
        f"{CONFIG_FILE} に `LIMITLESS_API_KEY=...` を1行追加してください。"
    )


def fetch_lifelogs(date_str: str, api_key: str) -> list:
    url = "https://api.limitless.ai/v1/lifelogs"
    headers = {"X-API-Key": api_key}
    params = {"date": date_str, "limit": 100, "timezone": "Asia/Tokyo"}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()["data"]["lifelogs"]


def jst_hhmm(ts: str) -> str:
    if not ts or len(ts) < 16:
        return ""
    return ts[11:16]


def filter_by_time(logs: list, start: Optional[str], end: Optional[str]) -> list:
    if not start and not end:
        return logs
    result = []
    for log in logs:
        hhmm = jst_hhmm(log.get("startTime", ""))
        if start and hhmm < start:
            continue
        if end and hhmm > end:
            continue
        result.append(log)
    return result


def logs_to_raw_text(logs: list) -> str:
    """各エントリの markdown（話者ヘッダー付きの生形式）を時系列に連結する。

    要約・整形は一切行わない(意味判断が必要な処理はここでは行わない方針のため)。
    """
    logs_sorted = sorted(logs, key=lambda l: l.get("startTime", ""))
    parts = []
    for log in logs_sorted:
        md = (log.get("markdown") or "").strip()
        if md:
            parts.append(md)
    return "\n".join(parts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--date", required=True, help="対象日 (YYYY-MM-DD, JST)")
    parser.add_argument("--start", default=None, help="開始時刻 JST HH:MM(省略時は終日)")
    parser.add_argument("--end", default=None, help="終了時刻 JST HH:MM")
    parser.add_argument("--output", type=Path, default=None, help="出力ファイルパス(省略時は標準出力)")
    args = parser.parse_args()

    api_key = load_api_key()

    print(f"[INFO] Limitless APIから {args.date} のログを取得中...", file=sys.stderr)
    logs = fetch_lifelogs(args.date, api_key)
    print(f"[INFO] {len(logs)} 件取得", file=sys.stderr)

    logs = filter_by_time(logs, args.start, args.end)
    print(f"[INFO] 時間帯フィルタ後: {len(logs)} 件", file=sys.stderr)

    if not logs:
        raise SystemExit("[ERROR] 対象ログがありません。")

    raw_text = logs_to_raw_text(logs)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw_text, encoding="utf-8")
        print(f"[OK] raw log を書き出しました: {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(raw_text)


if __name__ == "__main__":
    main()
