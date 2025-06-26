from aiogram import Router

from .generate_image_button import generate_image
from .magic_button import magic
from .remove_noise_button import remove_noise
from .start import start
from .view_history_button import view_history

all_routers = Router()
all_routers.include_routers(start, remove_noise, generate_image, view_history, magic)
