# tests/bot/test_bot.py
"""Тесты для хэндлеров Telegram-бота."""

import base64
import io

import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import (
    CallbackQuery,
    Message,
    PhotoSize,
    ReplyKeyboardRemove,
    User,
)

from denoise_bot.routers import (
    generate_image_button,
    magic_button,
    remove_noise_button,
    start,
    view_history_button,
)
from denoise_bot.routers.button_states import (
    Form,
    GenImage_States,
    History,
)
from denoise_bot.routers.start import (
    language_buttons,
    menu_buttons,
)


# =================================================================================
# === ОБЩИЕ ФИКСТУРЫ ===
# =================================================================================


@pytest.fixture
def mock_message() -> AsyncMock:
    """Фикстура для мока объекта aiogram.types.Message."""
    msg = AsyncMock(spec=Message)
    user = User(id=123, is_bot=False, first_name="Test")
    msg.from_user = user
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    bot = AsyncMock()
    bot.download = AsyncMock(return_value=io.BytesIO(b"test image data"))
    bot.delete_message = AsyncMock()
    msg.bot = bot
    msg.photo = [MagicMock(spec=PhotoSize)]
    msg.photo[-1].file_id = "test_file_id"
    return msg


@pytest.fixture
def mock_callback() -> AsyncMock:
    """Фикстура для мока объекта aiogram.types.CallbackQuery."""
    cb = AsyncMock(spec=CallbackQuery)
    user = User(id=123, is_bot=False, first_name="Test")
    cb.from_user = user
    message = AsyncMock(spec=Message)
    message.edit_text = AsyncMock()
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    cb.message = message
    cb.answer = AsyncMock()
    return cb


@pytest.fixture
def mock_state() -> AsyncMock:
    """Фикстура для мока FSMContext."""
    state = AsyncMock()
    state.set_state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    return state


@pytest.fixture
def mock_supabase() -> MagicMock:
    """Фикстура для мока клиента Supabase."""
    supabase = MagicMock()
    supabase.storage.from_.return_value.upload.return_value = MagicMock()
    supabase.storage.from_.return_value.get_public_url.return_value = (
        "http://test.url/image.png"
    )
    supabase.table.return_value.insert.return_value.execute.return_value = (
        MagicMock()
    )
    supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = (
        []
    )
    return supabase


# =================================================================================
# === ТЕСТЫ ===
# =================================================================================


@pytest.mark.asyncio
@patch("denoise_bot.routers.start.user_langs", {})
async def test_process_language_selection_ru(
        mock_callback: AsyncMock, mock_state: AsyncMock, mock_supabase: MagicMock
):
    """Тестирует обработку выбора русского языка."""
    from denoise_bot.routers.start import user_langs

    mock_callback.data = "lang_ru_RU"
    await start.process_language_selection(
        mock_callback, mock_state, mock_supabase
    )

    assert user_langs[123] == "ru"
    mock_callback.message.edit_text.assert_called_once_with(
        text="Выбран русский язык", reply_markup=None
    )
    mock_callback.message.answer.assert_called_once_with(
        "Выберите действие:", reply_markup=menu_buttons()
    )
    mock_state.set_state.assert_called_once_with(Form.is_choosing)


@pytest.mark.asyncio
@patch("shutil.rmtree")
@patch(
    "denoise_bot.routers.remove_noise_button.mkdtemp", return_value="/tmp/test_dir"
)
@patch("denoise_bot.routers.remove_noise_button.main_model")
async def test_process_received_image_success(
        mock_main_model: MagicMock,
        mock_mkdtemp: MagicMock,
        mock_rmtree: MagicMock,
        mock_message: AsyncMock,
        mock_state: AsyncMock,
        mock_supabase: MagicMock,
):
    """Тестирует успешный сценарий обработки изображения для удаления шума."""
    mock_main_model.run_inpainting_pipeline.return_value = np.zeros(
        (100, 100, 3), dtype=np.uint8
    )

    await remove_noise_button.process_received_image(
        mock_message, mock_state, mock_supabase
    )

    mock_message.answer.assert_any_call("🔄 Ваше изображение обрабатывается...")
    mock_rmtree.assert_called_once_with("/tmp/test_dir", ignore_errors=True)


@pytest.mark.asyncio
async def test_handle_generate_image(
        mock_callback: AsyncMock, mock_state: AsyncMock
):
    """Тестирует запрос на ввод промпта для генерации изображения."""
    await generate_image_button.handle_generate_image(mock_callback, mock_state)
    mock_callback.message.answer.assert_called_once_with(
        "Введите текст для генерации изображения:",
        reply_markup=ReplyKeyboardRemove(),
    )
    mock_state.set_state.assert_called_once_with(
        GenImage_States.waiting_for_prompt
    )


@pytest.mark.asyncio
@patch("denoise_bot.routers.generate_image_button.FusionBrainAPI")
async def test_generate_image_from_text_success(
        mock_fusion_brain_api: MagicMock,
        mock_message: AsyncMock,
        mock_state: AsyncMock,
        mock_supabase: MagicMock,
):
    """Тестирует успешный сценарий генерации изображения по тексту."""
    mock_api_instance = mock_fusion_brain_api.return_value
    mock_api_instance.get_pipeline.return_value = "test_pipeline"
    mock_api_instance.generate.return_value = "test_uuid"
    mock_api_instance.check_generation.return_value = [
        base64.b64encode(b"test_image_data").decode("utf-8")
    ]
    mock_message.text = "a beautiful cat"

    await generate_image_button.generate_image_from_text(
        mock_message, mock_state, mock_supabase
    )

    mock_api_instance.generate.assert_called_once_with(
        "a beautiful cat", "test_pipeline"
    )
    mock_message.answer.assert_called_with(
        "Выберите действие:", reply_markup=menu_buttons()
    )

@pytest.mark.asyncio
async def test_handle_view_history_empty(
        mock_callback: AsyncMock, mock_state: AsyncMock, mock_supabase: MagicMock
):
    """Тестирует случай, когда история запросов пуста."""
    await view_history_button.handle_view_history(
        mock_callback, mock_state, mock_supabase
    )
    mock_callback.message.answer.assert_called_with(
        "У вас еще нет истории запросов."
    )


@pytest.mark.asyncio
async def test_handle_magic_button_sends_cats(
        mock_callback: AsyncMock, mock_state: AsyncMock
):
    """Тестирует работу 'магической' кнопки с отправкой котиков."""
    with patch(
            "denoise_bot.routers.magic_button.os.listdir",
            return_value=["cat1.jpg", "cat2.png"],
    ):
        await magic_button.handle_magic_button(mock_callback, mock_state)

        mock_callback.message.answer_photo.assert_called()
        mock_callback.message.answer.assert_called_with(
            "Вот ваша порция котиков! 😊", reply_markup=menu_buttons()
        )
        mock_state.set_state.assert_called_once_with(Form.is_choosing)
