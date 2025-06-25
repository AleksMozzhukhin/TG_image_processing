from aiogram import Router

router = Router()
router.include_routers(
    start, 
    remove_noise, 
    generate_image, 
    view_history,
    magic
)