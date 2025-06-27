from typing import List, Tuple

from .utils import ArrayLike, BackendModule

try:
    import cupy  # noqa F401
except ImportError:
    pass


def MC_update_X(Z: "ArrayLike", lambda_: "ArrayLike", r: float, np: "BackendModule") -> "ArrayLike":
    """
    Обновление матрицы X.

    Шаг обновления низкоранговой матрицы X через пороговое сжатие сингулярных чисел (SVT).
    Это соответствует решению задачи: argmin_X ||X||_* + (r/2)||X - Z + U||^2_F

    Args:
        Z (ArrayLike): Текущая оценка матрицы, удовлетворяющей ограничениям.
        lambda_ (ArrayLike): Двойственная переменная (масштабированная).
        r (float): Параметр rho для ADMM, контролирующий штраф.
        np (BackendModule): Вычислительный бэкенд (модуль numpy или cupy).

    Returns:
        ArrayLike: Обновленная низкоранговая матрица X
            того же типа, что и входные.
    """
    matrix_to_decompose = Z - lambda_ / r
    u, s, vt = np.linalg.svd(matrix_to_decompose, full_matrices=False)

    # Пороговое сжатие (soft-thresholding) сингулярных чисел
    threshold = 1.0 / r
    s_thresholded = np.maximum(s - threshold, 0)

    return u @ np.diag(s_thresholded) @ vt


def MC_update_Z(X: "ArrayLike", lambda_: "ArrayLike", r: float, Y: "ArrayLike", mask: "ArrayLike") -> "ArrayLike":
    """
    Обновление матрицы Z.

    Шаг обновления матрицы Z, удовлетворяющей ограничениям на известные пиксели.
    Это соответствует проекции на множество матриц, совпадающих с Y на маске E.

    Args:
        X (ArrayLike): Текущая оценка низкоранговой матрицы.
        lambda_ (ArrayLike): Двойственная переменная.
        r (float): Параметр rho для ADMM.
        Y (ArrayLike): Исходная матрица с пропусками (используется для известных значений).
        mask (ArrayLike): Булева маска, где True - известные элементы.

    Returns:
        ArrayLike: Обновленная матрица Z.
    """
    # Сначала вычисляем временную матрицу
    Z_new = X + lambda_ / r

    # Затем принудительно устанавливаем известные значения из исходной матрицы Y
    Z_new[mask] = Y[mask]

    return Z_new


def MC_ADMM(
    Y: "ArrayLike",
    mask: "ArrayLike",
    tol: float,
    max_iters: int,
    r: float,
    backend: "BackendModule",
) -> Tuple["ArrayLike", List[float]]:
    """
    Дозаполняет матрицу с помощью ADMM.

    Решает задачу матричного дозаполнения с помощью ADMM,
    управляя итерационным процессом.

    Args:
        Y (ArrayLike): Исходная матрица (канал изображения) с пропусками.
        mask (ArrayLike): Булева маска, где True - известные элементы.
        tol (float): Порог для критерия остановки (изменение ядерной нормы).
        max_iters (int): Максимальное количество итераций.
        r (float): Параметр rho для ADMM.
        backend (BackendModule): Вычислительный бэкенд для всех операций (модуль numpy или cupy).

    Returns:
        Tuple[ArrayLike, List[float]]: Кортеж, содержащий:
            - Восстановленную матрицу X (на том же бэкенде, что и входные данные).
            - Историю значений ядерной нормы (список чисел float).
    """
    height, width = Y.shape

    # Инициализация переменных
    X = backend.random.rand(height, width)
    Z = backend.random.rand(height, width)
    lambda_ = backend.zeros_like(Y)

    # Начальная проекция, чтобы Z с самого начала удовлетворял ограничениям
    Z[mask] = Y[mask]

    # Инициализация истории для отслеживания сходимости
    u, s, v = backend.linalg.svd(X, compute_uv=True)
    norm_prev = backend.sum(s).get().item() if hasattr(s, "get") else backend.sum(s).item()
    norms_history = [norm_prev]

    for i in range(max_iters):
        # Шаг 1: Обновление X (SVT)
        X = MC_update_X(Z, lambda_, r, backend)

        # Шаг 2: Обновление Z (Проекция)
        Z = MC_update_Z(X, lambda_, r, Y, mask)

        # Шаг 3: Обновление двойственной переменной
        lambda_ += (X - Z) * r

        # Проверка сходимости по изменению ядерной нормы
        u, s, v = backend.linalg.svd(X, compute_uv=True)

        norm_current = backend.sum(s).get().item() if hasattr(s, "get") else backend.sum(s).item()
        norms_history.append(norm_current)

        # abs() для обычных чисел Python, np.abs() для массивов
        if abs(norm_current - norm_prev) < tol:
            print(f"Сходимость достигнута на итерации {i + 1}.")
            break

        norm_prev = norm_current

    else:
        print("Достигнуто максимальное количество итераций.")

    return X, norms_history
