---
name: run-llm-benchmark
description: ローカルLLMの実測ベンチマークを実行し、独立採点と結果投稿を調整する。
---
# 実行
Python 3.10以上で scripts/runner.py doctor を実行する。投稿予定なら --submit を追加する。認証情報を表示・保存しない。
利用者とモデル、ランタイムの固定版、GPU、設定を確認する。既存APIを起動し、scripts/runner.py run --base-url URL --model ID --runtime NAME --runtime-version VERSION を実行する。
受験者に採点基準やGitHub権限を与えない。local-runs の回答を別の採点者に渡し、投稿用Skillに引き継ぐ。未測定値を推測しない。

## 結果の出力

版・問題 ID・回番号を使い、問題文、各回の最終回答本文、計測値、独立採点と根拠を対応付けて渡す。モデル・ランタイム・設定と、確認できた OS・CPU・GPU・VRAM・RAM を記録する。検出された GPU と推論に使用した GPU の記録は区別し、不明な値は `null` とする。成果物の形式は [結果の形式](../../results/README.md) を参照する。公開する場合は投稿用 Skill に引き継ぐ。
