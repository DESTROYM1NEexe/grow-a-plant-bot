import asyncio
import html
import logging
import os
import time

from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.utils.backoff import BackoffConfig
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from dotenv import load_dotenv

from game import Game


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "").strip()
SUPPORT = os.getenv("SUPPORT_CONTACT", "").strip()
DB_PATH = os.getenv("DB_PATH", "garden.db")

if not TOKEN:
    raise RuntimeError("Укажи BOT_TOKEN в .env")

if not SUPPORT:
    raise RuntimeError("Укажи SUPPORT_CONTACT в .env")

try:
    ADMIN_IDS = {
        int(value.strip())
        for value in os.getenv("ADMIN_IDS", "").split(",")
        if value.strip()
    }
except ValueError as exc:
    raise RuntimeError("ADMIN_IDS: только числовые Telegram ID через запятую") from exc


session = AiohttpSession(timeout=60)

bot = Bot(
    token=TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()
game = Game(DB_PATH, ADMIN_IDS)

last_purchase = {}
bot_username = None


def markup(rows):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=label, callback_data=data)
                for label, data in row
            ]
            for row in rows
        ]
    )


async def send_screen(message, screen):
    text, rows = screen
    await message.answer(text, reply_markup=markup(rows))


async def edit_screen(callback, screen):
    text, rows = screen
    try:
        await callback.message.edit_text(
            text,
            reply_markup=markup(rows),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise


async def prepare_message(message):
    if message.chat.type != "private":
        await message.answer(
            "Открой бота в личных сообщениях / Open the bot privately."
        )
        return False

    game.ensure(message.from_user)
    return True


async def present_result(message, uid, result):
    if result is None:
        return

    screen = game.result_screen(uid, result)

    if result["kind"] != "case":
        await send_screen(message, screen)
        return

    # Награда уже записана в базе.
    # Анимация не влияет на розыгрыш.
    title = game.text(uid, "Открываем кейс", "Opening your case")
    animation = None

    try:
        animation = await message.answer(
            f"🎁 <b>{title}</b>\n\n▱▱▱"
        )

        # Без фиктивных «почти выпавших» дорогих растений.
        for frame in ("▰▱▱", "▰▰▱", "▰▰▰"):
            await asyncio.sleep(1)
            await animation.edit_text(
                f"✨ <b>{title}</b>\n\n{frame}"
            )

    except TelegramAPIError:
        logging.exception("Case animation failed: uid=%s", uid)

    text, rows = screen

    if animation is not None:
        try:
            await animation.edit_text(
                text,
                reply_markup=markup(rows),
            )
            return
        except TelegramAPIError:
            logging.exception("Could not edit reward message: uid=%s", uid)

    await message.answer(text, reply_markup=markup(rows))


# =========================================================
# COMMANDS
# =========================================================

@dp.message(CommandStart())
async def start(message: Message):
    if not await prepare_message(message):
        return

    uid = message.from_user.id
    parts = (message.text or "").split(maxsplit=1)

    if len(parts) == 2 and parts[1].startswith("coop_"):
        token = parts[1][len("coop_"):]

        try:
            game.join_coop(
                uid,
                message.from_user.full_name,
                token,
            )
            await message.answer(
                game.text(
                    uid,
                    "🎉 Ты присоединился к общему саду!",
                    "🎉 You joined the shared garden!",
                )
            )
        except ValueError as exc:
            await message.answer(str(exc), parse_mode=None)

        await send_screen(message, game.screen(uid, "coop"))
        return

    await send_screen(message, game.screen(uid, "home"))


@dp.message(Command("id"))
async def show_id(message: Message):
    if await prepare_message(message):
        await message.answer(
            f"Telegram ID: <code>{message.from_user.id}</code>"
        )


@dp.message(Command("paysupport"))
async def support(message: Message):
    if not await prepare_message(message):
        return

    uid = message.from_user.id
    await message.answer(
        game.text(
            uid,
            "Вопросы об оплате, возвратах и зависших счетах:\n",
            "Payment, refund and pending invoice support:\n",
        ) + SUPPORT,
        parse_mode=None,
    )


@dp.message(Command(
    "garden", "shop", "cases", "coop", "collection",
    "admin", "language", "trades", "invoices", "menu",
))
async def commands(message: Message):
    if not await prepare_message(message):
        return

    uid = message.from_user.id
    command = message.text.split()[0].split("@")[0][1:]

    routes = {
        "garden": "home",
        "shop": "shop:0",
        "collection": "col:all:0",
    }
    route = routes.get(command, command)

    try:
        await send_screen(message, game.screen(uid, route))
    except ValueError as exc:
        await message.answer(str(exc), parse_mode=None)


@dp.message(Command("trade"))
async def trade(message: Message):
    if not await prepare_message(message):
        return

    uid = message.from_user.id
    parts = (message.text or "").split()

    if len(parts) != 4:
        await send_screen(message, game.screen(uid, "trades"))
        return

    try:
        target = int(parts[1])
        tid = game.create_trade(
            uid,
            target,
            parts[2],
            parts[3],
        )
    except ValueError as exc:
        await message.answer(str(exc), parse_mode=None)
        return

    await send_screen(
        message,
        game.screen(uid, f"offer:{tid}"),
    )

    text, rows = game.screen(target, f"offer:{tid}")

    try:
        await bot.send_message(
            target,
            text,
            reply_markup=markup(rows),
        )
    except TelegramAPIError:
        logging.exception("Trade notification failed: target=%s", target)
        await message.answer(
            game.text(
                uid,
                "Уведомление не доставлено. Получатель может открыть /trades.",
                "Notification was not delivered. The recipient can open /trades.",
            )
        )


# =========================================================
# CALLBACKS
# =========================================================

@dp.callback_query()
async def callbacks(callback: CallbackQuery):
    if not callback.message or callback.message.chat.type != "private":
        await callback.answer(
            "Open the bot privately.",
            show_alert=True,
        )
        return

    uid = callback.from_user.id
    data = callback.data or ""

    try:
        game.ensure(callback.from_user)

        if data == "noop":
            await callback.answer()
            return

        # Платёжные кнопки.
        if data.startswith("pay:"):
            parts = data.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid purchase")

            _, kind, product = parts

            now = time.monotonic()
            previous = last_purchase.get(uid, 0)

            if now - previous < 3:
                await callback.answer(
                    game.text(
                        uid,
                        "Подожди несколько секунд.",
                        "Please wait a few seconds.",
                    ),
                    show_alert=True,
                )
                return

            last_purchase[uid] = now
            order = game.prepare(uid, kind, product)

            await callback.answer()

            if game.test(uid):
                result = game.deliver(uid, order["payload"])
                await present_result(callback.message, uid, result)
                return

            title, description = game.invoice_text(uid, order)

            try:
                await bot.send_invoice(
                    chat_id=uid,
                    title=title,
                    description=description,
                    payload=order["payload"],
                    provider_token="",
                    currency="XTR",
                    prices=[
                        LabeledPrice(
                            label=title,
                            amount=order["amount"],
                        )
                    ],
                )
            except TelegramAPIError:
                logging.exception(
                    "Invoice send failed: uid=%s payload=%s",
                    uid, order["payload"],
                )
                await callback.message.answer(
                    game.text(
                        uid,
                        "Не удалось отправить счёт. Попробуй позже. "
                        "Неиспользованный счёт можно отменить в /invoices.",
                        "Could not send the invoice. Try again later. "
                        "Unused invoices can be cancelled in /invoices.",
                    )
                )
            return

        # Приглашение в общий сад.
        if data == "invite":
            m = game.member(uid)

            if m is None or m["owner_id"] != uid:
                raise game.error(
                    uid,
                    "Приглашения доступны владельцу сада.",
                    "Only the garden owner can invite members.",
                )

            await callback.answer()

            link = (
                f"https://t.me/{bot_username}"
                f"?start=coop_{m['invite_token']}"
            )

            await callback.message.answer(
                game.text(
                    uid,
                    "🔗 <b>Приглашение в общий сад</b>\n\n"
                    "Отправь ссылку двум друзьям:\n",
                    "🔗 <b>Shared garden invitation</b>\n\n"
                    "Send this link to two friends:\n",
                )
                + link
                + game.text(
                    uid,
                    "\n\nЛюбой человек со ссылкой может занять свободное место.",
                    "\n\nAnyone with the link can take an available spot.",
                )
            )
            return

        screen, notice, notify = game.click(
            uid,
            data,
            callback.from_user.full_name,
        )

        await callback.answer(notice)
        await edit_screen(callback, screen)

        if notify is not None:
            try:
                await bot.send_message(
                    notify,
                    game.text(
                        notify,
                        "🤝 Твоё предложение обмена принято!",
                        "🤝 Your trade offer was accepted!",
                    ),
                )
            except TelegramAPIError:
                logging.exception(
                    "Trade completion notification failed: uid=%s", notify
                )

    except ValueError as exc:
        try:
            await callback.answer(str(exc)[:190], show_alert=True)
        except TelegramAPIError:
            await callback.message.answer(str(exc), parse_mode=None)

    except Exception:
        logging.exception("Callback failed: uid=%s data=%s", uid, data)
        await callback.message.answer(
            "Не удалось выполнить действие. Попробуй /start.\n"
            "Could not complete the action. Try /start."
        )


# =========================================================
# TELEGRAM STARS
# =========================================================

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    try:
        game.ensure(query.from_user)
        valid = game.checkout(
            query.from_user.id,
            query.invoice_payload,
            query.currency,
            query.total_amount,
        )
    except Exception:
        logging.exception(
            "Pre-checkout failed: uid=%s",
            query.from_user.id,
        )
        valid = False

    if valid:
        await query.answer(ok=True)
    else:
        await query.answer(
            ok=False,
            error_message=(
                "Счёт недоступен или истёк. Создай новый в боте. / "
                "Invoice unavailable or expired. Create a new one."
            ),
        )


@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    uid = message.from_user.id
    payment = message.successful_payment

    try:
        game.ensure(message.from_user)
        result = game.deliver(
            uid,
            payment.invoice_payload,
            payment,
        )
    except Exception:
        logging.exception(
            "PAYMENT NEEDS REVIEW: uid=%s charge=%s payload=%s",
            uid,
            payment.telegram_payment_charge_id,
            payment.invoice_payload,
        )

        charge = html.escape(payment.telegram_payment_charge_id)

        await message.answer(
            "Платёж требует проверки. Обратись в /paysupport.\n"
            "Payment needs review. Contact /paysupport.\n\n"
            f"<code>{charge}</code>"
        )
        return

    # Ошибка отправки/анимации не откатывает выданную награду.
    try:
        await present_result(message, uid, result)
    except TelegramAPIError:
        logging.exception(
            "Reward delivered, but notification failed: uid=%s payload=%s",
            uid,
            payment.invoice_payload,
        )


# =========================================================
# STARTUP
# =========================================================

async def main():
    global bot_username

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    try:
        me = await bot.get_me()
        bot_username = me.username

        await bot.set_my_commands([
            BotCommand(command="start", description="My garden / Мой сад"),
            BotCommand(command="collection", description="Collection / Коллекция"),
            BotCommand(command="shop", description="Shop / Магазин"),
            BotCommand(command="cases", description="Cases / Кейсы"),
            BotCommand(command="menu", description="Progress / Развитие"),
            BotCommand(command="coop", description="Shared garden / Общий сад"),
            BotCommand(command="trades", description="Trading / Обмен"),
            BotCommand(command="invoices", description="Invoices / Счета"),
            BotCommand(command="language", description="Language / Язык"),
            BotCommand(command="paysupport", description="Payment support / Поддержка"),
            BotCommand(command="id", description="My Telegram ID"),
        ])

        # Не отбрасываем накопленные события оплаты.
        await bot.delete_webhook(drop_pending_updates=False)

        await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
        polling_timeout=30,
        backoff_config=BackoffConfig(
        min_delay=2.0,
        max_delay=30.0,
        factor=1.5,
        jitter=0.2,
    ),
)

    finally:
        game.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())