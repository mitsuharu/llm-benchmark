---
name: submit-benchmark-result
description: 計測済みのLLMベンチマーク結果を検証し、利用者の承認を得て結果投稿PRを作成する。
---

# 結果投稿

受験者とは別の担当エージェントとして実行する。計測値や採点結果を捏造しない。
results/README.md と対象版の manifest.json を確認し、results/example.json を参考に結果を作成する。未計測は null。自己採点は evaluation_type に self と記録する。
公開可能な回答のみ添付し、秘密、個人情報、内部推論ログを除去する。
scripts/validate.py を実行する。利用者に公開内容を提示し承認を得た後、専用ブランチに results/ の対象runだけを追加しPRを作成する。自分でマージしない。
削除は対象runを指定し、別PRでディレクトリ全体を削除する。Git履歴や複製からの完全削除ではないことを説明する。
