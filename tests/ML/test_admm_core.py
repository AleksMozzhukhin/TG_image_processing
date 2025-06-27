import pytest
import numpy as np
from denoise_bot.ML_component import admm_core

try:
    import cupy as cp

    CUPY_AVAILABLE = True
    backends = [np, cp]
    backend_ids = ['numpy', 'cupy']
except ImportError:
    CUPY_AVAILABLE = False
    backends = [np]
    backend_ids = ['numpy']


# Фикстура для параметризации тестов по бэкендам (CPU/GPU)
@pytest.fixture(params=backends, ids=backend_ids)
def backend(request):
    """Фикстура, предоставляющая бэкенд (numpy или cupy)."""
    return request.param


# --- Тесты для MC_update_X ---

def test_mc_update_x(backend):
    """
    Проверяет шаг обновления X.
    Создает матрицу, где после вычитания lambda/r одно сингулярное значение
    должно обнулиться, а другое - уменьшиться.
    """
    # Arrange
    Z = backend.array([[1, 0], [0, 0.4]])
    lambda_ = backend.zeros_like(Z)
    r = 2.0  # threshold = 1.0/r = 0.5

    # Ожидаемые сингулярные значения для Z: [1.0, 0.4]
    # Пороговые значения: max(1.0 - 0.5, 0) = 0.5; max(0.4 - 0.5, 0) = 0.0
    expected_X = backend.array([[0.5, 0], [0, 0]])

    # Act
    X_new = admm_core.MC_update_X(Z, lambda_, r, backend)

    # Assert
    # Проверяем с использованием allclose для сравнения float-массивов
    assert backend.allclose(X_new, expected_X, atol=1e-6)


def test_mc_update_x_high_threshold(backend):
    """
    Проверяет, что при высоком пороге (маленьком r) матрица X становится нулевой.
    """
    # Arrange
    Z = backend.random.rand(5, 5)
    lambda_ = backend.zeros_like(Z)
    r = 0.1  # threshold = 1.0/r = 10.0, что больше любого сингулярного значения

    # Act
    X_new = admm_core.MC_update_X(Z, lambda_, r, backend)

    # Assert
    assert backend.allclose(X_new, backend.zeros((5, 5)))


# --- Тесты для MC_update_Z ---

def test_mc_update_z(backend):
    """
    Проверяет шаг обновления Z, который должен сохранять значения
    из Y на позициях, указанных в маске.
    """
    # Arrange
    X = backend.ones((3, 3))
    lambda_ = backend.full((3, 3), 2.0)
    r = 1.0
    Y = backend.full((3, 3), 99.0)
    mask = backend.array([[True, False, True],
                          [False, True, False],
                          [True, False, True]], dtype=bool)

    # Вне маски ожидаем X + lambda_/r = 1.0 + 2.0/1.0 = 3.0
    expected_Z = backend.array([[99.0, 3.0, 99.0],
                                [3.0, 99.0, 3.0],
                                [99.0, 3.0, 99.0]])

    # Act
    Z_new = admm_core.MC_update_Z(X, lambda_, r, Y, mask)

    # Assert
    assert backend.allclose(Z_new, expected_Z)


# --- Тесты для MC_ADMM (интеграционный тест) ---

def test_mc_admm_low_rank_recovery(backend):
    """
    Интеграционный тест для всего алгоритма ADMM.
    Создаем низкоранговую матрицу, "портим" ее, удаляя часть пикселей,
    и проверяем, сможет ли алгоритм ее восстановить.
    """
    # Arrange
    # 1. Создаем исходную низкоранговую матрицу (ранг 1)
    height, width = 20, 30
    u = backend.random.rand(height, 1)
    v = backend.random.rand(1, width)
    original_low_rank_matrix = u @ v

    # 2. Создаем маску и "поврежденную" матрицу Y
    np.random.seed(42)
    mask_np = np.random.rand(height, width) > 0.5
    mask = backend.asarray(mask_np)

    Y = backend.copy(original_low_rank_matrix)
    Y[~mask] = 0  # Зануляем пиксели вне маски

    # 3. Запускаем ADMM
    recovered_X, history = admm_core.MC_ADMM(
        Y=Y,
        mask=mask,
        tol=1e-4,
        max_iters=50,
        r=1.0,
        backend=backend
    )

    # Assert
    assert isinstance(history, list)
    assert len(history) > 1

    # Ключевая проверка: восстановленная матрица должна быть близка к оригиналу.
    # Используем относительную ошибку.
    diff = backend.linalg.norm(recovered_X - original_low_rank_matrix)
    norm_orig = backend.linalg.norm(original_low_rank_matrix)
    relative_error = diff / norm_orig

    # Для 50 итераций ожидаем достаточно хорошего восстановления (ошибка < 10%)
    assert relative_error < 0.1
