from pathlib import Path
from typing import List, Dict
import csv
import pathspec


def load_gitignore_specs(
    root_dir: Path, extra_gitignores: List[str]
) -> Dict[Path, pathspec.PathSpec]:
    """
    各 .gitignore / .git/info/exclude ごとに PathSpec を作成して返す。

    挙動:
    - ルート直下の .gitignore は root_dir に適用される
    - extra_gitignores に指定した .gitignore はその親ディレクトリ配下に適用される
    - .git/info/exclude が存在すれば、必ず root_dir 全体に適用される（extra_gitignores に未指定でも読み込む）
    """
    # まず生の行を集める（ディレクトリ -> List[str]）
    raw_patterns: Dict[Path, List[str]] = {}

    # ルート直下の .gitignore
    main_gitignore = root_dir / ".gitignore"
    if main_gitignore.exists():
        lines = main_gitignore.read_text(encoding="utf-8").splitlines()
        raw_patterns.setdefault(root_dir, []).extend(lines)

    # 追加指定の .gitignore（相対パスで渡される想定）
    for rel_path in extra_gitignores:
        gitignore_path = root_dir / rel_path
        if not gitignore_path.exists():
            continue
        base_dir = gitignore_path.parent
        lines = gitignore_path.read_text(encoding="utf-8").splitlines()
        raw_patterns.setdefault(base_dir, []).extend(lines)

    # 常に .git/info/exclude を読み込む（存在すれば root 全体に適用）
    git_exclude = root_dir / ".git" / "info" / "exclude"
    if git_exclude.exists():
        lines = git_exclude.read_text(encoding="utf-8").splitlines()
        raw_patterns.setdefault(root_dir, []).extend(lines)

    # 最後に PathSpec を作成して返す
    specs: Dict[Path, pathspec.PathSpec] = {}
    for base_dir, patterns in raw_patterns.items():
        # pathspec は空行やコメント行も無視するのでそのまま渡して良い
        specs[base_dir] = pathspec.PathSpec.from_lines("gitwildmatch", patterns)

    return specs


def is_ignored(
    path: Path, root_dir: Path, specs: Dict[Path, pathspec.PathSpec]
) -> bool:
    """
    path がいずれかの .gitignore ルールで無視されるかどうかを判定
    """
    for base_dir, spec in specs.items():
        # .gitignore が適用される範囲内であれば評価
        if base_dir in path.parents or path == base_dir:
            rel_from_base = path.relative_to(base_dir).as_posix()
            if spec.match_file(rel_from_base):
                return True
    return False


def get_all_project_files(root_dir: Path, extra_gitignores: List[str]) -> List[Path]:
    """
    .git 配下と .gitignore による除外を反映した全ファイル一覧を取得
    """
    specs = load_gitignore_specs(root_dir, extra_gitignores)
    result: List[Path] = []

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue

        # .git配下は除外
        if any(part == ".git" for part in path.relative_to(root_dir).parts):
            continue

        if is_ignored(path, root_dir, specs):
            continue

        result.append(path)

    return result


def export_to_csv(files: List[Path], root_dir: Path, output_csv: Path) -> None:
    """
    取得したファイル一覧のプロジェクトルートからの相対パスを Windows パス区切りで CSV 出力する
    """
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["relative_path"])
        for path in files:
            rel_path = path.relative_to(root_dir).as_posix().replace("/", "\\")
            writer.writerow([rel_path])


def main() -> None:
    # ======== 設定 ========

    # プロジェクトルート
    project_root = Path(r"C:\Users\hir-matsuoka\dev\honda\honda\mold-hinjyuku-software")

    # 相対パス指定の追加 .gitignore
    extra_gitignores = ["prisma/.gitignore", "dist/.gitignore", ".git/info/exclude"]
    # 出力パス
    output_csv = Path("output") / "file_list.csv"

    # =====================

    files = get_all_project_files(project_root, extra_gitignores)
    export_to_csv(files, project_root, output_csv)
    print(f"{len(files)} files exported to {output_csv}")


if __name__ == "__main__":
    main()
