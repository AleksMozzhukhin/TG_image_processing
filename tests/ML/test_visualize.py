from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from denoise_bot.ML_component import visualize


# --- Фикстуры ---


@pytest.fixture
def sample_image():
    """Простое изображение для тестов."""
    return np.random.rand(10, 10, 3)


@pytest.fixture
def mock_matplotlib():
    """Фикстура для мокирования matplotlib."""
    with (
        patch("matplotlib.pyplot.subplots") as mock_subplots,
        patch("matplotlib.pyplot.savefig") as mock_savefig,
        patch("matplotlib.pyplot.close") as mock_close,
    ):

        mock_fig = MagicMock()
        mock_axes = MagicMock()

        # Создаем два уникальных мока для каждой из будущих осей
        ax1, ax2, ax3 = MagicMock(), MagicMock(), MagicMock()

        # Настраиваем __getitem__ так, чтобы он возвращал
        # нужный мок для нужного индекса.
        def getitem_side_effect(index):
            if index == 0 or index == (0, 0):
                return ax1
            if index == 1 or index == (0, 1):
                return ax2
            if index == 2 or index == (0, 2):
                return ax3
            # Возвращаем дефолтный мок для других случаев
            return MagicMock()

        mock_axes.__getitem__.side_effect = getitem_side_effect
        # ----------------------------

        mock_subplots.return_value = (mock_fig, mock_axes)

        yield {
            "subplots": mock_subplots,
            "savefig": mock_savefig,
            "close": mock_close,
            # Возвращаем наши уникальные моки для проверки
            "axes_mocks": {"ax1": ax1, "ax2": ax2, "ax3": ax3},
        }


# --- Тесты ---


def test_show_image(sample_image):
    """Проверяет корректность вызовов методов matplotlib при отображении изображения."""
    mock_ax = MagicMock()
    title = "Test Title"
    visualize.show_image(mock_ax, sample_image, title=title, grid=True)
    mock_ax.imshow.assert_called_once()
    mock_ax.set_title.assert_called_with(title)
    mock_ax.grid.assert_called_with(True)
    mock_ax.axis.assert_called_with("off")


@patch("os.makedirs")
def test_save_results_comparison(mock_makedirs, mock_matplotlib, sample_image):
    """Проверяет, что функция сравнения результатов вызывает все нужные методы."""
    output_path = "output/comparison.png"

    with patch("denoise_bot.ML_component.visualize.show_image") as mock_show_image:
        visualize.save_results_comparison(
            original=sample_image, damaged=sample_image, recovered=sample_image, output_path=output_path
        )

        mock_makedirs.assert_called_once_with("output", exist_ok=True)
        mock_matplotlib["subplots"].assert_called_once_with(1, 3, figsize=(18, 6))
        assert mock_show_image.call_count == 3

        # Проверяем, что show_image был вызван с нашими уникальными моками осей
        ax1 = mock_matplotlib["axes_mocks"]["ax1"]
        ax2 = mock_matplotlib["axes_mocks"]["ax2"]
        ax3 = mock_matplotlib["axes_mocks"]["ax3"]
        mock_show_image.assert_any_call(ax1, sample_image, "Оригинальное изображение")
        mock_show_image.assert_any_call(ax2, sample_image, "Поврежденное изображение")
        mock_show_image.assert_any_call(ax3, sample_image, "Восстановленное изображение")

        mock_matplotlib["savefig"].assert_called_once_with(output_path, dpi=150)
        mock_matplotlib["close"].assert_called_once()


@patch("os.makedirs")
def test_save_convergence_plot(mock_makedirs, mock_matplotlib):
    """Проверяет, что функция построения графика сходимости вызывает нужные методы."""
    histories = [[10, 5, 2, 1], [12, 6, 3, 1.5]]
    titles = ["Red", "Green"]
    colors = ["red", "green"]
    output_path = "output/convergence.png"

    visualize.save_convergence_plot(histories, titles, colors, output_path)

    mock_makedirs.assert_called_once_with("output", exist_ok=True)

    num_plots = len(histories)
    mock_matplotlib["subplots"].assert_called_once_with(1, num_plots, figsize=(6 * num_plots, 5), squeeze=False)

    # Получаем наши уникальные моки для осей
    ax1 = mock_matplotlib["axes_mocks"]["ax1"]
    ax2 = mock_matplotlib["axes_mocks"]["ax2"]

    # Проверяем, что на КАЖДОЙ из уникальных осей .plot() был вызван ровно ОДИН раз
    assert ax1.plot.call_count == 1
    assert ax2.plot.call_count == 1

    # Проверяем аргументы вызова
    ax1.plot.assert_called_with(histories[0], color=colors[0], linewidth=2)
    ax2.plot.assert_called_with(histories[1], color=colors[1], linewidth=2)

    mock_matplotlib["savefig"].assert_called_once_with(output_path, dpi=150)
    mock_matplotlib["close"].assert_called_once()
