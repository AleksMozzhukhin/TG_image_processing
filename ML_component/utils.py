# utils.py
import numpy as np
import cv2


def load_image(path: str, normalize: bool = True) -> np.ndarray:
    """
    Загружает изображение из файла, конвертирует в RGB и опционально нормализует.

    Args:
        path (str): Путь к изображению.
        normalize (bool): Если True, нормализует значения пикселей в диапазон [0, 1].

    Returns:
        np.ndarray: Загруженное изображение в виде NumPy массива.

    Raises:
        FileNotFoundError: Если изображение по указанному пути не найдено.
    """
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Не удалось загрузить изображение по пути: {path}")

    # OpenCV загружает изображения в формате BGR, конвертируем в RGB для
    # корректного отображения в matplotlib и стандартной обработки.
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    if normalize:
        return image_rgb / 255.0

    return image_rgb


def generate_mask(shape: tuple, known_pixel_ratio: float, seed: int = 42) -> np.ndarray:
    """
    Генерирует бинарную маску, где True означает известный пиксель.

    Args:
        shape (tuple): Форма матрицы/изображения (высота, ширина).
        known_pixel_ratio (float): Доля известных пикселей (от 0 до 1).
        seed (int): Зерно для генератора случайных чисел для воспроизводимости.

    Returns:
        np.ndarray: Булева маска той же формы, что и `shape`.

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
    flat_mask = np.full(total_pixels, False)
    flat_mask[:known_pixels_count] = True
    np.random.shuffle(flat_mask)

    return flat_mask.reshape(shape)