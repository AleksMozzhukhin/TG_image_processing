import os
import matplotlib.pyplot as plt
import numpy as np
import cupy as cp


def _ensure_numpy(array: np.ndarray or cp.ndarray) -> np.ndarray:
    """Вспомогательная функция, которая гарантирует, что массив является NumPy массивом."""
    if isinstance(array, cp.ndarray):
        return cp.asnumpy(array)
    return array


def show_image(ax, image: np.ndarray, title: str = "", grid: bool = False):
    """Отображает одно изображение на предоставленной оси (Axes)."""
    image_np = _ensure_numpy(image)
    ax.imshow(np.clip(image_np, 0, 1))
    ax.set_title(title)
    ax.grid(grid)
    ax.axis('off')


def save_results_comparison(original: np.ndarray, damaged: np.ndarray, recovered: np.ndarray, output_path: str):
    """
    Сохраняет сравнение оригинального, поврежденного и восстановленного изображений в один файл.
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
    plt.savefig(output_path)
    plt.close(fig)  # Закрываем фигуру, чтобы она не оставалась в памяти
    print(f"Сравнительное изображение сохранено в: {output_path}")


def save_convergence_plot(norm_histories: list, titles: list, colors: list, output_path: str):
    """
    Сохраняет графики сходимости ядерной нормы для каждого канала в файл.
    """
    num_plots = len(norm_histories)
    fig, axes = plt.subplots(1, num_plots, figsize=(5 * num_plots, 5), squeeze=False)

    for i, history in enumerate(norm_histories):
        ax = axes[0, i]
        ax.plot(history, color=colors[i], linewidth=2)
        ax.set_title(f"Сходимость ({titles[i]})")
        ax.set_xlabel("Итерация")
        ax.set_ylabel("Ядерная норма")
        ax.set_yscale("log")
        ax.grid(True, which="both", linestyle='--', linewidth=0.5)

    fig.suptitle("Сходимость алгоритма по каналам", fontsize=16)

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_path)
    plt.close(fig)
    print(f"График сходимости сохранен в: {output_path}")