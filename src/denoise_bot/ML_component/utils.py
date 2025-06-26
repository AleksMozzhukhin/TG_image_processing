import os
from typing import Union, Tuple, IO, NewType
import cv2
import numpy as np
import types

try:
    import cupy as cp
    CUPY_AVAILABLE = True

    #: Псевдоним для массивов, которые могут быть на CPU (NumPy) или GPU (CuPy).
    ArrayLike = NewType('ArrayLike', Union[np.ndarray, cp.ndarray])

    #: Псевдоним для вычислительного бэкенда (модуль :py:mod:`numpy` или :py:mod:`cupy`).
    BackendModule = NewType('BackendModule', types.ModuleType)

except ImportError:
    cupy = None
    CUPY_AVAILABLE = False

    # --- То же самое для случая без CuPy ---
    ArrayLike = NewType('ArrayLike', np.ndarray)
    BackendModule = NewType('BackendModule', types.ModuleType)


def get_backend(use_gpu: bool = True) -> 'BackendModule':
    """
    Возвращает вычислительный бэкенд (NumPy или CuPy) в зависимости от доступности GPU и выбора пользователя.

    Args:
        use_gpu (bool): Флаг, указывающий, нужно ли пытаться использовать GPU.

    Returns:
        BackendModule: Модуль numpy или cupy, который будет использоваться для вычислений.
    """
    if use_gpu and CUPY_AVAILABLE:
        print("GPU (CuPy) доступен и выбран в качестве бэкенда.")
        return cp
    else:
        if use_gpu and not CUPY_AVAILABLE:
            print("Предупреждение: Запрошен GPU, но CuPy не найден. Используется CPU (NumPy).")
        print("CPU (NumPy) выбран в качестве бэкенда.")
        return np


def _ensure_numpy(array: 'ArrayLike') -> np.ndarray:
    """
    Вспомогательная функция, которая гарантирует, что массив находится на CPU (является NumPy массивом).
    Если на вход подан CuPy массив, он будет скопирован на CPU.

    Args:
        array (ArrayLike): Входной массив, который может быть numpy.ndarray или cupy.ndarray.

    Returns:
        np.ndarray: Массив в формате NumPy.
    """
    if CUPY_AVAILABLE and isinstance(array, cp.ndarray):
        return cp.asnumpy(array)
    return np.asarray(array)


def as_numpy(array: 'ArrayLike') -> np.ndarray:
    """
    Универсальная функция для преобразования CuPy/NumPy массива в NumPy массив (на CPU).

    Args:
        array (ArrayLike): Входной массив, который может быть numpy.ndarray или cupy.ndarray.

    Returns:
        np.ndarray: Массив в формате NumPy.
    """
    if CUPY_AVAILABLE and isinstance(array, cp.ndarray):
        return cp.asnumpy(array)
    return np.asarray(array)


def as_backend_array(array: 'ArrayLike', backend: 'BackendModule') -> 'ArrayLike':
    """
    Универсальная функция для преобразования массива в массив нужного бэкенда.

    Args:
        array (ArrayLike): Входной массив.
        backend (BackendModule): Целевой бэкенд (модуль numpy или cupy).

    Returns:
        ArrayLike: Массив, находящийся на целевом устройстве (CPU или GPU).
    """
    if backend is cp and CUPY_AVAILABLE:
        return cp.asarray(array)
    # Если целевой бэкенд - numpy, или если cupy не доступен, конвертируем в numpy
    return np.asarray(array)


def load_image(source: Union[str, IO[bytes]], normalize: bool = True) -> np.ndarray:
    """
    Загружает изображение из файла или байтового потока.

    Args:
        source (Union[str, IO[bytes]]): Путь к файлу (str) или байтовый поток (например, io.BytesIO).
        normalize (bool): Если True, нормализует значения пикселей в диапазон [0, 1].

    Returns:
        np.ndarray: Загруженное изображение в виде NumPy массива (на CPU).

    Raises:
        ValueError: Если не удалось декодировать изображение из предоставленного источника.
    """
    if isinstance(source, str):
        image = cv2.imread(source)
        if image is None:
            raise FileNotFoundError(f"Не удалось загрузить изображение по пути: {source}")
    else:
        # Если это байтовый поток, читаем его в NumPy массив
        file_bytes = np.frombuffer(source.read(), np.uint8)
        # Декодируем массив байтов в изображение
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Не удалось декодировать изображение из байтового потока.")

        # Конвертируем BGR в RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    if normalize:
        return image_rgb.astype(np.float32) / 255.0

    return image_rgb


def generate_mask(shape: Tuple[int, int],
                  known_pixel_ratio: float,
                  seed: int = 42
                  ) -> np.ndarray:
    """
    Генерирует бинарную NumPy маску, где True означает известный пиксель.

    Args:
        shape (Tuple[int, int]): Форма матрицы/изображения (высота, ширина).
        known_pixel_ratio (float): Доля известных пикселей (от 0 до 1).
        seed (int): Зерно для генератора случайных чисел для воспроизводимости.

    Returns:
        np.ndarray: Булева NumPy маска той же формы, что и `shape`.

    Raises:
        ValueError: Если known_pixel_ratio находится вне диапазона [0, 1].
    """
    if not (0 <= known_pixel_ratio <= 1):
        raise ValueError("known_pixel_ratio должен быть в диапазоне [0, 1]")

    np.random.seed(seed)
    total_pixels = np.prod(shape)
    known_pixels_count = int(total_pixels * known_pixel_ratio)

    # Создаем одномерный массив, заполняем его нужным количеством True,
    # перемешиваем и возвращаем в исходную форму.
    flat_mask = np.full(total_pixels, False, dtype=bool)
    flat_mask[:known_pixels_count] = True
    np.random.shuffle(flat_mask)

    return flat_mask.reshape(shape)


def save_image(image_array: 'ArrayLike', path: str):
    """
    Сохраняет изображение из NumPy или CuPy массива в файл.

    Args:
        image_array (ArrayLike): Массив изображения для сохранения.
        path (str): Путь для сохранения файла.
    """
    # Гарантируем, что массив находится на CPU для работы с OpenCV
    image_np = as_numpy(image_array)

    # Отсекаем значения и денормализуем до 8-битного формата
    image_to_save = (np.clip(image_np, 0, 1) * 255).astype(np.uint8)

    # Конвертируем из RGB (стандарт для обработки) в BGR (стандарт для OpenCV)
    image_bgr = cv2.cvtColor(image_to_save, cv2.COLOR_RGB2BGR)

    # Создаем директорию, если она не существует
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    cv2.imwrite(path, image_bgr)
    print(f"Изображение сохранено в: {path}")
