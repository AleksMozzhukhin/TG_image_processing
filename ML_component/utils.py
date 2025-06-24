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