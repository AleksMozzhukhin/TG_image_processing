import numpy as np


def MC_update_X(Z: np.ndarray, lambda_: np.ndarray, r: float) -> np.ndarray:
    """
    Шаг обновления низкоранговой матрицы X через пороговое сжатие сингулярных чисел (SVT).
    Это соответствует решению задачи: argmin_X ||X||_* + (r/2)||X - Z + U||^2_F

    Args:
        Z (np.ndarray): Текущая оценка матрицы, удовлетворяющей ограничениям.
        lambda_ (np.ndarray): Двойственная переменная (масштабированная).
        r (float): Параметр rho для ADMM, контролирующий штраф.

    Returns:
        np.ndarray: Обновленная низкоранговая матрица X.
    """
    matrix_to_decompose = Z - lambda_ / r
    u, s, vt = np.linalg.svd(matrix_to_decompose, full_matrices=False)

    # Пороговое сжатие (soft-thresholding) сингулярных чисел
    threshold = 1.0 / r
    s_thresholded = np.maximum(s - threshold, 0)

    # Собираем матрицу обратно
    return u @ np.diag(s_thresholded) @ vt


def MC_update_Z(X: np.ndarray, lambda_: np.ndarray, r: float, Y: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Шаг обновления матрицы Z, удовлетворяющей ограничениям на известные пиксели.
    Это соответствует проекции на множество матриц, совпадающих с Y на маске E.

    Args:
        X (np.ndarray): Текущая оценка низкоранговой матрицы.
        lambda_ (np.ndarray): Двойственная переменная.
        r (float): Параметр rho для ADMM.
        Y (np.ndarray): Исходная матрица с пропусками (используется для известных значений).
        mask (np.ndarray): Булева маска, где True - известные элементы.

    Returns:
        np.ndarray: Обновленная матрица Z.
    """
    # Сначала вычисляем временную матрицу
    Z_new = X + lambda_ / r

    # Затем принудительно устанавливаем известные значения из исходной матрицы Y
    Z_new[mask] = Y[mask]

    return Z_new
