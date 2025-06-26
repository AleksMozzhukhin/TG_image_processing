==================================
Справка по API: Логика Telegram-бота
==================================

Этот раздел описывает модули, отвечающие за работу самого Telegram-бота, его интерфейс и взаимодействие с пользователем.

Обработчики команд (Routers)
-------------------------------
Каждый модуль-роутер отвечает за логику, связанную с нажатием определенной кнопки в меню.

.. automodule:: src.routers.start
   :members:

.. automodule:: src.routers.remove_noise_button
   :members:

.. automodule:: src.routers.generate_image_button
   :members:

.. automodule:: src.routers.view_history_button
   :members:

.. automodule:: src.routers.magic_button
   :members:

.. automodule:: src.routers.all_routers
   :members:

Интерфейс и состояния
-----------------------
Модули, определяющие внешний вид кнопок и состояния конечного автомата (FSM) для управления диалогом.

.. automodule:: src.keyboards_buttons
   :members:

.. automodule:: src.routers.button_states
   :members:

Локализация
-----------
Модуль, содержащий строки для разных языков.

.. automodule:: src.routers.messages
   :members: