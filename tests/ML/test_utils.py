import io
from pathlib import Path

import numpy as np
import pytest

from denoise_bot.ML_component import utils

try:
    import cupy as cp

    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

# Маркер для пропуска тестов, требующих CuPy
requires_cupy = pytest.mark.skipif(not CUPY_AVAILABLE, reason="CuPy не установлен")


# --- Фикстуры для тестов ---


@pytest.fixture
def assets_dir() -> Path:
    """Возвращает путь к директории с тестовыми данными."""
    return Path(__file__).parent.parent / "test_assets"


@pytest.fixture
def sample_image_path(assets_dir: Path) -> Path:
    """Путь к тестовому изображению."""
    # Используем любое из существующих, например, поврежденное
    path = assets_dir / "sample_damaged.png"
    # Убедимся, что файл существует, чтобы тест не падал с непонятной ошибкой
    assert path.is_file(), f"Тестовый файл не найден: {path}"
    return path


@pytest.fixture
def sample_numpy_array():
    """Возвращает простой NumPy массив для тестов."""
    return np.arange(9, dtype=np.float32).reshape(3, 3)


@pytest.fixture
def sample_cupy_array(sample_numpy_array):
    """Возвращает простой CuPy массив для тестов."""
    # Пропускаем создание фикстуры, если CuPy недоступен
    if not CUPY_AVAILABLE:
        pytest.skip("CuPy не установлен, пропускаем создание CuPy фикстуры")
    return cp.asarray(sample_numpy_array)


# --- Тесты для функций работы с бэкендом ---


@pytest.mark.parametrize(
    "use_gpu, cupy_available, expected_backend",
    [
        (True, True, "cupy"),
        (True, False, "numpy"),
        (False, True, "numpy"),
        (False, False, "numpy"),
    ],
)
def test_get_backend(use_gpu, cupy_available, expected_backend, monkeypatch):
    """
    Проверяет, что get_backend возвращает правильный модуль.

    Тест проверяет все комбинации флага use_gpu и доступности cupy.
    """
    # Мокируем константу CUPY_AVAILABLE внутри модуля utils
    monkeypatch.setattr(utils, "CUPY_AVAILABLE", cupy_available)
    # Мокируем cp, если он не доступен, чтобы избежать ошибок импорта
    if not cupy_available:
        monkeypatch.setattr(utils, "cp", None)

    backend = utils.get_backend(use_gpu=use_gpu)

    if expected_backend == "cupy":
        assert backend.__name__ == "cupy"
    else:
        assert backend.__name__ == "numpy"


def test_as_numpy(sample_numpy_array):
    """Проверяет конвертацию NumPy -> NumPy."""
    result = utils.as_numpy(sample_numpy_array)
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, sample_numpy_array)


@requires_cupy
def test_as_numpy_from_cupy(sample_cupy_array):
    """Проверяет конвертацию CuPy -> NumPy."""
    result = utils.as_numpy(sample_cupy_array)
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, sample_cupy_array.get())


def test_as_backend_array_to_numpy(sample_numpy_array):
    """Проверяет преобразование в массив NumPy бэкенда."""
    result = utils.as_backend_array(sample_numpy_array, np)
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, sample_numpy_array)


@requires_cupy
def test_as_backend_array_to_cupy(sample_numpy_array):
    """Проверяет преобразование в массив CuPy бэкенда."""
    result = utils.as_backend_array(sample_numpy_array, cp)
    assert isinstance(result, cp.ndarray)
    assert (result.get() == sample_numpy_array).all()


# --- Тесты для работы с изображениями ---


def test_load_image_from_real_path_normalized(sample_image_path: Path):
    """Проверяет загрузку реального изображения из файла и его нормализацию."""
    # Act
    image = utils.load_image(str(sample_image_path), normalize=True)

    # Assert
    assert isinstance(image, np.ndarray)
    assert image.ndim == 3  # Проверяем, что есть 3 измерения (H, W, C)
    assert image.shape[2] == 3  # Проверяем, что есть 3 цветовых канала
    assert image.dtype == np.float32
    assert 0.0 <= np.min(image) <= 1.0  # Значения должны быть в диапазоне [0, 1]
    assert 0.0 <= np.max(image) <= 1.0


def test_load_image_from_real_path_not_normalized(sample_image_path: Path):
    """Проверяет загрузку реального изображения из файла без нормализации."""
    # Act
    image = utils.load_image(str(sample_image_path), normalize=False)

    # Assert
    assert isinstance(image, np.ndarray)
    assert image.shape[2] == 3
    assert image.dtype == np.uint8
    assert 0 <= np.min(image) <= 255  # Значения должны быть в диапазоне [0, 255]
    assert 0 <= np.max(image) <= 255


def test_load_image_from_real_bytes(sample_image_path: Path):
    """Проверяет загрузку изображения из реального байтового потока."""
    # Arrange: Читаем реальный файл в байтовый поток
    with open(sample_image_path, "rb") as f:
        file_bytes_io = io.BytesIO(f.read())

    # Act
    image = utils.load_image(file_bytes_io, normalize=False)

    # Assert
    assert isinstance(image, np.ndarray)
    assert image.shape[2] == 3
    assert image.dtype == np.uint8


def test_load_image_raises_error_for_nonexistent_path():
    """Проверяет, что при несуществующем пути возбуждается FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        utils.load_image("this/path/does/not/exist.png")


def test_save_and_reload_image_cycle(tmp_path: Path):
    """Проверяет полный цикл: сохранение массива и его последующую загрузку."""
    # Arrange
    # Создаем случайный тестовый массив, представляющий изображение
    original_image_array = np.random.rand(50, 40, 3).astype(np.float32)
    save_path = tmp_path / "test_output.png"

    # Act
    # 1. Сохраняем массив как изображение
    utils.save_image(original_image_array, str(save_path))

    # 2. Загружаем только что сохраненное изображение
    reloaded_image_array = utils.load_image(str(save_path), normalize=True)

    # Assert
    # Проверяем, что файл действительно был создан
    assert save_path.is_file()

    # Проверяем, что размерности совпадают
    assert reloaded_image_array.shape == original_image_array.shape

    mean_absolute_error = np.mean(np.abs(original_image_array - reloaded_image_array))
    assert mean_absolute_error < 0.01, (
        f"Разница между сохраненным и загруженным изображением слишком велика: " f"{mean_absolute_error}"
    )


# --- Тесты для генерации маски ---


def test_generate_mask():
    """Проверяет генерацию маски с заданными параметрами."""
    shape = (100, 100)
    ratio = 0.7
    mask = utils.generate_mask(shape, ratio, seed=42)

    assert mask.shape == shape
    assert mask.dtype == bool
    # Проверяем, что доля известных пикселей примерно соответствует заданной
    assert np.isclose(mask.sum() / mask.size, ratio, atol=1e-3)


def test_generate_mask_invalid_ratio():
    """Проверяет, что функция возбуждает ошибку при неверном ratio."""
    with pytest.raises(ValueError):
        utils.generate_mask((10, 10), 1.5)
    with pytest.raises(ValueError):
        utils.generate_mask((10, 10), -0.1)
