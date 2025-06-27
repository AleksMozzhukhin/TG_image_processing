import os
from pathlib import Path
import shutil

# --- Конфигурация путей ---
ROOT_DIR = Path(__file__).parent
DOCS_DIR = ROOT_DIR / "docs"
SRC_DIR = ROOT_DIR / "src"
PKG_DIR = SRC_DIR / "denoise_bot"
ROUTERS_DIR = PKG_DIR / "routers"

# Пути и домен для локализации
DOMAIN = "translations"
POT_FILE = ROUTERS_DIR / f"{DOMAIN}.pot"
LOCALES_DIR = ROUTERS_DIR / "locales"

LANGUAGES = ["en_US"]


# --- ОСНОВНЫЕ ЗАДАЧИ СБОРКИ ---
def copy_dir(src, dst):
    """Вспомогательная функция-обертка для shutil.copytree, чтобы doit был доволен."""
    shutil.copytree(src, dst, dirs_exist_ok=True)
    return True

def task_cleanup():
    """Очистка всех артефактов сборки (папок build, dist, .egg-info и т.д.)."""
    def clean_func():
        patterns_to_remove = [
            "build", "dist",
            str(SRC_DIR / "*.egg-info"),
            str(PKG_DIR / "share")
        ]
        for pattern in patterns_to_remove:
            for path in ROOT_DIR.glob(pattern):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                    print(f"Removed directory: {path}")
                elif path.is_file():
                    path.unlink()
                    print(f"Removed file: {path}")

    return {
        "actions": [clean_func],
        "doc": "Очистить все артефакты сборки."
    }


def task_docs():
    """Сборка HTML-документации и копирование ее внутрь пакета."""
    build_dir = DOCS_DIR / "build" / "html"
    target_dir = PKG_DIR / "share" / "doc" / "html"

    return {
        "actions": [
            # 1. Собрать документацию (оставляем как есть)
            f"sphinx-build -b html {DOCS_DIR / 'source'} {build_dir}",

            # --- ИСПРАВЛЕННЫЙ ВЫЗОВ ---
            # Теперь мы вызываем нашу обертку `copy_dir`
            (copy_dir, [build_dir, target_dir]),
        ],
        "file_dep": list((DOCS_DIR / "source").glob("**/*.rst")) + [DOCS_DIR / "source" / "conf.py"],
        "targets": [target_dir / "index.html"],
        "clean": [f"rm -rf {DOCS_DIR / 'build'}", f"rm -rf {PKG_DIR / 'share'}"],
        "doc": "Собрать HTML-документацию и подготовить ее к упаковке.",
    }


def task_i18n_compile():
    """[i18n] Скомпилировать .po файлы в бинарные .mo файлы."""
    po_files = list(LOCALES_DIR.glob(f"**/{DOMAIN}.po"))
    return {
        "actions": [f"pybabel compile -D {DOMAIN} -d {LOCALES_DIR} -f"],
        "file_dep": po_files,
        "targets": [p.with_suffix(".mo") for p in po_files],
        "doc": "Скомпилировать переводы в .mo файлы."
    }


def task_build():
    """Собрать финальный wheel и sdist пакеты проекта."""
    return {
        "actions": ["python -m build"],
        # Эта задача зависит от готовности документации и локализации
        "task_dep": ["docs", "i18n_compile"],
        "doc": "Собрать wheel и sdist пакеты проекта.",
    }


def task_test():
    """Запуск тестов с помощью pytest."""
    return {
        "actions": ["pytest -v"],
        "verbosity": 2,
        "doc": "Запустить все тесты проекта.",
    }


# --- Настройка задач по умолчанию ---
DOIT_CONFIG = {
    'default_tasks': ['build'],
}