from aiogram import Router

from .start import start
from .remove_noise_button import remove_noise
from .generate_image_button import generate_image
from .view_history_button import view_history
from .magic_button import magic

all_routers = Router()
all_routers.include_routers(
    start, 
    remove_noise, 
    generate_image, 
    view_history,
    magic
)