====================================
Справка по API: Логика Telegram-бота
====================================

Этот раздел описывает модули, отвечающие за работу самого Telegram-бота, его интерфейс и взаимодействие с пользователем.

Обработчики команд (Routers)
-------------------------------
Каждый модуль-роутер отвечает за логику, связанную с нажатием определенной кнопки в меню.

.. automodule:: denoise_bot.routers.start
   :members:

.. automodule:: denoise_bot.routers.remove_noise_button
   :members:

.. automodule:: denoise_bot.routers.generate_image_button
   :members:

.. automodule:: denoise_bot.routers.view_history_button
   :members:

.. automodule:: denoise_bot.routers.magic_button
   :members:

.. automodule:: denoise_bot.routers.all_routers
   :members:

Интерфейс и состояния
-----------------------
Модули, определяющие внешний вид кнопок и состояния конечного автомата (FSM) для управления диалогом.

.. automodule:: denoise_bot.keyboards_buttons
   :members:

.. automodule:: denoise_bot.routers.button_states
   :members:

Локализация
-----------
Модуль, содержащий строки для разных языков.

.. automodule:: denoise_bot.routers.messages
   :members: