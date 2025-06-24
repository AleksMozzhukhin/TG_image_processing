import matplotlib.pyplot as plt
import numpy as np


def show_image(image: np.ndarray, title: str = "", grid: bool = False, axis: bool = False):
    """
    Отображает одно изображение с заданными параметрами.

    Args:
        image (np.ndarray): Массив изображения.
        title (str): Заголовок для изображения.
        grid (bool): Показывать ли сетку.
        axis (bool): Показывать ли оси координат.
    """
    # np.clip гарантирует, что значения пикселей будут в валидном диапазоне [0, 1]
    # для корректного отображения, особенно после численных операций.
    plt.imshow(np.clip(image, 0, 1))
    plt.title(title)
    plt.grid(grid)
    plt.axis(axis)


def show_results(original: np.ndarray, damaged: np.ndarray, recovered: np.ndarray):
    """
    Отображает оригинальное, поврежденное и восстановленное изображения в один ряд для сравнения.

    Args:
        original (np.ndarray): Оригинальное изображение.
        damaged (np.ndarray): Изображение с зануленными пикселями.
        recovered (np.ndarray): Изображение после восстановления.
    """
    plt.figure(figsize=(18, 6))

    plt.subplot(1, 3, 1)
    show_image(original, "Оригинальное изображение")

    plt.subplot(1, 3, 2)
    show_image(damaged, "Поврежденное изображение")

    plt.subplot(1, 3, 3)
    show_image(recovered, "Восстановленное изображение")

    plt.suptitle("Результат восстановления изображения методом ADMM", fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Корректируем расположение, чтобы заголовок не накладывался
    plt.show()