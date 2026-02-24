import os
import json
from pydriller import Repository
from pathspec import PathSpec

# 拡張子 → 言語の簡易マッピング
LANGUAGE_MAP = {
    ".js": "JavaScript",
    ".jsx": "JavaScript (React)",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".html": "HTML",
    ".css": "CSS",
    ".md": "Markdown",
    ".json": "JSON",
}


def get_language_from_extension(filename):
    _, ext = os.path.splitext(filename)
    return LANGUAGE_MAP.get(ext, None)


# ------------------------------------------------------------
# .gitignore 読み込み＆判定ロジック
# ------------------------------------------------------------
def load_gitignore(root_path):
    """
    ルートディレクトリ直下の .gitignore を読み込み、PathSpec を返す。
    """
    gitignore_path = os.path.join(root_path, ".gitignore")
    if not os.path.exists(gitignore_path):
        return None
    with open(gitignore_path, "r", encoding="utf-8") as f:
        spec = PathSpec.from_lines("gitwildmatch", f)
    return spec


def is_ignored(path, spec, root_path):
    """
    .gitignore のルールに一致するか判定。
    常に .git ディレクトリは除外する。
    """
    # 無条件で .git ディレクトリをスキップ
    if ".git" in os.path.relpath(path, root_path).split(os.sep):
        return True

    if spec is None:
        return False

    rel_path = os.path.relpath(path, root_path)
    return spec.match_file(rel_path)


# ------------------------------------------------------------
# プロジェクト構造の探索
# ------------------------------------------------------------
def build_project_structure(root_path, current_path=".", spec=None):
    """
    プロジェクトツリー構造を再帰的に構築。
    .gitignore で無視されているものはスキップ。
    """
    abs_path = os.path.join(root_path, current_path)
    items = []

    for entry in sorted(os.listdir(abs_path)):
        full_path = os.path.join(abs_path, entry)
        if is_ignored(full_path, spec, root_path):
            continue  # 無視対象をスキップ

        rel_path = os.path.relpath(full_path, root_path)
        if os.path.isdir(full_path):
            children = build_project_structure(root_path, rel_path, spec)
            items.append(
                {
                    "type": "directory",
                    "name": entry,
                    "path": rel_path,
                    "children": children,
                }
            )
        else:
            items.append({"type": "file", "name": entry, "path": rel_path})
    return items


def build_directories_list(root_path, spec=None):
    """
    ディレクトリ一覧を構築。
    """
    directories = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        if is_ignored(dirpath, spec, root_path):
            continue

        rel_path = os.path.relpath(dirpath, root_path)
        if rel_path == ".":
            rel_path = ""

        children = []
        for d in dirnames:
            full_d = os.path.join(dirpath, d)
            if not is_ignored(full_d, spec, root_path):
                children.append(os.path.join(rel_path, d) + "/")

        for f in filenames:
            full_f = os.path.join(dirpath, f)
            if not is_ignored(full_f, spec, root_path):
                children.append(os.path.join(rel_path, f))

        directories.append(
            {
                "relative_path": rel_path + "/" if rel_path else "./",
                "children": children,
            }
        )
    return directories


# ------------------------------------------------------------
# Git 履歴の収集 (PyDriller)
# ------------------------------------------------------------
def extract_git_history(repo_path, branch):
    """
    PyDrillerを使って全ファイルの変更履歴を収集。
    """
    file_histories = {}

    for commit in Repository(
        path_to_repo=repo_path, only_in_branch=branch
    ).traverse_commits():
        for mod in getattr(
            commit, "modified_files", getattr(commit, "modifications", [])
        ):
            if not mod.new_path:
                continue  # 削除されたファイルなどをスキップ
            rel_path = mod.new_path
            entry = {
                "commit_hash": commit.hash[:8],
                "commit_message": commit.msg.strip(),
                "author_date": commit.author_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "commit_date": commit.committer_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            file_histories.setdefault(rel_path, []).append(entry)

    # コミット日時でソート（古い順）
    for rel_path in file_histories:
        file_histories[rel_path].sort(key=lambda x: x["author_date"])

    return file_histories


# ------------------------------------------------------------
# JSON生成メイン関数
# ------------------------------------------------------------
def generate_git_summary_json(repo_path, branch, output_file="git_summary.json"):
    repo_path = os.path.abspath(repo_path)
    root_name = os.path.basename(repo_path)

    print(f"Analyzing repository: {root_name} (branch: {branch})")

    # .gitignoreの読み込み
    spec = load_gitignore(repo_path)
    if spec:
        print(f"Loaded .gitignore from {repo_path}")
    else:
        print("No .gitignore found — analyzing all files.")

    # 構造情報
    project_tree = {
        "root": {
            "name": root_name,
            "root_path": ".",
            "structure": build_project_structure(repo_path, ".", spec),
        }
    }

    # Git履歴収集
    git_history = extract_git_history(repo_path, branch)

    files_data = []
    for rel_path, history in git_history.items():
        created_at = history[0]["author_date"] if history else None
        file_info = {
            "relative_path": rel_path,
            "type": "file",
            "created_at": created_at,
            "git_history": history,
        }
        lang = get_language_from_extension(rel_path)
        if lang:
            file_info["metadata"] = {"language": lang}
        files_data.append(file_info)

    directories_data = build_directories_list(repo_path, spec)

    output = {
        "project_tree": project_tree,
        "files": files_data,
        "directories": directories_data,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"JSON summary created: {output_file}")


# ------------------------------------------------------------
# CLI実行エントリポイント
# ------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate git history summary JSON using PyDriller."
    )
    parser.add_argument(
        "repo_path", help="Path to the root directory of the git project"
    )
    parser.add_argument(
        "--branch", default="main", help="Target branch name (default: main)"
    )
    parser.add_argument(
        "--output", default="git_summary.json", help="Output JSON file name"
    )

    args = parser.parse_args()
    generate_git_summary_json(args.repo_path, args.branch, args.output)
