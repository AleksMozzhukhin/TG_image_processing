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
    matrix_to_decompose = Z - lambda_ / r
    u, s, vt = np.linalg.svd(matrix_to_decompose, full_matrices=False)
    threshold = 1.0 / r
    s_thresholded = np.maximum(s - threshold, 0)
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


def MC_ADMM(Y: np.ndarray, mask: np.ndarray, tol: float, max_iters: int, r: float) -> tuple[np.ndarray, list]:
    """
    Решает задачу матричного дозаполнения с помощью ADMM, управляя итерационным процессом.

    Args:
        Y (np.ndarray): Исходная матрица (канал изображения) с пропусками.
        mask (np.ndarray): Булева маска, где True - известные элементы.
        tol (float): Порог для критерия остановки (изменение ядерной нормы).
        max_iters (int): Максимальное количество итераций.
        r (float): Параметр rho для ADMM.

    Returns:
        tuple[np.ndarray, list]: Кортеж из восстановленной матрицы X и истории ядерной нормы.
    """
    height, width = Y.shape

    # Инициализация переменных
    X = np.random.rand(height, width)
    Z = np.random.rand(height, width)
    lambda_ = np.zeros_like(Y)

    # Начальная проекция, чтобы Z с самого начала удовлетворял ограничениям
    Z[mask] = Y[mask]

    # Инициализация истории для отслеживания сходимости
    u, s, v = np.linalg.svd(X, compute_uv=True)
    norm_prev = np.sum(s)
    norms_history = [norm_prev]

    for i in range(max_iters):
        # Шаг 1: Обновление X (SVT)
        X = MC_update_X(Z, lambda_, r)

        # Шаг 2: Обновление Z (Проекция)
        Z = MC_update_Z(X, lambda_, r, Y, mask)

        # Шаг 3: Обновление двойственной переменной
        lambda_ += (X - Z) * r

        # Проверка сходимости по изменению ядерной нормы
        u, s, v = np.linalg.svd(X, compute_uv=True)
        norm_current = np.sum(s)
        norms_history.append(norm_current)

        if np.abs(norm_current - norm_prev) < tol:
            print(f"Сходимость достигнута на итерации {i + 1}.")
            break

        norm_prev = norm_current

    if i == max_iters - 1:
        print("Достигнуто максимальное количество итераций.")

    return X, norms_history