from aiogram import Router

from bot.handler.add_good import router as add_good_router
from bot.handler.check_goods import router as check_goods_router
from bot.handler.check_one import router as check_one_router
from bot.handler.cmd import router as cmd_router
from bot.handler.delete_good import router as delete_good_router

main_router = Router(name='main_router')
main_router.include_router(cmd_router)
main_router.include_router(add_good_router)
main_router.include_router(check_goods_router)
main_router.include_router(check_one_router)
main_router.include_router(delete_good_router)
