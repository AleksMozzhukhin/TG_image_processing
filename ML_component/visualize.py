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


def plot_convergence(norm_histories: list, titles: list, colors: list):
    """
    Строит графики сходимости ядерной нормы для каждого канала в логарифмическом масштабе.

    Args:
        norm_histories (list): Список списков, где каждый внутренний список - история ядерной нормы для одного канала.
        titles (list): Список заголовков для каждого графика (например, имена каналов).
        colors (list): Список цветов для каждого графика.
    """
    if not (len(norm_histories) == len(titles) == len(colors)):
        raise ValueError("Длины списков должны совпадать")

    num_plots = len(norm_histories)
    plt.figure(figsize=(5 * num_plots, 5))

    for i, history in enumerate(norm_histories):
        plt.subplot(1, num_plots, i + 1)
        plt.plot(history, color=colors[i], linewidth=2)
        plt.title(f"Сходимость ({titles[i]})")
        plt.xlabel("Итерация")
        plt.ylabel("Ядерная норма")
        plt.yscale("log")  # Логарифмическая шкала для лучшей наглядности на начальных этапах
        plt.grid(True, which="both", linestyle='--', linewidth=0.5)

    plt.suptitle("Сходимость алгоритма по каналам", fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()