import os
import json
from datetime import datetime
from pydriller import Repository

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


def build_project_structure(root_path, current_path="."):
    """プロジェクトツリー構造を再帰的に構築"""
    abs_path = os.path.join(root_path, current_path)
    items = []
    for entry in sorted(os.listdir(abs_path)):
        full_path = os.path.join(abs_path, entry)
        rel_path = os.path.relpath(full_path, root_path)
        if os.path.isdir(full_path):
            children = build_project_structure(root_path, rel_path)
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


def build_directories_list(root_path):
    """ディレクトリ一覧を構築"""
    directories = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        rel_path = os.path.relpath(dirpath, root_path)
        if rel_path == ".":
            rel_path = ""
        children = [os.path.join(rel_path, d) + "/" for d in dirnames] + [
            os.path.join(rel_path, f) for f in filenames
        ]
        directories.append(
            {
                "relative_path": rel_path + "/" if rel_path else "./",
                "children": children,
            }
        )
    return directories


def extract_git_history(repo_path, branch):
    """PyDrillerで全ファイルの変更履歴を収集"""
    file_histories = {}

    for commit in Repository(
        path_to_repo=repo_path, only_in_branch=branch
    ).traverse_commits():
        for mod in commit.modified_files:
            if not mod.new_path:
                continue  # 削除済みなど
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


def generate_git_summary_json(repo_path, branch, output_file="git_summary.json"):
    repo_path = os.path.abspath(repo_path)
    root_name = os.path.basename(repo_path)
    print(f"Analyzing repository: {root_name} (branch: {branch})")

    project_tree = {
        "root": {
            "name": root_name,
            "root_path": ".",
            "structure": build_project_structure(repo_path),
        }
    }

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

    directories_data = build_directories_list(repo_path)

    output = {
        "project_tree": project_tree,
        "files": files_data,
        "directories": directories_data,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"JSON summary created: {output_file}")


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
