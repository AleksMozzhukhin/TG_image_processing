import os
import numpy as np  # NumPy для работы с OpenCV и Matplotlib
import cupy as cp  # CuPy для всех тяжелых вычислений на GPU
import admm_core
import utils
import visualize


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
    # --- Параметры и пути ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    output_dir = os.path.join(script_dir, 'output')  # Папка для результатов

    ORIGINAL_IMAGE_PATH = os.path.join(data_dir, 'img.png')
    DAMAGED_IMAGE_PATH = os.path.join(data_dir, 'damaged.png')

    # Пути для сохранения результатов
    RECOVERED_IMAGE_PATH = os.path.join(output_dir, 'recovered.png')
    COMPARISON_PLOT_PATH = os.path.join(output_dir, 'comparison.png')
    CONVERGENCE_PLOT_PATH = os.path.join(output_dir, 'convergence.png')

    # Параметры ADMM
    ADMM_TOL = 1e-3
    ADMM_MAX_ITERS = 250
    ADMM_RHO = 0.5

    try:
        # --- 1. Загрузка данных (на CPU) ---
        print(f"Загрузка оригинального изображения: {ORIGINAL_IMAGE_PATH}")
        original_image_np = utils.load_image(ORIGINAL_IMAGE_PATH)

        print(f"Загрузка поврежденного изображения: {DAMAGED_IMAGE_PATH}")
        damaged_image_np = utils.load_image(DAMAGED_IMAGE_PATH)

        # --- 2. Создание маски и перенос данных на GPU ---
        print("Создание маски на основе поврежденного изображения...")
        mask_np = create_mask_from_damaged(damaged_image_np)

        print(f"Передача данных (изображение {original_image_np.shape}, маска {mask_np.shape}) на GPU...")
        image_to_recover_gpu = cp.asarray(damaged_image_np)
        mask_gpu = cp.asarray(mask_np)

        # --- 3. Обработка каждого канала на GPU ---
        recovered_channels_gpu = []
        norm_histories = []
        channel_names = ["Красный", "Зелёный", "Синий"]
        channel_colors = ["red", "green", "blue"]

        for i in range(3):
            print(f"\n--- Восстановление канала: {channel_names[i]} ---")
            channel_data_gpu = image_to_recover_gpu[:, :, i]

            recovered_channel_gpu, history = admm_core.MC_ADMM(
                Y=channel_data_gpu, mask=mask_gpu, tol=ADMM_TOL,
                max_iters=ADMM_MAX_ITERS, r=ADMM_RHO
            )
            recovered_channels_gpu.append(recovered_channel_gpu)
            norm_histories.append(history)

        # --- 4. Сборка результата и возврат на CPU ---
        print("\nСборка восстановленного изображения на GPU...")
        recovered_image_gpu = cp.stack(recovered_channels_gpu, axis=2)

        print("Передача финального изображения на CPU...")
        recovered_image_np = cp.asnumpy(recovered_image_gpu)

        # --- 5. Сохранение и визуализация ---
        print("Сохранение результатов...")
        # Сохраняем восстановленное изображение
        utils.save_image(recovered_image_np, RECOVERED_IMAGE_PATH)

        # Сохраняем сравнительный график
        visualize.save_results_comparison(
            original_image_np, damaged_image_np, recovered_image_np,
            COMPARISON_PLOT_PATH
        )
        # Сохраняем график сходимости
        visualize.save_convergence_plot(
            norm_histories, channel_names, channel_colors,
            CONVERGENCE_PLOT_PATH
        )

    except FileNotFoundError as e:
        print(f"Критическая ошибка: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()