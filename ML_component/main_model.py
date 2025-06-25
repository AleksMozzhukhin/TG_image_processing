import os
import numpy as np
import cupy as cp
import utils


def create_mask_from_damaged(damaged_image: np.ndarray, threshold: int = 10) -> np.ndarray:
    """
    Создает маску известных пикселей на основе поврежденного изображения (работает с NumPy массивами).
    Пиксель считается известным, если он не является почти черным.
    """
    # Убеждаемся, что работаем с NumPy массивом на CPU
    if isinstance(damaged_image, cp.ndarray):
        damaged_image = cp.asnumpy(damaged_image)

    # Суммируем значения каналов, чтобы получить одноканальное изображение
    gray_image = np.sum(damaged_image, axis=2)

    # Определяем порог в зависимости от нормализации
    # Если значения в диапазоне [0, 1], порог тоже должен быть в этом диапазоне
    effective_threshold = threshold / 255.0 if damaged_image.max() <= 1.0 else threshold

    # True там, где пиксель не черный
    mask = gray_image > effective_threshold
    return mask


def main():
    # --- Шаг 1: Параметры и пути ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    output_dir = os.path.join(script_dir, 'output')

    ORIGINAL_IMAGE_PATH = os.path.join(data_dir, 'img.png')
    DAMAGED_IMAGE_PATH = os.path.join(data_dir, 'damaged.png')

    RECOVERED_IMAGE_PATH = os.path.join(output_dir, 'recovered.png')
    COMPARISON_PLOT_PATH = os.path.join(output_dir, 'comparison.png')
    CONVERGENCE_PLOT_PATH = os.path.join(output_dir, 'convergence.png')

    ADMM_TOL = 1e-3
    ADMM_MAX_ITERS = 250
    ADMM_RHO = 0.5

    try:
        # --- Шаг 2: Загрузка и подготовка данных ---
        print("Загрузка данных...")
        original_image_np = utils.load_image(ORIGINAL_IMAGE_PATH)
        damaged_image_np = utils.load_image(DAMAGED_IMAGE_PATH)

        print("Создание маски и перенос на GPU...")
        mask_np = create_mask_from_damaged(damaged_image_np)

        image_to_recover_gpu = cp.asarray(damaged_image_np)
        mask_gpu = cp.asarray(mask_np)

        print(f"Данные готовы к обработке на GPU (изображение {image_to_recover_gpu.shape})")


    except FileNotFoundError as e:
        print(f"Критическая ошибка: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()