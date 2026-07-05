#!/usr/bin/env python3
"""SFA｜Limitlessログ機械クリーニングスクリプト。

raw log (Limitless Pendant の書き出しテキスト) を読み込み、以下の機械的な処理のみを行う。
意味判断が必要な編集（誤認識文脈からの推測修正・段落整理・SFA Session化）は行わない。
それらは prompts/SFA_Builder_v1.md を使ってLLMに委ねる前提。

処理内容:
  1. raw log 読み込み
  2. タイムスタンプ・タイムライン表記の削除
  3. Unknown話者行の削除
  4. フィラー（あの／えっと 等）の削除
  5. 単独の相づち行（はい／うん／そうですね 等）の削除
  6. 連続する重複行の削除
  7. 誤変換辞書（dictionaries/replacement_dictionary.yml）の適用
  8. cleaned text の保存
  9. （任意）SFA_Builder_v1.md と合体させた「プロンプトパッケージ」の生成

使い方:
  python3 scripts/clean_limitless_log.py SFA/00_raw_logs/raw_20260702.txt \\
      --session-id SFA-20260702-001_yaoichi_prototype-kitchen \\
      --make-prompt-package

依存: PyYAML (pip install pyyaml)
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAMLが必要です。`pip install pyyaml` を実行してください。"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DICT_PATH = REPO_ROOT / "dictionaries" / "replacement_dictionary.yml"
DEFAULT_CLEANED_DIR = REPO_ROOT / "SFA" / "01_cleaned_text"
DEFAULT_PROMPT_PACKAGE_DIR = REPO_ROOT / "SFA" / "08_prompts"
DEFAULT_SFA_BUILDER_PROMPT = REPO_ROOT / "prompts" / "SFA_Builder_v1.md"

# タイムスタンプ・タイムライン表記のパターン
TIMESTAMP_PATTERNS = [
    re.compile(r"\[\d{1,2}:\d{2}(:\d{2})?\]"),          # [00:12] [00:12:34]
    re.compile(r"\(\d{1,2}:\d{2}(:\d{2})?\)"),          # (00:12) (00:12:34)
    re.compile(r"^\d{1,2}:\d{2}(:\d{2})?\s*[-–—]\s*"),   # 00:12:34 - (行頭)
    re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?"),  # 2026-07-02 10:23:11
]

# Unknown話者行のパターン（行全体がUnknown発言とみなせるもの）
UNKNOWN_LINE_PATTERNS = [
    re.compile(r"^\s*\*{0,2}Unknown\*{0,2}\s*[:：]"),
    re.compile(r"^\s*\*{0,2}Unknown\*{0,2}\s*$"),
]

# フィラー（意味を持たない語）。長い語から先にマッチさせるため長さ降順で使用する。
FILLER_WORDS = [
    "そのですね", "えーっと", "えっとー", "あのー", "えっと", "あの", "ええと",
    "えー", "まあまあ", "まあ", "なんか", "こう", "ちょっとその",
]

# 単独で行全体を占める場合に削除する相づち（前後の空白・句読点は無視して判定）
STANDALONE_AIZUCHI = {
    "はい", "うん", "そうですね", "そうそう", "うんうん", "はいはい", "ええ",
}

# 「話者名: 発言」形式の行から話者名と発言本文を分離するためのパターン
SPEAKER_LINE_PATTERN = re.compile(r"^(?P<speaker>[^\s:：][^:：]{0,30})[:：]\s*(?P<content>.*)$")


def load_replacement_dictionary(path: Path) -> list[tuple[str, str]]:
    """replacement_dictionary.yml を読み込み、(raw_form, correct_form) のリストを返す。

    raw_form が長い順に並べ替え、部分一致による誤置換を避ける。
    """
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = data.get("entries", []) or []
    pairs = [
        (e["raw_form"], e["correct_form"])
        for e in entries
        if e.get("raw_form") and e.get("correct_form")
    ]
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def load_anonymization_map(path: Path | None) -> list[tuple[str, str]]:
    """任意の匿名化マップ（実名 -> 匿名ラベル）を読み込む。"""
    if path is None or not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = data.get("entries", []) or []
    pairs = [
        (e["real_name"], e["anonymized_as"])
        for e in entries
        if e.get("real_name") and e.get("anonymized_as")
    ]
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def strip_timestamps(line: str) -> str:
    for pattern in TIMESTAMP_PATTERNS:
        line = pattern.sub("", line)
    return line


def is_unknown_line(line: str) -> bool:
    return any(pattern.search(line) for pattern in UNKNOWN_LINE_PATTERNS)


def remove_fillers(line: str) -> str:
    for filler in FILLER_WORDS:
        line = line.replace(filler, "")
    return line


def is_standalone_aizuchi(line: str) -> bool:
    """話者名を除いた発言本文が、単独の相づちだけで構成されているか判定する。"""
    stripped_line = line.strip()
    match = SPEAKER_LINE_PATTERN.match(stripped_line)
    content = match.group("content") if match else stripped_line
    content = content.strip().strip("。、！？!?.,")
    return bool(content) and content in STANDALONE_AIZUCHI


def cleanup_punctuation(line: str) -> str:
    """フィラー削除で生じた句読点の重複・行頭句読点を整える（機械的な範囲のみ）。"""
    line = re.sub(r"[、,]{2,}", "、", line)
    line = re.sub(r"([:：]\s*)、+", r"\1", line)
    line = re.sub(r"^\s*、+", "", line)
    return line


def dedupe_consecutive(lines: list[str]) -> list[str]:
    result: list[str] = []
    prev_stripped = None
    for line in lines:
        stripped = line.strip()
        if stripped and stripped == prev_stripped:
            continue
        result.append(line)
        prev_stripped = stripped
    return result


def collapse_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text)


def apply_pairs(text: str, pairs: list[tuple[str, str]]) -> tuple[str, int]:
    count = 0
    for raw_form, correct_form in pairs:
        if raw_form == correct_form:
            continue  # 保護語彙（no-op）
        occurrences = text.count(raw_form)
        if occurrences:
            text = text.replace(raw_form, correct_form)
            count += occurrences
    return text, count


def clean_text(raw_text: str, dict_pairs: list[tuple[str, str]],
                anon_pairs: list[tuple[str, str]]) -> tuple[str, dict]:
    stats = {
        "input_lines": 0,
        "removed_unknown_lines": 0,
        "removed_aizuchi_lines": 0,
        "removed_duplicate_lines": 0,
        "dict_replacements": 0,
        "anonymization_replacements": 0,
    }

    lines = raw_text.splitlines()
    stats["input_lines"] = len(lines)

    kept_lines: list[str] = []
    for line in lines:
        line = strip_timestamps(line).strip()

        if is_unknown_line(line):
            stats["removed_unknown_lines"] += 1
            continue

        if not line:
            kept_lines.append(line)
            continue

        if is_standalone_aizuchi(line):
            stats["removed_aizuchi_lines"] += 1
            continue

        line = remove_fillers(line)
        line = cleanup_punctuation(line).strip()

        if not line:
            continue

        kept_lines.append(line)

    before_dedupe = len(kept_lines)
    kept_lines = dedupe_consecutive(kept_lines)
    stats["removed_duplicate_lines"] = before_dedupe - len(kept_lines)

    text = "\n".join(kept_lines)
    text = collapse_blank_lines(text)

    text, dict_count = apply_pairs(text, dict_pairs)
    stats["dict_replacements"] = dict_count

    if anon_pairs:
        text, anon_count = apply_pairs(text, anon_pairs)
        stats["anonymization_replacements"] = anon_count

    return text.strip() + "\n", stats


def build_prompt_package(session_id: str, cleaned_text: str, sfa_builder_prompt: Path) -> str:
    prompt_body = sfa_builder_prompt.read_text(encoding="utf-8")
    return (
        f"{prompt_body}\n\n"
        "---\n\n"
        "## このセッションのメタデータ（人手で埋めてから実行すること）\n\n"
        f"- Session ID: `{session_id}`\n"
        "- 実施日: \n"
        "- クライアント: \n"
        "- 業種: \n"
        "- 対象: \n"
        "- 人数: \n"
        "- テーマ: \n"
        "- 使用プログラム: \n"
        "- 匿名化レベル: \n"
        "\n---\n\n"
        "## クリーニング済みテキスト（機械処理済み・意味編集は未実施）\n\n"
        "```\n"
        f"{cleaned_text}"
        "```\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("raw_log", type=Path, help="raw log ファイルパス（SFA/00_raw_logs/ 配下推奨）")
    parser.add_argument("--session-id", default=None,
                         help="例: SFA-20260702-001_yaoichi_prototype-kitchen（未指定時は入力ファイル名を使用）")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_CLEANED_DIR,
                         help="cleaned text の出力先ディレクトリ")
    parser.add_argument("--dict", type=Path, default=DEFAULT_DICT_PATH,
                         help="誤変換辞書 yml のパス")
    parser.add_argument("--anonymize-map", type=Path, default=None,
                         help="任意: 実名 -> 匿名ラベルの対応表 yml")
    parser.add_argument("--make-prompt-package", action="store_true",
                         help="SFA_Builder_v1.md と結合したプロンプトパッケージも生成する")
    parser.add_argument("--prompt-package-dir", type=Path, default=DEFAULT_PROMPT_PACKAGE_DIR,
                         help="プロンプトパッケージの出力先ディレクトリ")
    args = parser.parse_args()

    if not args.raw_log.exists():
        raise SystemExit(f"raw log が見つかりません: {args.raw_log}")

    session_id = args.session_id or args.raw_log.stem
    raw_text = args.raw_log.read_text(encoding="utf-8")

    dict_pairs = load_replacement_dictionary(args.dict)
    anon_pairs = load_anonymization_map(args.anonymize_map)

    cleaned_text, stats = clean_text(raw_text, dict_pairs, anon_pairs)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{session_id}.md"
    output_path.write_text(cleaned_text, encoding="utf-8")

    print(f"[OK] cleaned text を書き出しました: {output_path}")
    print("--- クリーニング統計 ---")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print(
        "\n※ 誤変換の意味的な修正・段落整理・SFA Session化は行っていません。\n"
        "  次工程として prompts/SFA_Builder_v1.md をLLMに渡してください。"
    )

    if args.make_prompt_package:
        if not DEFAULT_SFA_BUILDER_PROMPT.exists():
            print(f"[WARN] {DEFAULT_SFA_BUILDER_PROMPT} が見つからないため、プロンプトパッケージ生成をスキップしました。")
            return
        args.prompt_package_dir.mkdir(parents=True, exist_ok=True)
        package_path = args.prompt_package_dir / f"{session_id}_prompt_package.md"
        package_text = build_prompt_package(session_id, cleaned_text, DEFAULT_SFA_BUILDER_PROMPT)
        package_path.write_text(package_text, encoding="utf-8")
        print(f"[OK] プロンプトパッケージを書き出しました: {package_path}")


if __name__ == "__main__":
    main()
