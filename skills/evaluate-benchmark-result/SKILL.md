---
name: evaluate-benchmark-result
description: 受験者から独立して回答を採点する。
---
# 採点
対象版の rubrics を確認し、モデル名や速度を伏せた回答を採点する。各問題の上限を守り、根拠と採点者のモデル・版を記録する。実行していないテストを成功扱いしない。生成コードは通常環境で実行しない。採点結果を元の計測結果に結合し evaluation_type を independent とする。受験者自身の採点は self とする。
