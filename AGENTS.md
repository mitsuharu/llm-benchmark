# Repository guidelines

このリポジトリは、LLMの能力評価用ベンチマークと Agent Skills、測定結果を管理する。
説明文と手順は原則日本語で書き、Skill名・パス・コマンドは英語表記を使う。

## ブランチ・コミット・PR

- 作業開始時にブランチと未コミットの変更を確認し、他の作業を上書きしない。
- すべての変更は作業用ブランチで行い、PR 経由で追加する。ブランチ名は用途に応じて `feature/<内容>`、`fix/<内容>`、`docs/<内容>`、`ci/<内容>`、`refactor/<内容>`、`results/<run-id>` などを使う。
- デフォルトブランチへの直接コミット・push を禁止する。PR のマージは別途依頼がある場合だけ行う。
- コミットは目的・機能ごとに分け、各コミットの目的が単体で分かるようにする。関連する実装とテスト、Skill の追加と一覧の更新は同じコミットに含めてよい。
- コミットメッセージは Conventional Commits 形式を使う。接頭辞の例は `feat:`、`fix:`、`docs:`、`test:`、`ci:`、`refactor:`、`chore:`、`results:`。本文は日本語でよい。
- エージェントが変更を作成・編集した場合、またはコミットを作成した場合は、コミットメッセージ末尾に空行を挟んで、実際に作業したエージェント名とそのエージェント用のメールアドレスを `Co-authored-by: 名前 <メールアドレス>` の形式で記載する。Codex の例は `Co-authored-by: Codex <noreply@openai.com>`。
- エージェントが作るマージコミットや squash merge で作られるコミットにも、該当する `Co-authored-by` を引き継ぐ。コミット作成前とマージ前に、付け忘れがないことを確認する。
- PR は目的ごとに分け、説明に目的、変更内容、テスト内容、要確認事項を記載する。

## Skill development

- 新規追加前に既存の `skills/` とREADMEの一覧を確認し、目的の重複と命名・構成の一貫性を確認する。
- `skills/<skill-name>/SKILL.md` を配置の基本とし、ディレクトリ名とfrontmatterの `name` を一致させる。
- Skill追加には 継承元 https://github.com/mitsuharu/agent-skills の追加手順を参照する。
- Skill固有の詳細は各 `SKILL.md` や `references/` に置き、このファイルに集約しない。
- `SKILL.md` を簡潔に保ち、補助資料・スクリプト・素材は実際に必要な場合だけ追加する。
- Skillを追加・変更したらREADMEの一覧と使い方を同期する。不要な設定や生成物を追加しない。

## GitHub Actions

- 外部のactionはタグではなくフルのコミットSHAで固定し、行末にバージョンをコメントで書く。例: `uses: actions/checkout@<40桁のSHA> # v7.0.1`
- SHAはタグが指すコミットを公式リポジトリで確認して使う（`git ls-remote --tags https://github.com/<owner>/<repo>` など）。更新時もSHAとコメントを一緒に変える。
- Node.jsのバージョンはルートの `.node-version` で指定する（現在は24）。非推奨のNode.jsで動くactionは、そのランタイムに対応したバージョンへ上げる。
- PRを検証するCIは `pull_request` の `types: [opened, synchronize, reopened]` で起動し、`push` トリガーは付けない。対象Skillのファイルだけで動くよう `paths` を指定する。
- 同じPRで重複して走らないよう、workflowには次の `concurrency` を付ける。

  ```yaml
  concurrency:
    group: ci-${{ github.workflow }}-${{ github.ref }}
    cancel-in-progress: true
  ```

- actionの更新はDependabot（`.github/dependabot.yml` の `github-actions`）で月1回確認する。新しい依存のエコシステムを追加したら同じファイルに設定を足す。

## Validation

- PR作成前に 継承元 agent-skills の `skills/add-skill/references/validation.md` に従い、frontmatter・リンク・Skillの動作手順を確認する。
- `npx skills add . --list` で配布対象が検出されることを確認する。これはインストールを行わない。
- CLI仕様を書くときは公式ドキュメントを確認する。
- `git diff --check` と差分・コミット履歴を確認し、不要なファイルや機密情報がないことを確かめる。
- 実施した検証と未実施の項目を区別して報告する。

## Benchmark

- 公開済み問題と採点基準は固定し、変更は新バージョンで管理する。
- 受験者に採点基準を渡さない。問題ID、版、実測条件を記録する。
- 未測定は null とする。生成コードは通常のCIで実行しない。
- 公開結果から機密情報を除去する。
- ベンチマークの納品物には、版と問題 ID で特定できる問題文、各回の回答本文、採点と根拠、計測値、実行環境を含める。各回のデータは問題 ID と回番号で対応付ける。実行・採点・投稿の各 Skill と [結果の形式](results/README.md) に従う。
- Pages に掲載する場合は、回答本文を含む公開候補を提示し、利用者が承認した内容を投稿する。マージ後に計測の詳細ページを開き、承認済みの回答本文と各回の記録が表示されることを確認する。

## PR・CI・デプロイの完了条件

- 作業開始時とPR作成前にデフォルトブランチを取得し、Workflowのブランチ名（例: `main`）との整合性を確認する。
- PRマージ前に変更差分・未解決レビュー・最新head SHAのCI結果を確認する。必要なCIが失敗・未実行・確認不能の場合はマージせず、原因と未確認事項を報告する。単にPRがmergeableであることをCI成功と見なさない。
- PRのCIだけでなく、**マージ後に起動するpush、release、workflow_dispatch等の関連Workflowも確認する**。マージは作業完了ではない。
- GitHub Pagesを変更した場合は、`publish-pages` の `build` と `deploy` がともに成功したことを実行ID・ログ・対象コミットSHAで確認し、公開URLをHTTPで開いて内容を確認する。Pagesが未設定なら先に [Settings → Pages](https://github.com/mitsuharu/llm-benchmark/settings/pages) の Source が GitHub Actions かを確認する。
- デプロイで404などのエラーが発生したら失敗したジョブのログを取得し、設定不足・権限・Workflowの問題を切り分ける。コード修正だけで解消したと推測しない。
- マージ後のWorkflowを利用可能なツールで確認できない場合、**成功したと主張しない**。必要なrun URLや追加権限を依頼し、未確認と明示する。確認できるところまでログを検証する。
- 変更ごとにPR番号・マージSHA・CI run URL・デプロイrun URL・公開URLの確認結果を報告する。失敗時は原因と再検証の結果を報告し、成功を確認するまで完了扱いにしない。
- GitHub Pages等の外部設定はWorkflowでは検証しきれない場合がある。環境準備をREADME / docsに明示し、初回公開の受入試験に含める。
