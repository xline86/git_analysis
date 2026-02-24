import os
import json
from datetime import timezone, timedelta, datetime
from pathlib import Path
from typing import Any
from pydriller import Repository
from pathspec import PathSpec
from pydriller.domain.commit import ModificationType


# ------------------------------------------------------------
# 定数定義
# ------------------------------------------------------------

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

# JST タイムゾーン
JST = timezone(timedelta(hours=9))


# ------------------------------------------------------------
# 言語判定
# ------------------------------------------------------------
def get_language_from_extension(filename: str) -> str | None:
    return LANGUAGE_MAP.get(Path(filename).suffix, None)


# ------------------------------------------------------------
# .gitignore 読み込み＆判定
# ------------------------------------------------------------
def load_gitignore(root_path: Path) -> PathSpec | None:
    """
    ルートディレクトリ直下の .gitignore を読み込み、PathSpec を返す。
    """
    gitignore_path = root_path / ".gitignore"
    if not gitignore_path.exists():
        return None
    with gitignore_path.open("r", encoding="utf-8") as f:
        spec = PathSpec.from_lines("gitwildmatch", f)
    return spec


def is_ignored(path: Path, spec: PathSpec | None, root_path: Path) -> bool:
    """
    .gitignore のルールに一致するか判定。
    常に .git ディレクトリは除外する。
    """
    if ".git" in path.relative_to(root_path).parts:
        return True

    if spec is None:
        return False

    rel_path = path.relative_to(root_path).as_posix()
    return spec.match_file(rel_path)


# ------------------------------------------------------------
# プロジェクト構造の探索
# ------------------------------------------------------------
def build_project_structure(
    root_path: Path, current_path: Path = Path("."), spec: PathSpec | None = None
) -> list[dict[str, Any]]:
    """
    プロジェクトのツリー構造を再帰的に構築。
    .gitignore で無視されているものはスキップ。
    """
    abs_path = root_path / current_path
    items: list[dict[str, Any]] = []

    for entry in sorted(abs_path.iterdir()):
        if is_ignored(entry, spec, root_path):
            continue

        rel_path = entry.relative_to(root_path)
        if entry.is_dir():
            children = build_project_structure(root_path, rel_path, spec)
            items.append(
                {
                    "type": "directory",
                    "name": entry.name,
                    "path": rel_path.as_posix(),
                    "children": children,
                }
            )
        else:
            items.append(
                {
                    "type": "file",
                    "name": entry.name,
                    "path": rel_path.as_posix(),
                }
            )

    return items


def build_directories_list(
    root_path: Path, spec: PathSpec | None = None
) -> list[dict[str, Any]]:
    directories: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirpath = Path(dirpath)
        if is_ignored(dirpath, spec, root_path):
            continue

        rel_path = dirpath.relative_to(root_path)
        rel_str = "" if rel_path.as_posix() == "." else rel_path.as_posix()

        children: list[str] = []
        for d in dirnames:
            full_d = dirpath / d
            if not is_ignored(full_d, spec, root_path):
                children.append(f"{(Path(rel_str) / d).as_posix()}/")

        for f in filenames:
            full_f = dirpath / f
            if not is_ignored(full_f, spec, root_path):
                children.append((Path(rel_str) / f).as_posix())

        directories.append(
            {
                "relative_path": f"{rel_str}/" if rel_str else "./",
                "children": children,
            }
        )
    return directories


# ------------------------------------------------------------
# Git 履歴の収集 (PyDriller)
# ------------------------------------------------------------
def extract_git_history(
    repo_path: Path,
    branch: str,
    start_date_jst: datetime | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    PyDrillerを使って、指定ブランチ全体の変更履歴をファイル単位で収集。
    """

    # 日付をUTCに変換
    from_date_utc = None
    if start_date_jst is not None:
        from_date_utc = start_date_jst.astimezone(timezone.utc)

    file_histories: dict[str, list[dict[str, Any]]] = {}

    for commit in Repository(
        path_to_repo=repo_path.as_posix(),
        only_in_branch=branch,
        since=from_date_utc,  # JST→UTCに変換して渡す
    ).traverse_commits():
        for mod in getattr(
            commit, "modified_files", getattr(commit, "modifications", [])
        ):
            # ファイルパス情報
            old_path = mod.old_path
            new_path = mod.new_path

            # 変更タイプ判定
            change_type = mod.change_type
            file_created = change_type == ModificationType.ADD
            file_deleted = change_type == ModificationType.DELETE
            file_rename = change_type == ModificationType.RENAME

            # 解析対象パス（削除されたファイルの場合は old_path を採用）
            rel_path = new_path or old_path
            if not rel_path:
                continue

            entry = {
                "commit_hash": commit.hash[:14],
                "commit_message": commit.msg.strip(),
                "author_date": commit.author_date.astimezone(JST).isoformat(),
                "commit_date": commit.committer_date.astimezone(JST).isoformat(),
                "change_type": change_type.name,
                "file_created": file_created,
                "file_deleted": file_deleted,
                "file_rename": file_rename,
                "old_file_name": old_path,
                "new_file_name": new_path,
            }
            file_histories.setdefault(rel_path, []).append(entry)

    # コミット時刻でソート（古い順）
    for rel_path in file_histories:
        file_histories[rel_path].sort(key=lambda x: x["author_date"])

    return file_histories


# ------------------------------------------------------------
# JSON生成メイン関数
# ------------------------------------------------------------
def generate_git_summary_json(
    repo_path: Path,
    branch: str,
    output_file: Path = Path("git_summary.json"),
    since: datetime | None = None,
) -> None:
    repo_path = repo_path.resolve()
    root_name = repo_path.name

    print(f"Analyzing repository: {root_name} (branch: {branch})")

    # .gitignoreの読み込み
    spec = load_gitignore(repo_path)
    if spec:
        print(f"Loaded .gitignore from {repo_path}")
    else:
        print("No .gitignore found — analyzing all files.")

    # プロジェクトディレクトリの構造情報
    project_tree = {
        "root": {
            "name": root_name,
            "root_path": ".",
            "structure": build_project_structure(repo_path, Path("."), spec),
        }
    }

    # Git履歴収集
    git_history = extract_git_history(repo_path, branch, since)

    files_data: list[dict[str, Any]] = []
    for rel_path, history in git_history.items():
        created_at = history[0]["author_date"] if history else None
        file_info: dict[str, Any] = {
            "relative_path": rel_path,
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

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print(f"JSON summary created: {output_file}")


# ------------------------------------------------------------
# 実行
# ------------------------------------------------------------
if __name__ == "__main__":
    repo_path = Path(
        r"C:\Users\hir-matsuoka\dev\honda\honda\mold-hinjyuku-software"
    )  # プロジェクトのルートディレクトリ
    branch = "master"  # 解析対象のgitブランチ名
    output = Path(r"output\project_history.json")  # 出力ファイル(json)
    since = None  # datetime(2026, 1, 1, 0, 0, tzinfo=JST) # <= ほんとは指定した日時以降のコミットをさらいたかったけどなんかできなかった

    generate_git_summary_json(repo_path, branch,  output,since)
