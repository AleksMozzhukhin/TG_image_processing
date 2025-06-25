import os
import numpy as np  # NumPy для работы с OpenCV и Matplotlib
import cupy as cp  # CuPy для всех тяжелых вычислений на GPU
from . import admm_core
from . import utils
from . import visualize


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


def run_inpainting_pipeline(
        damaged_image_path: str,
        output_dir: str,
        max_iters: int = 250,
        original_image_path: str = None
):
    """
    Главная функция для запуска всего процесса восстановления изображения.

    Args:
        damaged_image_path (str): Путь к поврежденному изображению.
        output_dir (str): Папка для сохранения всех результатов.
        max_iters (int): Максимальное количество итераций для ADMM.
        original_image_path (str, optional): Путь к оригинальному изображению для сравнения.
                                              Если не указан, сравнительный график не создается.
    """
    # --- Пути для сохранения результатов ---
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(damaged_image_path))[0]

    RECOVERED_IMAGE_PATH = os.path.join(output_dir, f"{base_name}_recovered.png")
    COMPARISON_PLOT_PATH = os.path.join(output_dir, f"{base_name}_comparison.png")
    CONVERGENCE_PLOT_PATH = os.path.join(output_dir, f"{base_name}_convergence.png")

    # Параметры ADMM
    ADMM_TOL = 1e-3
    ADMM_RHO = 0.5

    try:
        # --- 1. Загрузка данных (на CPU) ---
        print(f"Загрузка поврежденного изображения: {damaged_image_path}")
        damaged_image_np = utils.load_image(damaged_image_path)

        # --- 2. Создание маски и перенос данных на GPU ---
        print("Создание маски на основе поврежденного изображения...")
        mask_np = create_mask_from_damaged(damaged_image_np)

        print(f"Передача данных на GPU...")
        image_to_recover_gpu = cp.asarray(damaged_image_np)
        mask_gpu = cp.asarray(mask_np)

        # --- 3. Обработка каждого канала на GPU ---
        recovered_channels_gpu = []
        norm_histories = []
        channel_names = ["Красный", "Зелёный", "Синий"]
        for i in range(3):
            print(f"\n--- Восстановление канала: {channel_names[i]} ---")
            channel_data_gpu = image_to_recover_gpu[:, :, i]

            recovered_channel_gpu, history = admm_core.MC_ADMM(
                Y=channel_data_gpu, mask=mask_gpu, tol=ADMM_TOL,
                max_iters=max_iters, r=ADMM_RHO
            )
            recovered_channels_gpu.append(recovered_channel_gpu)
            norm_histories.append(history)

        # --- 4. Сборка результата и возврат на CPU ---
        print("\nСборка и возврат результата на CPU...")
        recovered_image_gpu = cp.stack(recovered_channels_gpu, axis=2)
        recovered_image_np = cp.asnumpy(recovered_image_gpu)

        # --- 5. Сохранение и визуализация ---
        print("Сохранение результатов...")
        utils.save_image(recovered_image_np, RECOVERED_IMAGE_PATH)
        visualize.save_convergence_plot(norm_histories, channel_names, ["red", "green", "blue"], CONVERGENCE_PLOT_PATH)

        if original_image_path:
            print(f"Загрузка оригинального изображения для сравнения: {original_image_path}")
            original_image_np = utils.load_image(original_image_path)
            visualize.save_results_comparison(
                original_image_np, damaged_image_np, recovered_image_np,
                COMPARISON_PLOT_PATH
            )

        print(f"\nВосстановление завершено. Результаты сохранены в папке: {output_dir}")
        return recovered_image_np

    except FileNotFoundError as e:
        print(f"Критическая ошибка: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return None


if __name__ == '__main__':
    # Вызов для тестирования
    script_dir = os.path.dirname(os.path.abspath(__file__))
    damaged_path = os.path.join(script_dir, 'data', 'damaged.png')
    original_path = os.path.join(script_dir, 'data', 'img.png')
    output_path = os.path.join(script_dir, 'output_test')

    run_inpainting_pipeline(
        damaged_image_path=damaged_path,
        output_dir=output_path,
        max_iters=10,
        original_image_path=original_path
    )