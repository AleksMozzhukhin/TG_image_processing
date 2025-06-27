import os
from typing import List

import matplotlib.pyplot as plt
import numpy as np

from .utils import ArrayLike, _ensure_numpy

try:
    import cupy as cp

except ImportError:
    cp = None


def show_image(ax: plt.Axes, image: "ArrayLike", title: str = "", grid: bool = False):
    """
    Отображение заданной картинки.

    Отображает одно изображение на предоставленной оси matplotlib.Axes.
    Автоматически конвертирует CuPy массив в NumPy, если необходимо.

    Args:
        ax (plt.Axes): Ось Matplotlib, на которой будет отрисовано изображение.
        image (ArrayLike): Массив изображения (numpy или cupy).
        title (str): Заголовок для изображения.
        grid (bool): Показывать ли сетку.
    """
    image_np = _ensure_numpy(image)
    # Отсекаем значения для корректного отображения
    ax.imshow(np.clip(image_np, 0, 1))
    ax.set_title(title)
    ax.grid(grid)
    ax.axis("off")


def save_results_comparison(
    original: "ArrayLike",
    damaged: "ArrayLike",
    recovered: "ArrayLike",
    output_path: str,
):
    """
    Сохранение сравнение результатов.

    Сохраняет сравнение оригинального, поврежденного и восстановленного
    изображений в один файл.

    Args:
        original (ArrayLike): Оригинальное изображение.
        damaged (ArrayLike): Изображение с зануленными пикселями.
        recovered (ArrayLike): Изображение после восстановления.
        output_path (str): Путь для сохранения файла.
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    show_image(axes[0], original, "Оригинальное изображение")
    show_image(axes[1], damaged, "Поврежденное изображение")
    show_image(axes[2], recovered, "Восстановленное изображение")

    fig.suptitle("Результат восстановления изображения методом ADMM", fontsize=16)

    # Проверяем, существует ли директория для сохранения
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, dpi=150)
    plt.close(fig)  # Закрываем фигуру, чтобы она не оставалась в памяти
    print(f"Сравнительное изображение сохранено в: {output_path}")


def save_convergence_plot(
    norm_histories: List[List[float]],
    titles: List[str],
    colors: List[str],
    output_path: str,
):
    """
    Сохраняет графики сходимости ядерной нормы для каждого канала в файл.

    Args:
        norm_histories (List[List[float]]):
            Список историй сходимости (каждая история - список чисел).
        titles (List[str]): Список заголовков для каждого графика.
        colors (List[str]): Список цветов для каждого графика.
        output_path (str): Путь для сохранения файла.
    """
    num_plots = len(norm_histories)
    # squeeze=False гарантирует, что axes всегда
    # будет 2D-массивом, даже если num_plots=1
    fig, axes = plt.subplots(1, num_plots, figsize=(6 * num_plots, 5), squeeze=False)

    for i, history in enumerate(norm_histories):
        ax = axes[0, i]
        ax.plot(history, color=colors[i], linewidth=2)
        ax.set_title(f"Сходимость ({titles[i]})")
        ax.set_xlabel("Итерация")
        ax.set_ylabel("Ядерная норма")
        ax.set_yscale("log")
        ax.grid(True, which="both", linestyle="--", linewidth=0.5)

    fig.suptitle("Сходимость алгоритма по каналам", fontsize=16)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    print(f"График сходимости сохранен в: {output_path}")
