import os
from typing import Optional
import numpy as np

from . import admm_core
from . import utils
from . import visualize


def create_mask_from_damaged(damaged_image: np.ndarray,
                             threshold: int = 10
) -> np.ndarray:
    """
    Создает маску известных пикселей на основе поврежденного изображения (работает с NumPy массивами).
    Пиксель считается известным, если он не является почти черным.

    Args:
        damaged_image (np.ndarray): Входное изображение в формате NumPy (H, W, C).
        threshold (int): Порог яркости для определения черного пикселя (в диапазоне 0-255).

    Returns:
        np.ndarray: Двумерная булева маска, где True означает известный (неповрежденный) пиксель.
    """

    # Суммируем значения каналов, чтобы получить одноканальное изображение
    gray_image = damaged_image.sum(axis=2)

    # Определяем порог в зависимости от нормализации
    # Если значения в диапазоне [0, 1], порог тоже должен быть в этом диапазоне
    is_normalized = damaged_image.max() <= 1.0
    effective_threshold = threshold / 255.0 if is_normalized else threshold

    # True там, где пиксель не черный
    return gray_image > effective_threshold


def run_inpainting_pipeline(
        damaged_image_path: str,
        output_dir: str,
        max_iters: int = 250,
        original_image_path: Optional[str] = None,
        use_gpu: bool = True
) -> Optional[np.ndarray]:
    """
    Главная функция для запуска всего процесса восстановления изображения.
    Оркестрирует загрузку данных, выбор бэкенда (CPU/GPU), запуск ADMM и сохранение результатов.

    Args:
        damaged_image_path (str): Путь к поврежденному изображению.
        output_dir (str): Папка для сохранения всех результатов.
        max_iters (int): Максимальное количество итераций для ADMM.
        original_image_path (Optional[str]): Путь к оригинальному изображению для сравнения.
                                              Если не указан (None), сравнительный график не создается.
        use_gpu (bool): Флаг для использования GPU. Если True, будет предпринята попытка
                        использовать CuPy, при неудаче - откат к NumPy.

    Returns:
        Optional[np.ndarray]: Восстановленное изображение в виде NumPy массива, если процесс прошел успешно,
                              иначе None.
    """

    # --- 1. Выбор бэкенда и настройка путей ---
    backend = utils.get_backend(use_gpu)

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(damaged_image_path))[0]

    # Формируем пути для сохранения результатов
    RECOVERED_IMAGE_PATH = os.path.join(output_dir, f"{base_name}_recovered.png")
    COMPARISON_PLOT_PATH = os.path.join(output_dir, f"{base_name}_comparison.png")
    CONVERGENCE_PLOT_PATH = os.path.join(output_dir, f"{base_name}_convergence.png")

    # Параметры ADMM
    ADMM_TOL = 1e-3
    ADMM_RHO = 0.5

    try:
        # --- 2. Загрузка данных (всегда на CPU) ---
        print(f"Загрузка поврежденного изображения: {damaged_image_path}")
        damaged_image_np = utils.load_image(damaged_image_path)

        # --- 3. Создание маски и перенос на выбранный бэкенд ---
        print("Создание маски на основе поврежденного изображения...")
        mask_np = create_mask_from_damaged(damaged_image_np)

        print(f"Передача данных на выбранный бэкенд ({'GPU' if backend is not np else 'CPU'})...")
        image_to_recover = utils.as_backend_array(damaged_image_np, backend)
        mask = utils.as_backend_array(mask_np, backend)

        # --- 4. Обработка каждого канала ---
        recovered_channels = []
        norm_histories = []
        channel_names = ["Красный", "Зелёный", "Синий"]

        for i in range(len(channel_names)):
            print(f"\n--- Восстановление канала: {channel_names[i]} ---")
            channel_data = image_to_recover[:, :, i]

            recovered_channel, history = admm_core.MC_ADMM(
                Y=channel_data, mask=mask, tol=ADMM_TOL,
                max_iters=max_iters, r=ADMM_RHO, backend=backend
            )
            recovered_channels.append(recovered_channel)
            norm_histories.append(history)

        # --- 5. Сборка результата и возврат на CPU ---
        print("\nСборка восстановленного изображения...")
        recovered_image = backend.stack(recovered_channels, axis=2)

        # --- 6. Сохранение и визуализация ---
        print("Сохранение результатов...")
        # Конвертируем финальный результат в NumPy для сохранения и визуализации
        recovered_image_np = utils.as_numpy(recovered_image)
        utils.save_image(recovered_image_np, RECOVERED_IMAGE_PATH)

        visualize.save_convergence_plot(
            norm_histories, channel_names, ["red", "green", "blue"], CONVERGENCE_PLOT_PATH
        )

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
    print("--- Запуск в тестовом режиме ---")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    damaged_path = os.path.join(script_dir, 'data', 'damaged.png')
    original_path = os.path.join(script_dir, 'data', 'img.png')
    output_path = os.path.join(script_dir, 'output_test')

    run_inpainting_pipeline(
        damaged_image_path=damaged_path,
        output_dir=output_path,
        max_iters=250,
        original_image_path=original_path,
        use_gpu=True # Попытаться использовать GPU, если доступен
    )