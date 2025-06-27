from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from denoise_bot.ML_component import main_model, utils


# --- Фикстуры для путей к тестовым данным ---


@pytest.fixture
def assets_dir() -> Path:
    """Возвращает путь к директории с тестовыми данными."""
    return Path(__file__).parent.parent / "test_assets"


@pytest.fixture
def damaged_image_path(assets_dir: Path) -> Path:
    """Путь к тестовому поврежденному изображению."""
    path = assets_dir / "sample_damaged.png"
    assert path.is_file(), f"Тестовый файл не найден: {path}"
    return path


@pytest.fixture
def original_image_path(assets_dir: Path) -> Path:
    """Путь к тестовому оригинальному изображению."""
    path = assets_dir / "sample_original.png"
    assert path.is_file(), f"Тестовый файл не найден: {path}"
    return path


# --- Тесты для create_mask_from_damaged ---


def test_create_mask_from_damaged_on_real_image(damaged_image_path: Path):
    """Проверяет создание маски на реальном изображении из файла."""
    # Arrange
    # Загружаем реальное изображение, как это происходит в пайплайне
    damaged_image_np = utils.load_image(str(damaged_image_path), normalize=True)

    # Act
    mask = main_model.create_mask_from_damaged(damaged_image_np, threshold=10)

    # Assert
    assert mask.dtype == bool

    # Проверяем, что черные пиксели (поврежденные) отмечены как False в маске,
    # а не-черные - как True.
    # Суммируем по каналам, чтобы получить серое изображение
    gray_image = (damaged_image_np * 255).sum(axis=2)
    expected_mask = gray_image > 10.0

    np.testing.assert_array_equal(mask, expected_mask)


# --- Интеграционные тесты для run_inpainting_pipeline ---

PIPELINE_PATCHES = [
    patch("denoise_bot.ML_component.utils.save_image"),
    patch("denoise_bot.ML_component.visualize.save_convergence_plot"),
    patch("denoise_bot.ML_component.visualize.save_results_comparison"),
    patch("denoise_bot.ML_component.admm_core.MC_ADMM"),
]


def apply_pipeline_patches(func):
    """Декоратор для применения группы патчей к тестовой функции."""
    for p in reversed(PIPELINE_PATCHES):
        func = p(func)
    return func


@apply_pipeline_patches
def test_run_inpainting_pipeline_success_flow(
        mock_mc_admm,
        mock_save_comparison,
        mock_save_convergence,
        mock_save_image,
        damaged_image_path: Path,
        original_image_path: Path,
        tmp_path: Path,
):
    """
    Проверяет полный успешный сценарий работы пайплайна.

    Тест использует реальные файлы, но мокирует тяжелые
    вычислительные и I/O операции.
    """
    # --- Arrange ---
    output_dir = str(tmp_path)

    # Загружаем реальное изображение, чтобы знать его размер
    h, w, _ = utils.load_image(str(damaged_image_path)).shape

    # Настраиваем мок для MC_ADMM, чтобы он возвращал результат правильного размера
    fake_recovered_channel = np.random.rand(h, w)
    fake_history = [10, 5, 2]
    mock_mc_admm.return_value = (fake_recovered_channel, fake_history)

    # --- Act ---
    result_image = main_model.run_inpainting_pipeline(
        damaged_image_source=str(damaged_image_path),
        original_image_source=str(original_image_path),
        output_dir=output_dir,
        max_iters=5,
        use_gpu=False,
    )

    # --- Assert ---
    # 1. Проверяем, что результат не None и имеет правильную форму
    assert result_image is not None
    assert result_image.shape == (h, w, 3)

    # 2. Проверяем вызовы ключевых функций
    # ADMM должен быть вызван 3 раза (для каждого RGB канала)
    assert mock_mc_admm.call_count == 3

    # Проверяем, что в ADMM переданы данные правильной формы
    first_call_args = mock_mc_admm.call_args_list[0].kwargs
    assert "Y" in first_call_args
    assert "mask" in first_call_args
    assert first_call_args["Y"].shape == (h, w)
    assert first_call_args["mask"].shape == (h, w)

    # 3. Проверяем, что функции сохранения/визуализации были вызваны
    mock_save_image.assert_called_once()
    mock_save_convergence.assert_called_once()
    mock_save_comparison.assert_called_once()


@patch("denoise_bot.ML_component.utils.load_image", side_effect=FileNotFoundError("Test error"))
def test_run_inpainting_pipeline_handles_file_not_found(mock_load_image, tmp_path: Path):
    """
    Проверяет, что пайплайн корректно обрабатывает FileNotFoundError.

    Если файл не найден, функция должна вернуть None и не падать.
    """
    # Act
    result = main_model.run_inpainting_pipeline(damaged_image_source="nonexistent.png", output_dir=str(tmp_path))

    # Assert
    assert result is None
    mock_load_image.assert_called_once_with("nonexistent.png")


@patch("denoise_bot.ML_component.admm_core.MC_ADMM", side_effect=Exception("ADMM Critical Error"))
@patch("denoise_bot.ML_component.utils.load_image")
def test_run_inpainting_pipeline_handles_admm_exception(
        mock_load_image, mock_mc_admm, damaged_image_path: Path, tmp_path: Path
):
    """
    Проверяет, что пайплайн корректно обрабатывает непредвиденную ошибку.

    Ошибка имитируется внутри алгоритма ADMM, и пайплайн должен
    безопасно завершиться, вернув None.
    """
    # --- Arrange ---
    img_bgr = cv2.imread(str(damaged_image_path))
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    real_damaged_image = img_rgb.astype(np.float32) / 255.0

    # Настраиваем мок load_image, чтобы он возвращал наш подготовленный массив.
    mock_load_image.return_value = real_damaged_image

    # --- Act ---
    result = main_model.run_inpainting_pipeline(
        damaged_image_source=str(damaged_image_path), output_dir=str(tmp_path), use_gpu=False
    )

    # --- Assert ---
    assert result is None
    mock_load_image.assert_called_once_with(str(damaged_image_path))
    mock_mc_admm.assert_called_once()
