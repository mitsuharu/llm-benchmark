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

## Runner（初期実装）

Python 3.10以上。起動済みOpenAI互換APIを使用する。

```sh
python scripts/runner.py doctor --submit
python scripts/runner.py run --base-url http://localhost:8080/v1 --model MODEL_ID --runtime llamacpp --case ja-01
```

結果は local-runs に保存。採点・投稿は別Skillで行う。Strata / Project Maya は互換APIが利用可能な場合に接続できる。実機検証、自動起動は今後の対応。既定3回の独立リクエストを行い中央値と個別結果を保存する。タイムアウト時は子プロセスを終了する（部分回答の保存は未対応）。

- [実行Skill](skills/run-llm-benchmark/SKILL.md)
- [採点Skill](skills/evaluate-benchmark-result/SKILL.md)

### llama.cpp の準備

公式リリースの固定タグ・ZIP名・信頼できるSHA-256を指定する。

```sh
python scripts/runtime.py --version BUILD_TAG --asset ASSET.zip --sha256 EXPECTED_SHA256
```

取得は計測前に行う。追加のGPU依存ライブラリが必要な配布物やZIP以外は手動準備する。取得した llama-server を起動してから Runner に接続する。`--model-file` はローカルGGUFのSHA-256を記録する（APIが実際にそのファイルを使用することは利用者が確認する）。

### 自動起動モード

既存バイナリとGGUFを再利用する。

```sh
python scripts/runner.py run --server-binary /path/to/llama-server --model-file /path/to/model.gguf --model MODEL_ID --context-length 4096 --gpu-layers 99 --case ja-01
```

または `--server-binary` の代わりに `--auto-prepare --runtime-version BUILD_TAG --asset ASSET.zip --archive-sha256 SHA256` を指定する。ローカルサーバーの起動時間は推論時間と別に記録し、終了時に停止する。実機検証は未実施。モデルの自動取得は行わない。

### 結果投稿の準備

独立採点済みJSONを確認し、機密情報を除去した後、`python scripts/submission.py PATH/result.json --run-id RUN_ID --reviewed` で公開用ディレクトリに配置・検証する。回答やログは自動コピーしない。PR作成は投稿Skillに従い利用者の承認後に行う。

ハードウェア情報はRunnerを実行したホストの情報。NVIDIA GPUは nvidia-smi で検出する。AMD/Intel GPUやリモート推論機の情報は手動指定する。
