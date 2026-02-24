## 🧩 プロジェクト概要

このツールは、指定した Git リポジトリを解析し、
以下の情報を JSON 形式で出力する Python スクリプトです。

- 各ファイルのコミット履歴(メッセージ・日時・ハッシュ)
- 各ファイルの初回コミット日時
- ファイルの種類(拡張子からの簡易推定)
- プロジェクト構造(フォルダ・ファイル階層)

出力された JSON は、ドキュメント生成などに再利用できます。

---

## 🚀 主な機能


## 🚀 特徴

- 📂 Gitリポジトリを1回走査して履歴を全収集
- 🔍 `.gitignore`対応(ルートディレクトリ直下の`.gitignore`のみ対応)
- 🧠 PyDriller を利用（MITライセンス・商用利用可）
- 🪶 Python標準ライブラリのみ依存（＋PyDriller）
- 🧱 指定ブランチ・任意ルートディレクトリ対応

---

## 🧱 依存ライブラリ

このプロジェクトは以下の外部ライブラリに依存しています：

```bash
pip install pydriller pathspec
```

### 使用ライブラリ概要

| ライブラリ | 用途                    |
| ---------- | ----------------------- |
| PyDriller  | Git コミット履歴解析    |
| PathSpec   | `.gitignore` ルール処理 |

---

## ⚙️ 使い方

### 1️⃣ リポジトリクローン or ローカルプロジェクト準備

解析したい Git プロジェクトをローカルに用意します。

### 2️⃣ スクリプトの設定

`main.py` の末尾で以下を指定します：

```python
from pathlib import Path

if __name__ == "__main__":
    repo_path = Path(
        r"C:\Users\user\Documents\workspace\project\test_app"
    )  # プロジェクトのルートディレクトリ
    branch = "main"  # 解析対象のgitブランチ名
    output = Path(r"output\project_history.json")  # 出力ファイル(json)

    generate_git_summary_json(repo_path, branch, output)
```

### 3️⃣ 実行

```bash
python main.py
```

実行後、`output/` フォルダ内に `project_history.json` が生成されます。

---

## 📄 出力されるJSON構造(例)

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

## 🧑‍💻 開発・ライセンス

- 開発言語: Python 3.9+
- 依存ライブラリ: PyDriller (MIT License)
- 本スクリプト: MIT License

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
...
```
