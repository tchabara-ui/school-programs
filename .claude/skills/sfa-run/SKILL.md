---
name: sfa-run
description: "Use this skill to run the full SFA (Soulmate Facilitation Archive) pipeline end-to-end in this repo: fetch a Limitless Pendant recording for a given date/time range, clean it, and generate all 7 SFA deliverables (SFA Session, AI analysis, quotes/questions/framings, Facebook post, Instagram post, blog post, core line). Trigger when the user asks to run SFA, process a Limitless recording, build an SFA session for a date, or references the SFA pipeline / Soulmate Facilitation Archive / SFA-YYYYMMDD."
---

# SFA Run — Soulmate Facilitation Archive 一気通貫パイプライン

Limitless Pendantで録音したファシリテーション研修ログを、毎回同じ手順・同じ品質で
7点の成果物に変換する。**このリポジトリ直下の `README.md` が唯一の正**。
本ファイルと矛盾する場合は README.md を優先する。

意味判断が必要な工程(クリーニング後の文脈修正・SFA Session化・分析・抽出・SNS化)は、
実行者自身(Claude)が `prompts/*.md` の指示に直接従って行う。他のLLMに貼り付ける
運用ではない——これがこのスキルの存在意義(以前は人手で貼り付けていた工程を、
Claude Code内で完結させる)。

## 実行前提

- Limitless MCP(`mcp__limitless__searchLifelogsWithTranscripts`)が利用可能なこと
- 背景ジョブとして実行する場合は、先に EnterWorktree でこのリポジトリを隔離してから
  ファイルを書き込むこと(共有チェックアウトへの直接書き込みは拒否される)

## ステップ0: セッション情報のヒアリング

ユーザーから対象の日付(必要なら時間帯)を受け取ったら、以下を確認する。
まとめて一度に聞いてよい。分からない項目は「未記入」でよいと伝える。

- クライアント名
- テーマ(セッション内容を一言で。英数字ハイフン区切りのスラッグも決める)
- 実施日・時間帯(Limitlessの検索範囲として使う)
- 業種・対象・人数・使用プログラム
- 匿名化レベル(デフォルト:なし。実名を使う方針を都度確認する)

**Session ID** を決定する: `SFA-YYYYMMDD-###_client_theme`
`SFA/00_raw_logs/` を確認し、同日の既存セッションがあれば `###` をインクリメントする。

## ステップ1: Limitlessからログ取得

`mcp__limitless__searchLifelogsWithTranscripts` で対象日を検索する。

- 1回の呼び出しは最大10件までしか返らない。`nextCursor` を使って対象の時間帯を
  カバーするまでページネーションする(1日を通して録音していると数百〜数千件になりうる。
  実際に2026-07-02のセッション例では2,069件だった)。
- `date` パラメータに加えて、セッションの開始・終了がおおよそ分かっていれば
  `startTime`/`endTime` で絞り込み、無関係な録音(私用の会話等)を混入させない。
- 各結果の `metadata.startTime` で時系列ソートする(取得順が時系列とは限らない)。
- 各結果の `text` フィールドは、すでに `- 話者 (M/D/YY H:MM AM/PM): 発言内容` の
  1行1発言形式になっている(`clean_limitless_log.py` がそのまま読める形式)。
  複数エントリの `text` を時系列順に連結すればよい。

## ステップ2: raw logとして保存

連結したテキストを `SFA/00_raw_logs/<SessionID>_raw.txt` に保存する。
**このファイルは以後絶対に上書き・改変しない**(原本保管の原則)。

## ステップ3: 機械クリーニング

```bash
python3 scripts/clean_limitless_log.py SFA/00_raw_logs/<SessionID>_raw.txt \
    --session-id <SessionID> --make-prompt-package
```

出力:
- `SFA/01_cleaned_text/<SessionID>.md`
- `SFA/08_prompts/<SessionID>_prompt_package.md`

(初回のみ `pip install pyyaml` が必要な場合がある)

## ステップ4: SFA Session + AI分析(自分で実行する)

`prompts/SFA_Builder_v1.md` を読み、その指示に**自分自身が**従う。
入力は `01_cleaned_text/` のクリーニング済みテキストとステップ0のメタデータ。

- 出力1: `SFA/02_sessions/<SessionID>.md`(`templates/session_template.md` の構造)
- 出力2: `SFA/03_analysis/<SessionID>_analysis.md`(`templates/analysis_template.md` の構造)
- プロンプト末尾の「品質チェックリスト」を自己申告し、チャットにも要約を出す

## ステップ5: 名言・問い・フレーミング集 + 今回の一文

`prompts/Knowledge_Builder_v1.md` の指示に従う。入力はステップ4のSFA Session。

- 出力: `SFA/04_quotes_questions_frames/<SessionID>_quotes.md`,
  `SFA/04_quotes_questions_frames/<SessionID>_coreline.md`
- レキシコン(`SFA/07_lexicon/concept_lexicon.md`)への追加提案が出た場合は、
  **勝手に反映せずユーザーに提示して確認を取ってから**追記する

## ステップ6: SNS・ブログ生成

`prompts/Content_Builder_v1.md` の指示に従う。入力はSFA Session + 名言集。

- 出力: `SFA/05_sns/facebook/<SessionID>_fb.md`,
  `SFA/05_sns/instagram/<SessionID>_ig.md`,
  `SFA/06_blog/<SessionID>_blog.md`

## ステップ7: レビュー用ビューワー公開

SFA Session(正本)をArtifactとして公開し、ユーザーがすぐ確認できるようにする。

## ステップ8: 書き出し・コミット

ユーザーが内容を確認したら:

1. 確定ファイルを `SFA/09_exports/` へコピー(そのまま投稿できる形に整えたもの)
2. 新しいブランチで全成果物(raw〜exportsまで)をコミット・push・draft PR作成
   (このリポジトリのデフォルトブランチに対して)

## 守るべき原則(README.mdより再掲)

- `00_raw_logs/` は改変しない。誤りがあっても新しいセッションとして扱う
- SFA Sessionが唯一の正本。SNS/ブログの表現をSFA Sessionへ書き戻さない
- 創作しない。聞き取れない・判断できない箇所は `【認識不明】` と明記する
- 匿名化指定がある場合、最終確認で実名が残っていないかチェックする
- 研究用文章(AI分析・名言集)とSNS/ブログの文章のトーンを混ぜない
