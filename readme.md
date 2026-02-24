# 🧩 Git Project History Extractor

Gitリポジトリ内の **すべてのファイル変更履歴** を抽出し、
**JSON形式** でまとめるPythonスクリプトです。

各ファイルの

* コミット履歴（メッセージ・日時・ハッシュ）
* 初回コミット日時（created_at）
* 拡張子からの簡易言語判定
* プロジェクトディレクトリ構造（再帰的）

を1つのJSONにまとめ、ドキュメント生成などに再利用できます。

---

## 🚀 特徴

* 📂 **Gitリポジトリを1回走査**して履歴を全収集
* 🧠 **PyDriller** を利用（MITライセンス・商用利用可）
* 🪶 **Python標準ライブラリのみ依存（＋PyDriller）**
* 🧱 **指定ブランチ・任意ルートディレクトリ対応**
* 🗃️ **JSON出力形式を柔軟に加工可能**

---

## 🧰 インストール

```bash
git clone https://github.com/yourname/git-project-history-extractor.git
cd git-project-history-extractor
pip install -r requirements.txt
```

`requirements.txt` の内容：

```
pydriller>=2.0
```

---

## ⚙️ 使い方

```bash
python generate_git_summary.py <path_to_repo> [--branch BRANCH] [--output OUTPUT]
```

### 例：

```bash
python generate_git_summary.py ./my-nextjs-app --branch main --output project_history.json
```

### 引数

| 引数名      | 説明                              | デフォルト値       |
| :---------- | :-------------------------------- | :----------------- |
| `repo_path` | Gitリポジトリのルートディレクトリ | **必須**           |
| `--branch`  | 対象ブランチ名                    | `main`             |
| `--output`  | 出力JSONファイル名                | `git_summary.json` |

---

## 📄 出力されるJSON構造

```json
{
    "project_tree": {
        "root": {
            "name": "my-nextjs-app",
            "root_path": ".",
            "structure": [
                {
                    "type": "directory",
                    "name": "src",
                    "path": "src",
                    "children": [
                        {
                            "type": "file",
                            "name": "main.py",
                            "path": "src/main.py"
                        }
                    ]
                }
            ]
        }
    },
    "files": [
        {
            "relative_path": "src/main.py",
            "type": "file",
            "created_at": "2026-02-01T09:30:00Z",
            "metadata": {
                "language": "Python"
            },
            "git_history": [
                {
                    "commit_hash": "a1b2c3d4",
                    "commit_message": "Initial commit: add main script",
                    "author_date": "2026-02-01T09:31:20Z",
                    "commit_date": "2026-02-01T09:32:10Z"
                }
            ]
        }
    ],
    "directories": [
        {
            "relative_path": "src/",
            "children": [
                "src/main.py"
            ]
        }
    ]
}
```

---

## 🧩 JSONの利用例

生成された `git_summary.json` は以下のような用途に使えます：

* ドキュメント生成ツールの入力データ
* 開発履歴の可視化（グラフ・タイムライン）
* チーム内レビュー・コードベースの変遷解析

---

## 🧑‍💻 開発・ライセンス

* 開発言語: **Python 3.9+**
* 依存ライブラリ: **PyDriller (MIT License)**
* 本スクリプト: **MIT License**

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
...
```

---

## 🧠 補足

* 削除済みファイルはスキップされます。
* バイナリファイルも履歴上は検出されますが、内容の解析は行いません。
* 拡張子による言語判定は簡易的です。必要に応じて `LANGUAGE_MAP` を拡張してください。

---

## 📜 更新履歴

| 日付       | 内容         |
| :--------- | :----------- |
| 2026-02-24 | 初版リリース |

---

## 💬 貢献

改善案・バグ報告はぜひ [Issues](https://github.com/yourname/git-project-history-extractor/issues) へ！
