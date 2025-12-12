import os
import ast
from pathlib import Path


# Базовый список мусорных директорий
IGNORE_DIRS = {
    "__pycache__",
    "node_modules",
    ".git",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    ".tox",
    ".eggs",
    ".svn",
    ".hg",
    ".next",
    ".turbo",
    ".cache",
    ".parcel-cache",
    ".pnpm-store",
}

# Можно добавить свои через переменную окружения: TREE_IGNORE="foo,bar"
USER_IGNORE = {x.strip() for x in os.getenv("TREE_IGNORE", "").split(",") if x.strip()}
IGNORE_DIRS |= USER_IGNORE


def parse_python_file(file_path: Path):
    """Возвращает список классов и функций из Python-файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except Exception as e:
        return [f"[parse error: {e}]"]

    result = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            result.append(f"class {node.name}")
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    result.append(f"  def {item.name}()")
        elif isinstance(node, ast.FunctionDef):
            result.append(f"def {node.name}()")
    return result


def _should_skip(entry: Path) -> bool:
    # Не лезем в симлинки (чтобы не зациклиться)
    try:
        if entry.is_symlink():
            return True
    except OSError:
        return True
    # Режем мусорные директории
    return entry.is_dir() and entry.name in IGNORE_DIRS


def print_tree(root: Path, prefix: str = ""):
    """Рекурсивно печатает дерево с методами и классами Python."""
    # Фильтруем мусор и сортируем: сначала папки, потом файлы
    items = [p for p in root.iterdir() if not _should_skip(p)]
    items.sort(key=lambda p: (p.is_file(), p.name.lower()))

    for i, item in enumerate(items):
        connector = "└── " if i == len(items) - 1 else "├── "
        print(prefix + connector + item.name)

        branch_prefix = prefix + ("    " if i == len(items) - 1 else "│   ")

        if item.is_dir():
            print_tree(item, branch_prefix)
        elif item.suffix == ".py":
            methods = parse_python_file(item)
            for m in methods:
                print(branch_prefix + "   " + m)


if __name__ == "__main__":
    root_dir = Path(__file__).parents[1]
    print_tree(root_dir)
