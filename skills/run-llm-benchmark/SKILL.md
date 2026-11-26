---
name: run-llm-benchmark
description: ローカルLLMの実測ベンチマークを実行し、独立採点と結果投稿を調整する。
---
# 実行
Python 3.10以上で scripts/runner.py doctor を実行する。投稿予定なら --submit を追加する。認証情報を表示・保存しない。
利用者とモデル、ランタイムの固定版、GPU、設定を確認する。既存APIを起動し、scripts/runner.py run --base-url URL --model ID --runtime NAME --runtime-version VERSION を実行する。
受験者に採点基準やGitHub権限を与えない。local-runs の回答を別の採点者に渡し、投稿用Skillに引き継ぐ。未測定値を推測しない。
