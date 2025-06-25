from aiogram import Router

from start import start
from remove_noise_button import remove_noise
from view_history_button import view_history
from magic_button import magic

all_routers = Router()
router.include_routers(
    start, 
    remove_noise, 
    generate_image, 
    view_history,
    magic
)