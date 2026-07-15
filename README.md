# SFA｜Soulmate Facilitation Archive

Limitless Pendantで録音した研修ログを、毎回同じ手順・同じ品質で以下7点に変換するための
ワークフローとテンプレート一式。

これは単なる文字起こしの整形ではない。目的は、ファシリテーター「チャー」の
問い・介入・フレーミング・場づくり・参加者反応・現場転移の言葉を蓄積し、
将来のテキストマイニング・研修研究・SNS発信・ブログ記事・書籍化・
ファシリテーター育成に使える**知的資産**を作ることである。

## 生成される7点の成果物

1. SFA Session｜ファシリテーションアーカイブ（**唯一の正本**）
2. AI分析
3. 名言・問い・フレーミング集
4. Facebook投稿
5. Instagram投稿
6. コーポレートサイトブログ
7. 今回の一文｜セッションの核心コピー

**派生の方向は一方向のみ。** SFA Session → AI分析／名言集 → SNS・ブログ。
逆方向（SNSやブログの表現をSFA Sessionに書き戻す）は禁止。

---

## 運用方針（最重要）

- 完璧な自動化より、**毎回確実に同じ品質で運用できること**を優先する。
- 原本ログ（`00_raw_logs/`）は改変せず必ず残す。編集版と原本を分離する。
- SNS用文章と研究用文章（AI分析・名言集）は混ぜない。トーンも保存先も別にする。
- SFA Sessionを唯一の正本とし、SNS・ブログはそこから派生させる。
- 後から検索・分析できるよう、タグとメタデータを必ず残す。
- 意味判断が必要な編集（誤変換の文脈修正・段落整理・SFA Session化・分析・SNS化）は
  スクリプトで完全自動化せず、LLM（Claude等）に投げる前提とする。
  スクリプトが担当するのは機械的な処理のみ。

---

## フォルダ構成

```
school-programs/
├── README.md                      ← 本ファイル
├── prompts/                        ← LLMに渡すマスタープロンプト（3本）
│   ├── SFA_Builder_v1.md           ← cleaned text → SFA Session + AI分析
│   ├── Knowledge_Builder_v1.md      ← SFA Session → 名言・問い・フレーミング集 + 今回の一文
│   └── Content_Builder_v1.md        ← SFA Session + 名言集 → Facebook/Instagram/ブログ
├── templates/                      ← 各成果物のMarkdown雛形
│   ├── session_template.md
│   ├── analysis_template.md
│   ├── sns_template.md
│   └── blog_template.md
├── dictionaries/
│   └── replacement_dictionary.yml  ← ASR誤変換修正辞書（追加・更新可能）
├── scripts/
│   ├── clean_limitless_log.py      ← raw log の機械的クリーニング（Python）
│   ├── fetch_lifelog.py            ← Limitless REST APIから直接ログ取得
│   ├── intake_convert.py           ← 受信箱ファイル(音声/Word/テキスト)→プレーンテキスト変換
│   └── transcribe_audio.py         ← 音声ファイルの文字起こし（OpenAI Whisper API）
└── SFA/                             ← 実データ置き場（セッションごとに増えていく）
    ├── 00_inbox/                    ← 受信箱。Limitless以外の音声/Word/テキストをここに置く
    ├── 00_raw_logs/                 ← 生ログ（Limitless由来／受信箱由来とも）。改変禁止・原本保管
    ├── 01_cleaned_text/             ← スクリプトによる機械クリーニング後のテキスト
    ├── 02_sessions/                 ← 【正本】SFA Session（確定版）
    ├── 03_analysis/                 ← AI分析
    ├── 04_quotes_questions_frames/  ← 名言・問い・フレーミング集／今回の一文
    ├── 05_sns/
    │   ├── facebook/
    │   └── instagram/
    ├── 06_blog/                     ← コーポレートサイトブログ原稿
    ├── 07_lexicon/                  ← 概念レキシコン（Prototype Kitchen等の定義・タグ定義。生きた辞書）
    ├── 08_prompts/                  ← セッションごとに生成する「プロンプトパッケージ」（実行ログ）
    └── 09_exports/                  ← 外部共有用の書き出し（PDF化・SNS投稿直前ファイル等）
```

`prompts/` `templates/` `dictionaries/` `scripts/` は**マスター資産**（全セッション共通）、
`SFA/` は**セッションごとに積み上がっていくデータレイク**という位置づけ。

---

## 命名規則

### Session ID

```
SFA-YYYYMMDD-###_client_theme
```

例：`SFA-20260702-001_yaoichi_prototype-kitchen`

- `YYYYMMDD`: 実施日
- `###`: 同日に複数セッションがある場合の連番（001, 002, ...）
- `client`: クライアント名（英数字・ローマ字。匿名化が必要な場合は仮名でも可）
- `theme`: テーマ（英数字・ハイフン区切り）

このIDを全成果物のファイル名プレフィックスとして使う。日本語ファイル名を併用してもよいが、
機械処理・検索のため英数字IDを必ず含めること。

### ファイル名の例（1セッション分）

```
SFA/00_raw_logs/SFA-20260702-001_yaoichi_prototype-kitchen_raw.txt
SFA/01_cleaned_text/SFA-20260702-001_yaoichi_prototype-kitchen.md
SFA/02_sessions/SFA-20260702-001_yaoichi_prototype-kitchen.md
SFA/03_analysis/SFA-20260702-001_yaoichi_prototype-kitchen_analysis.md
SFA/04_quotes_questions_frames/SFA-20260702-001_yaoichi_prototype-kitchen_quotes.md
SFA/04_quotes_questions_frames/SFA-20260702-001_yaoichi_prototype-kitchen_coreline.md
SFA/05_sns/facebook/SFA-20260702-001_yaoichi_prototype-kitchen_fb.md
SFA/05_sns/instagram/SFA-20260702-001_yaoichi_prototype-kitchen_ig.md
SFA/06_blog/SFA-20260702-001_yaoichi_prototype-kitchen_blog.md
```

---

## 処理フロー（12ステップ）

| # | ステップ | 担当 |
|---|---|---|
| 1 | raw log投入（`00_raw_logs/`に保存） | 人 |
| 2 | Unknown・タイムライン・時刻削除 | スクリプト |
| 3 | フィラー削除 | スクリプト |
| 4 | 誤変換修正（辞書ベース） | スクリプト |
| 5 | ぶつ切り文章の統合 | LLM（意味判断が必要） |
| 6 | 段落整理 | LLM |
| 7 | SFA Session化 | LLM（`SFA_Builder_v1.md`） |
| 8 | AI分析 | LLM（`SFA_Builder_v1.md`） |
| 9 | 名言・問い・フレーミング抽出／今回の一文 | LLM（`Knowledge_Builder_v1.md`） |
| 10 | SNS投稿生成 | LLM（`Content_Builder_v1.md`） |
| 11 | ブログ記事生成 | LLM（`Content_Builder_v1.md`） |
| 12 | 保存・書き出し | 人（`09_exports/`へ） |

ステップ2〜4（機械的処理）は `scripts/clean_limitless_log.py` が担当し、
ステップ5以降（意味判断が必要な処理）はLLMに3本のマスタープロンプトを渡して行う。

---

## 自動実行(Claude Codeスキル)

Claude Code上でこのリポジトリを開けば、`.claude/skills/sfa-run/SKILL.md` のスキルが
以下を一気通貫で行う。情報源はLimitlessに限らない。

1. 対象日のLimitlessログを自動取得、または `SFA/00_inbox/` に置いた音声・Word・
   テキストファイルを自動変換(手動貼り付け不要)
2. 機械クリーニング → SFA Session/AI分析/名言集/SNS/ブログの生成まで自動
3. SFA Session(正本)をビューワー公開してレビュー
4. 確認後、`09_exports/`への書き出しとコミット・PR作成

### Limitless以外の音声・文書を取り込む(受信箱)

他社からもらった音声ファイルや、既に文字起こし済みのWord文書・テキストは、
`SFA/00_inbox/` に置いて「inboxを処理して」のように声をかければよい。
ファイル形式ごとに以下のように変換される(スクリプトが機械的に行う。
どのファイルをどのセッションにまとめるかはClaudeとの聞き取りで確認する)。

| 形式 | 変換方法 |
|---|---|
| 音声(`.m4a` `.mp3` `.wav` `.mp4` `.mov` `.aac` `.flac` `.ogg`) | OpenAI Whisper APIで文字起こし(`scripts/transcribe_audio.py`)。要 `ffmpeg` と `OPENAI_API_KEY` |
| Word(`.docx`) | markitdownでテキスト抽出 |
| テキスト(`.txt` `.md`) | そのまま読み込み |

音声の文字起こしは話者分離を行わない(全発言が地の文になる)。
処理済みの原本は `SFA/00_inbox/_done/<SessionID>/` に移動され、受信箱には残らない
(削除はしない)。`OPENAI_API_KEY` は環境変数または `~/.openai_key` から読み込む。
**APIキーをこのリポジトリ内のファイルに書き込んではいけない**(公開リポジトリのため)。

下記「クイックスタート」は、スキルを使わず手動で1ステップずつ進める場合の手順
(スキルが使えない環境向け・処理内容の参照用)。

---

## クイックスタート

### 1. raw logを配置する

Limitlessから書き出したログを `SFA/00_raw_logs/` に保存する。
ファイル名は `SFA-YYYYMMDD-###_client_theme_raw.txt` 推奨（このIDはまだ仮でよい）。

### 2. 機械クリーニングを実行する

```bash
pip install pyyaml   # 初回のみ

python3 scripts/clean_limitless_log.py \
    SFA/00_raw_logs/SFA-20260702-001_yaoichi_prototype-kitchen_raw.txt \
    --session-id SFA-20260702-001_yaoichi_prototype-kitchen \
    --make-prompt-package
```

これにより以下が生成される。

- `SFA/01_cleaned_text/SFA-20260702-001_yaoichi_prototype-kitchen.md`（機械クリーニング済みテキスト）
- `SFA/08_prompts/SFA-20260702-001_yaoichi_prototype-kitchen_prompt_package.md`
  （`SFA_Builder_v1.md` + クリーニング済みテキストを合体させた、LLMにそのまま貼り付けられるパッケージ）

### 3. SFA Session と AI分析を作る

`SFA/08_prompts/..._prompt_package.md` の中の空欄（実施日・クライアント・業種など）を埋めてから、
LLM（Claude等）に貼り付けて実行する。出力を以下に保存する。

- `SFA/02_sessions/SFA-20260702-001_yaoichi_prototype-kitchen.md`
- `SFA/03_analysis/SFA-20260702-001_yaoichi_prototype-kitchen_analysis.md`

### 4. 名言・問い・フレーミング集／今回の一文を作る

確定した SFA Session を `prompts/Knowledge_Builder_v1.md` と一緒にLLMへ渡す。出力を保存する。

- `SFA/04_quotes_questions_frames/SFA-20260702-001_yaoichi_prototype-kitchen_quotes.md`
- `SFA/04_quotes_questions_frames/SFA-20260702-001_yaoichi_prototype-kitchen_coreline.md`

レキシコン更新提案が出た場合は、内容を確認したうえで `SFA/07_lexicon/concept_lexicon.md` に反映する。

### 5. SNS・ブログを作る

SFA Session + 名言集 + 今回の一文を `prompts/Content_Builder_v1.md` と一緒にLLMへ渡す。出力を保存する。

- `SFA/05_sns/facebook/SFA-20260702-001_yaoichi_prototype-kitchen_fb.md`
- `SFA/05_sns/instagram/SFA-20260702-001_yaoichi_prototype-kitchen_ig.md`
- `SFA/06_blog/SFA-20260702-001_yaoichi_prototype-kitchen_blog.md`

### 6. 書き出し

公開・共有直前のファイルを `SFA/09_exports/` にコピーする（そのまま投稿できる形に整えたもの）。

---

## 編集ルール（必須・全工程共通）

- Unknownを削除する
- タイムライン・時刻を削除する
- 「あの」「えっと」「そのですね」など意味を持たないフィラーを削除する
- 単独の「はい」「うん」「そうですね」などの相づちを削除する
- 重複認識を削除する
- ぶつ切りになった文章を自然につなげる（発言の意図・語順は変えない）
- 音声認識の誤変換を文脈から修正する
- ただし**意味が不明な箇所は創作せず `【認識不明】` と表記する**
- 話し言葉の熱量は残す（丁寧語に整えすぎない）
- 研修記録として読みやすい文章に整える
- 参加者個人名・企業名は必要に応じて匿名化できるようにする

---

## 誤変換辞書

`dictionaries/replacement_dictionary.yml` に登録。`entries:` に追記するだけで拡張できる。
`raw_form` と `correct_form` が同一のエントリは「保護語彙」（表記揺れ防止のための固定登録で、
置換処理には影響しない no-op）。詳細はファイル内コメントを参照。

意味が確定できない誤変換は辞書に入れず、`SFA_Builder_v1.md` の `【認識不明】` ルールに委ねる。

---

## タグ一覧

`【問い】【フレーミング】【比喩】【ユーモア】【心理的安全性】【組織開発】【感情喚起】
【現場転移】【リーダーシップ】【学習理論】【介入】【観察】【参加者反応】【名言】
【Prototype Kitchen】【啐啄同時】【Iメッセージ】`

定義は `SFA/07_lexicon/concept_lexicon.md` を参照。新しいタグを追加する場合は、
このファイル・`templates/session_template.md`・各プロンプトのタグ一覧を同時に更新すること。

---

## Prototype Kitchen（概念定義）

Prototype Kitchenとは、現場で実践する前に、新しい行動・対話・リーダーシップ・チームのあり方を
安心して試作し、フィードバックを受けながら磨き、現場へ持ち帰るための学習環境である。

料理人が、お客様に料理を出す前に、厨房で試作し、味見し、フィードバックを受けて改善するように、
研修では現場に持ち帰る行動を試作する。

（詳細・関連タグは `SFA/07_lexicon/concept_lexicon.md` を参照）

---

## SNS・ブログ生成ルールの要点

| 媒体 | 文字数 | 特徴 |
|---|---|---|
| Facebook | 1500〜2500文字 | ストーリー重視、現場の臨場感、最後に読者への問い、宣伝色を抑える |
| Instagram | 500〜900文字 | 保存されやすい構成、短い見出し、最後に問い、カルーセル案も可 |
| ブログ | 3000〜5000文字 | SEO意識、タイトル案5つ、導入→事例→学び→組織開発→現場の問い→まとめ→問い合わせ導線 |

詳細ルールは各テンプレート（`templates/sns_template.md` / `templates/blog_template.md`）と
`prompts/Content_Builder_v1.md` を参照。守秘義務に配慮し、必要に応じて企業名・個人名を匿名化する。

---

## 実装方式について（A案／B案）

このリポジトリは **A案（Markdown運用）を主軸に、B案（Pythonスクリプト）で機械処理部分のみ自動化**
するハイブリッド構成を採用している。

- 全成果物はMarkdownで保存し、Gitで版管理する（A案）。
- 機械的に確定できる処理（Unknown削除・時刻削除・フィラー削除・辞書適用）のみ
  `scripts/clean_limitless_log.py` で自動化する（B案）。
- 意味判断が必要な処理（誤変換の文脈修正・段落整理・SFA Session化・分析・抽出・SNS化）は
  自動化せず、3本のマスタープロンプトを使ってLLMに委ねる。

---

## スクリプト詳細

`scripts/clean_limitless_log.py` の詳細な使い方はスクリプト冒頭のdocstringを参照。

```bash
python3 scripts/clean_limitless_log.py <raw_log_path> \
    --session-id <SessionID> \
    [--output-dir SFA/01_cleaned_text] \
    [--dict dictionaries/replacement_dictionary.yml] \
    [--anonymize-map path/to/anonymize_map.yml] \
    [--make-prompt-package] \
    [--prompt-package-dir SFA/08_prompts]
```

`--anonymize-map` は任意。`entries: [{real_name: ..., anonymized_as: ...}]` 形式のYAMLを渡すと、
機械的な実名→匿名ラベル置換も同時に行える。
