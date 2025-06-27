import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User,  PhotoSize
from src.denoise_bot.routers.start import start
import numpy as np
from ...src.denoise_bot.routers.remove_noise_button import remove_noise
from pathlib import Path
import io
from ...src.denoise_bot.routers.generate_image_button import generate_image
import base64
from io import BytesIO
from ...src.denoise_bot.routers.view_history_button import view_history
import httpx


@pytest.fixture
def mock_message():
    msg = AsyncMock(spec=Message)
    msg.from_user = User(id=123, first_name="Test", is_bot=False)
    msg.answer = AsyncMock()
    return msg

@pytest.fixture
def mock_callback():
    cb = AsyncMock(spec=CallbackQuery)
    cb.from_user = User(id=123, first_name="Test", is_bot=False)
    cb.message = AsyncMock(spec=Message)
    cb.message.edit_text = AsyncMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    return cb

@pytest.fixture
def mock_state():
    state = AsyncMock()
    state.set_state = AsyncMock()
    return state

@pytest.fixture
def mock_supabase():
    return MagicMock()

@pytest.mark.asyncio
async def test_command_start(mock_message, mock_state, mock_supabase):
    await start.command_start(mock_message, mock_state, mock_supabase)
    
    mock_state.set_state.assert_called_once_with(Form.set_language)
    mock_message.answer.assert_called_once_with(
        "Пожалуйста, выберите язык / Please choose your language:",
        reply_markup=language_buttons()
    )

@pytest.mark.asyncio
async def test_process_language_selection_ru(mock_callback, mock_state, mock_supabase):
    mock_callback.data = "lang_ru"
    
    await start.process_language_selection(mock_callback, mock_state, mock_supabase)
    
    assert user_langs[123] == "ru"
    mock_callback.message.edit_text.assert_called_once_with(
        text="Выбран русский язык",
        reply_markup=None
    )
    mock_callback.message.answer.assert_called_once_with(
        "Выберите действие:",
        reply_markup=menu_buttons()
    )
    mock_state.set_state.assert_called_once_with(Form.is_choosing)
    mock_callback.answer.assert_called_once()

@pytest.mark.asyncio
async def test_process_language_selection_en(mock_callback, mock_state, mock_supabase):
    mock_callback.data = "lang_en"
    
    await start.process_language_selection(mock_callback, mock_state, mock_supabase)
    
    assert user_langs[123] == "en"
    # Проверяем что установился английский язык
    mock_callback.message.edit_text.assert_called_once()
    mock_callback.message.answer.assert_called_once()

@pytest.mark.asyncio
async def test_show_main_menu(mock_message):
    # Устанавливаем русский язык для теста
    set_locale("ru")
    
    await start.show_main_menu(mock_message)
    
    mock_message.answer.assert_called_once_with(
        "Выберите действие:",
        reply_markup=menu_buttons()
    )

def test_set_locale():
    set_locale("ru")
    assert _("Выберите действие:") == "Выберите действие:"
    
    set_locale("en")
    # Предполагая что есть перевод для английского
    assert _("Выберите действие:") == "Choose action:"

class TestRemoveNoiseHandlers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_callback = AsyncMock(spec=CallbackQuery)
        self.mock_callback.from_user = User(id=123, first_name="Test", is_bot=False)
        self.mock_callback.message = AsyncMock(spec=Message)
        self.mock_callback.message.answer = AsyncMock()
        self.mock_callback.answer = AsyncMock()
        
        self.mock_message = AsyncMock(spec=Message)
        self.mock_message.from_user = User(id=123, first_name="Test", is_bot=False)
        self.mock_message.photo = [MagicMock(spec=PhotoSize)]
        self.mock_message.photo[-1].file_id = "test_file_id"
        self.mock_message.answer = AsyncMock()
        self.mock_message.answer_photo = AsyncMock()
        
        self.mock_state = AsyncMock()
        self.mock_state.set_state = AsyncMock()
        
        self.mock_supabase = MagicMock()
        self.mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
        self.mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://test.url/image.jpg"
        self.mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        self.mock_bot = AsyncMock()
        self.mock_bot.download = AsyncMock()
        self.mock_message.bot = self.mock_bot
        
        # Мок для main_model
        self.patcher = patch('remove_noise_button.main_model')
        self.mock_model = self.patcher.start()
        self.mock_model.run_inpainting_pipeline.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Мок для временной директории
        self.temp_dir_patcher = patch('remove_noise_button.mkdtemp')
        self.mock_mkdtemp = self.temp_dir_patcher.start()
        self.mock_mkdtemp.return_value = "/tmp/test_dir"
        
        # Мок для shutil
        self.shutil_patcher = patch('remove_noise_button.shutil')
        self.mock_shutil = self.shutil_patcher.start()
        
    def tearDown(self):
        self.patcher.stop()
        self.temp_dir_patcher.stop()
        self.shutil_patcher.stop()

    async def test_handle_remove_noise(self):
        await remove_noise.handle_remove_noise(self.mock_callback, self.mock_state)
        
        self.mock_callback.message.answer.assert_called_once_with(
            "Загрузите вышу картинку",
            reply_markup=None
        )
        self.mock_state.set_state.assert_called_once_with(DelNoise_States.get_image)

    async def test_process_received_image_success(self):
        # Настраиваем моки
        mock_file = io.BytesIO(b"test image data")
        self.mock_bot.download.return_value = mock_file
        
        # Вызываем тестируемую функцию
        await remove_noise.process_received_image(
            self.mock_message, 
            self.mock_state, 
            self.mock_supabase
        )
        
        # Проверяем вызовы
        self.mock_message.answer.assert_called_once_with("🔄 Ваше изображение обрабатывается...")
        self.mock_bot.download.assert_called_once_with("test_file_id")
        self.mock_model.run_inpainting_pipeline.assert_called_once()
        
        # Проверяем сохранение в Supabase
        self.mock_supabase.storage.from_.assert_called_with("images")
        self.mock_supabase.table.assert_called_with("images")
        
        # Проверяем отправку результата
        self.mock_message.answer_photo.assert_called_once()
        
        # Проверяем завершающие действия
        self.mock_message.answer.assert_called_with(
            "Выберите действие:",
            reply_markup=menu_buttons()
        )
        self.mock_state.set_state.assert_called_with(Form.is_choosing)
        self.mock_shutil.rmtree.assert_called_once_with("/tmp/test_dir", ignore_errors=True)

    async def test_process_received_image_model_failure(self):
        # Настраиваем мок модели для возврата None
        self.mock_model.run_inpainting_pipeline.return_value = None
        
        with self.assertLogs(level='ERROR'):
            await remove_noise.process_received_image(
                self.mock_message, 
                self.mock_state, 
                self.mock_supabase
            )
            
        self.mock_message.answer.assert_called_with("Ошибка обработки: Модель вернула None")

    async def test_process_received_image_encoding_failure(self):
        # Настраиваем мок cv2.imencode
        with patch('remove_noise_button.cv2.imencode') as mock_imencode:
            mock_imencode.return_value = (False, None)
            
            with self.assertLogs(level='ERROR'):
                await remove_noise.process_received_image(
                    self.mock_message, 
                    self.mock_state, 
                    self.mock_supabase
                )
                
        self.mock_message.answer.assert_called_with("Ошибка обработки: Ошибка кодирования jpg")

    async def test_process_received_image_upload_failure(self):
        # Настраиваем мок supabase для ошибки загрузки
        self.mock_supabase.storage.from_.return_value.upload.side_effect = Exception("Upload failed")
        
        with self.assertLogs(level='ERROR'):
            await remove_noise.process_received_image(
                self.mock_message, 
                self.mock_state, 
                self.mock_supabase
            )
            
        self.mock_message.answer.assert_called_with("Ошибка обработки: Upload failed")

class TestGenerateImageHandlers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock для callback
        self.mock_callback = AsyncMock(spec=CallbackQuery)
        self.mock_callback.from_user = User(id=123, first_name="Test", is_bot=False)
        self.mock_callback.message = AsyncMock(spec=Message)
        self.mock_callback.message.answer = AsyncMock()
        
        # Mock для message
        self.mock_message = AsyncMock(spec=Message)
        self.mock_message.from_user = User(id=123, first_name="Test", is_bot=False)
        self.mock_message.text = "test prompt"
        self.mock_message.answer = AsyncMock()
        self.mock_message.answer_photo = AsyncMock()
        
        # Mock для state
        self.mock_state = AsyncMock()
        self.mock_state.set_state = AsyncMock()
        
        # Mock для supabase
        self.mock_supabase = MagicMock()
        self.mock_supabase.storage.from_.return_value.upload.return_value = MagicMock()
        self.mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://test.url/image.png"
        self.mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()
        
        # Patch для FusionBrainAPI
        self.api_patcher = patch('generate_image_button.FusionBrainAPI')
        self.mock_api = self.api_patcher.start()
        self.mock_api_instance = MagicMock()
        self.mock_api.return_value = self.mock_api_instance
        self.mock_api_instance.get_pipeline.return_value = "test_pipeline"
        self.mock_api_instance.generate.return_value = "test_uuid"
        self.mock_api_instance.check_generation.return_value = [base64.b64encode(b"test_image_data").decode('utf-8')]

    def tearDown(self):
        self.api_patcher.stop()

    async def test_handle_generate_image(self):
        await generate_image.handle_generate_image(self.mock_callback, self.mock_state)
        
        self.mock_callback.message.answer.assert_called_once_with(
            "Введите текст для генерации изображения:",
            reply_markup=ReplyKeyboardRemove()
        )
        self.mock_state.set_state.assert_called_once_with(GenImage_States.waiting_for_prompt)

    async def test_generate_image_from_text_success(self):
        await generate_image.generate_image_from_text(
            self.mock_message, 
            self.mock_state, 
            self.mock_supabase
        )
        
        # Проверяем вызовы API
        self.mock_api.assert_called_once_with(
            'https://api-key.fusionbrain.ai/',
            "E41777D35F336F1D0C2B00EB08D75F38",
            "1E0A23558FF802583C814E5AD49C4814"
        )
        self.mock_api_instance.get_pipeline.assert_called_once()
        self.mock_api_instance.generate.assert_called_once_with("test prompt", "test_pipeline")
        self.mock_api_instance.check_generation.assert_called_once_with("test_uuid")
        
        # Проверяем сохранение в Supabase
        self.mock_supabase.storage.from_.assert_called_with("images")
        self.mock_supabase.storage.from_.return_value.upload.assert_called_once()
        self.mock_supabase.table.assert_called_with("images")
        
        # Проверяем отправку результата
        self.mock_message.answer_photo.assert_called_once()
        self.mock_message.answer.assert_called_with(
            "Выберите действие:",
            reply_markup=menu_buttons()
        )
        self.mock_state.set_state.assert_called_with(Form.is_choosing)

    async def test_generate_image_from_text_api_failure(self):
        # Настраиваем мок API для ошибки
        self.mock_api_instance.get_pipeline.side_effect = Exception("API error")
        
        await generate_image.generate_image_from_text(
            self.mock_message, 
            self.mock_state, 
            self.mock_supabase
        )
        
        self.mock_message.answer.assert_any_call(
            "Произошла ошибка при обработке: API error"
        )

    async def test_generate_image_from_text_supabase_failure(self):
        # Настраиваем мок supabase для ошибки
        self.mock_supabase.storage.from_.return_value.upload.side_effect = Exception("Storage error")
        
        await generate_image.generate_image_from_text(
            self.mock_message, 
            self.mock_state, 
            self.mock_supabase
        )
        
        self.mock_message.answer.assert_any_call(
            "Произошла ошибка при обработке: Storage error"
        )

    async def test_generate_image_from_text_empty_prompt(self):
        # Тест с пустым промптом
        self.mock_message.text = ""
        
        await generate_image.generate_image_from_text(
            self.mock_message, 
            self.mock_state, 
            self.mock_supabase
        )
        
        self.mock_message.answer.assert_any_call(
            "Произошла ошибка при обработке: "
        )


class TestViewHistoryHandlers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock для callback
        self.mock_callback = AsyncMock(spec=CallbackQuery)
        self.mock_callback.from_user = User(id=123, first_name="Test", is_bot=False)
        self.mock_callback.message = AsyncMock(spec=Message)
        self.mock_callback.message.answer = AsyncMock()
        self.mock_callback.message.edit_text = AsyncMock()
        self.mock_callback.answer = AsyncMock()
        
        # Mock для state
        self.mock_state = AsyncMock()
        self.mock_state.set_state = AsyncMock()
        self.mock_state.get_data = AsyncMock()
        
        # Mock для supabase
        self.mock_supabase = MagicMock()
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = MagicMock()
        
        # Mock для httpx client
        self.client_patcher = patch('view_history_button.httpx.AsyncClient')
        self.mock_client = self.client_patcher.start()
        self.mock_client_instance = AsyncMock()
        self.mock_client.return_value.__aenter__.return_value = self.mock_client_instance
        
        # Mock для BufferedInputFile
        self.buffer_patcher = patch('view_history_button.BufferedInputFile')
        self.mock_buffer = self.buffer_patcher.start()

    def tearDown(self):
        self.client_patcher.stop()
        self.buffer_patcher.stop()

    async def test_handle_view_history_success(self):
        # Настраиваем мок ответа supabase
        test_data = [{
            'id': 1,
            'request': 'test request',
            'created_at': '2023-01-01T00:00:00',
            'image_url': 'http://test.url/image.jpg'
        }]
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = test_data
        
        await view_history.handle_view_history(self.mock_callback, self.mock_state, self.mock_supabase)
        
        # Проверяем вызовы
        self.mock_supabase.table.assert_called_with("images")
        self.mock_callback.message.answer.assert_called_once()
        self.mock_state.update_data.assert_called_once()
        self.mock_state.set_state.assert_called_once_with(History.view_hist)

    async def test_handle_view_history_empty(self):
        # Настраиваем пустой ответ
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
        
        await view_history.handle_view_history(self.mock_callback, self.mock_state, self.mock_supabase)
        
        self.mock_callback.message.answer.assert_called_with("У вас еще нет истории запросов.")

    async def test_handle_view_history_error(self):
        # Настраиваем ошибку
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.side_effect = Exception("DB error")
        
        await view_history.handle_view_history(self.mock_callback, self.mock_state, self.mock_supabase)
        
        self.mock_callback.message.answer.assert_called_with("Ошибка при получении истории: DB error")

    async def test_handle_history_select_success(self):
        # Настраиваем тестовые данные
        test_data = {
            'history_data': {
                '1': {
                    'image_url': 'http://test.url/image.jpg',
                    'request': 'test request'
                }
            }
        }
        self.mock_state.get_data.return_value = test_data
        self.mock_callback.data = "show_image:1"
        
        # Настраиваем мок ответа httpx
        self.mock_client_instance.get.return_value.raise_for_status.return_value = None
        self.mock_client_instance.get.return_value.content = b'test image data'
        
        await view_history.handle_history_select(self.mock_callback, self.mock_state)
        
        # Проверяем вызовы
        self.mock_client_instance.get.assert_called_once_with('http://test.url/image.jpg')
        self.mock_buffer.assert_called_once()
        self.mock_callback.message.answer_photo.assert_called_once()
        self.mock_state.set_state.assert_called_once_with(History.view_again)

    async def test_handle_history_select_not_found(self):
        # Настраиваем пустые данные
        self.mock_state.get_data.return_value = {'history_data': {}}
        self.mock_callback.data = "show_image:1"
        
        await view_history.handle_history_select(self.mock_callback, self.mock_state)
        
        self.mock_callback.answer.assert_called_with("❌ Изображение не найдено", show_alert=True)

    async def test_return_to_history_list(self):
        # Настраиваем тестовые данные
        self.mock_state.get_data.return_value = {
            'photo_message_id': 123,
            'control_message_id': 124
        }
        self.mock_callback.message.chat.id = 456
        
        with patch('view_history_button.handle_view_history') as mock_handle:
            await view_history.return_to_history_list(self.mock_callback, self.mock_state, self.mock_supabase)
            
            # Проверяем удаление сообщений
            self.mock_callback.bot.delete_message.assert_any_call(
                chat_id=456,
                message_id=123
            )
            self.mock_callback.bot.delete_message.assert_any_call(
                chat_id=456,
                message_id=124
            )
            mock_handle.assert_called_once()

    async def test_handle_exit_history(self):
        await view_history.handle_exit_history(self.mock_callback, self.mock_state)
        
        self.mock_callback.message.edit_text.assert_called_once_with(
            "Вы вернулись в главное меню:",
            reply_markup=None
        )
        self.mock_callback.message.answer.assert_called_once_with(
            "Выберите действие:",
            reply_markup=menu_buttons()
        )
        self.mock_state.set_state.assert_called_once_with(Form.is_choosing)

