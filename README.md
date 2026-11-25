# LLM Benchmark

日本語理解・モバイル開発・設計・推論・成果物生成を評価する公開ベンチマーク。

初期版 v0.1.0（未リリース）。固定12問100点と別枠のPagoda Garden風HTML生成問題。受験者には [Agent Skill](skills/llm-benchmark/SKILL.md) または対象問題のみを渡し、採点者には [採点基準](rubrics/v0.1.0.md) を渡す。各問を新規会話で3回実施し、速度は外部実測で記録する。

- [問題一覧](benchmarks/v0.1.0/manifest.json)
- [測定結果](results/README.md)
- [開発ルール](AGENTS.md)

## 結果投稿・公開

- [投稿用Skill](skills/submit-benchmark-result/SKILL.md)
- [バージョン管理](docs/versioning.md)
- [Pages設定](docs/pages.md)
