import os
from pathlib import Path

# --- Конфигурация путей ---
ROOT_DIR = Path(__file__).parent
DOCS_DIR = ROOT_DIR / "docs"
SRC_DIR = ROOT_DIR / "src"
ROUTERS_DIR = SRC_DIR / "denoise_bot" / "routers"

# Пути и домен для локализации
DOMAIN = "translations"
POT_FILE = ROUTERS_DIR / f"{DOMAIN}.pot"
LOCALES_DIR = ROUTERS_DIR / "locales"

LANGUAGES = ["en_US"]


# --- Задачи ---

def task_docs():
    """Сборка HTML-документации с помощью Sphinx."""
    source_files = list(SRC_DIR.glob("**/*.py"))
    doc_files = list((DOCS_DIR / "source").glob("**/*.rst"))

    return {
        "actions": [
            f"sphinx-build -M clean {DOCS_DIR / 'source'} {DOCS_DIR / 'build'}",
            f"sphinx-build -b html {DOCS_DIR / 'source'} {DOCS_DIR / 'build/html'}"
        ],
        "file_dep": source_files + doc_files + [DOCS_DIR / "source" / "conf.py"],
        "targets": [DOCS_DIR / "build" / "html" / "index.html"],
        "clean": [f"rm -rf {DOCS_DIR / 'build'}"],
        "doc": "Собрать HTML документацию проекта.",
    }


def task_test():
    """Запуск тестов с помощью pytest."""
    return {
        "actions": ["pytest"],
        "verbosity": 2,
        "doc": "Запустить все тесты проекта.",
    }


# --- Задачи для локализации ---

def task_i18n_extract():
    """[i18n] 1. Извлечь переводимые строки из кода в .pot шаблон."""
    source_files = list(SRC_DIR.glob("**/*.py"))

    babel_cfg_content = """
[python: **.py]
[extractors]
python = babel.messages.extract:extract_python
    """

    return {
        "actions": [
            # Создаем babel.cfg, если его нет
            (create_babel_cfg, [babel_cfg_content]),
            # Указываем использовать этот конфиг
            f"pybabel extract -F babel.cfg . -o {POT_FILE}"
        ],
        "file_dep": source_files,
        "targets": [POT_FILE],
        "doc": "Создать/обновить .pot шаблон переводов.",
        "clean": [f"rm -f {ROOT_DIR / 'babel.cfg'}"]  # Очистка конфига
    }


def create_babel_cfg(content, path="babel.cfg"):
    """Вспомогательная функция для создания babel.cfg"""
    p = Path(path)
    if not p.exists():
        p.write_text(content)


def task_i18n_init():
    """[i18n] 2. Инициализировать каталоги для НОВЫХ языков (запускать вручную)."""
    for lang in LANGUAGES:
        po_file = LOCALES_DIR / lang / "LC_MESSAGES" / f"{DOMAIN}.po"
        # Создаем задачу, только если .po файл еще не существует
        if not po_file.exists():
            yield {
                "name": lang,
                "actions": [
                    f"pybabel init -l {lang} -D {DOMAIN} -i {POT_FILE} -d {LOCALES_DIR}"
                ],
                "file_dep": [POT_FILE],
                "targets": [po_file],
                "doc": f"Инициализировать каталог для языка: {lang}",
            }


def task_i18n_update():
    """[i18n] 3. Обновить существующие .po файлы из .pot шаблона."""
    lang_dirs = [d for d in LOCALES_DIR.iterdir() if d.is_dir() and d.name in LANGUAGES]
    po_files = [LOCALES_DIR / lang.name / "LC_MESSAGES" / f"{DOMAIN}.po" for lang in lang_dirs]

    return {
        "task_dep": ["i18n_extract"],
        "actions": [
            f"pybabel update -D {DOMAIN} -i {POT_FILE} -d {LOCALES_DIR}"
        ],
        "file_dep": [POT_FILE],
    }


def task_i18n_compile():
    """[i18n] 4. Скомпилировать .po файлы в бинарные .mo файлы."""
    po_files = list(LOCALES_DIR.glob(f"**/{DOMAIN}.po"))

    return {
        "task_dep": ["i18n_update"],
        "actions": [
            f"pybabel compile -D {DOMAIN} -d {LOCALES_DIR}"
        ],
        "file_dep": po_files,
        "targets": [p.with_suffix(".mo") for p in po_files],
    }


def task_i18n():
    """[i18n] Полный цикл: извлечь, обновить и скомпилировать переводы."""
    return {
        "actions": None,
        "task_dep": ["i18n_compile"],
    }


# --- Настройка задач по умолчанию ---
DOIT_CONFIG = {
    'default_tasks': ['docs'],
}
