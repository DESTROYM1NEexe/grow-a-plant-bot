import asyncio
import html
import logging
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from aiogram.utils.backoff import BackoffConfig
from dotenv import load_dotenv

from game import Game

# =========================================================
# CONFIG
# =========================================================

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
    raise RuntimeError(
        "ADMIN_IDS: только числовые Telegram ID через запятую"
    ) from exc

# =========================================================
# BOT & DISPATCHER
# =========================================================

session = AiohttpSession(timeout=60)
bot = Bot(
    token=TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()
game = Game(DB_PATH, ADMIN_IDS)

last_purchase = {}
bot_username = ""

# =========================================================
# HELPERS
# =========================================================

def markup(rows):
    keyboard = []
    for row in rows:
        btn_row = []
        for item in row:
            label, target = item[0], item[1]
            # Поддержка ссылок (url-кнопки) и callback-кнопок
            if target.startswith("https://") or target.startswith("tg://"):
                btn_row.append(InlineKeyboardButton(text=label, url=target))
            else:
                btn_row.append(InlineKeyboardButton(text=label, callback_data=target))
        keyboard.append(btn_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def send_screen(message, screen):
    text, rows = screen
    await message.answer(text, reply_markup=markup(rows))


async def edit_screen(callback, screen):
    text, rows = screen
    try:
        await callback.message.edit_text(text, reply_markup=markup(rows))
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise


async def prepare_message(message):
    if message.chat.type != "private":
        await message.answer("Открой бота в личных сообщениях / Open the bot privately.")
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

    title = game.text(uid, "Открываем кейс", "Opening your case")
    animation = None

    try:
        animation = await message.answer(f"🎁 <b>{title}</b>\n\n▱▱▱")
        for frame in ("▰▱▱", "▰▰▱", "▰▰▰"):
            await asyncio.sleep(1)
            await animation.edit_text(f"✨ <b>{title}</b>\n\n{frame}")
    except TelegramAPIError:
        logging.exception("Case animation failed: uid=%s", uid)

    text, rows = screen
    if animation is not None:
        try:
            await animation.edit_text(text, reply_markup=markup(rows))
            return
        except TelegramAPIError:
            logging.exception("Could not edit reward message: uid=%s", uid)

    await message.answer(text, reply_markup=markup(rows))


# =========================================================
# COMMANDS
# =========================================================

@dp.message(CommandStart())
async def start(message: Message, command: CommandObject = None):
    if message.chat.type != "private":
        await message.answer("Открой бота в личных сообщениях / Open the bot privately.")
        return

    uid = message.from_user.id
    payload = (command.args or "").strip() if command else ""

    if not payload:
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) == 2:
            payload = parts[1].strip()

    # 1. Обработка приглашения в общий сад (coop)
    if payload.startswith("coop_"):
        token = payload[len("coop_"):]
        game.ensure(message.from_user)
        try:
            game.join_coop(uid, message.from_user.full_name, token)
            await message.answer(
                game.text(
                    uid,
                    "🎉 Ты присоединился к общему саду!",
                    "🎉 You joined the shared garden!",
                )
            )
        except ValueError as exc:
            await message.answer(str(exc), parse_mode=None)

        await send_screen(message, game.screen(uid, "coop", bot_name=bot_username))
        return

    # 2. Обработка реферальной ссылки (ref_XXXXX)
    if payload.startswith("ref_") or (payload and not payload.startswith("coop_")):
        ref_arg = payload[len("ref_"):] if payload.startswith("ref_") else payload
        res = game.apply_referral(message.from_user, ref_arg)
        status = res["status"]

        if status == "self_referral":
            await message.answer(
                game.text(
                    uid,
                    "⚠️ <b>Это твоя собственная реферальная ссылка!</b>\n\n"
                    "Отправь её друзьям, чтобы получать по +10 🪙 за каждого, "
                    "а также кейсы за 3 и 10 приглашений.",
                    "⚠️ <b>This is your own referral link!</b>\n\n"
                    "Send it to your friends to earn +10 🪙 per friend and milestone cases.",
                )
            )
        elif status == "already_referred":
            await message.answer(
                game.text(
                    uid,
                    "ℹ️ Ты уже переходил по приглашению ранее.",
                    "ℹ️ You have already joined via an invite link earlier.",
                )
            )
        elif status == "already_player":
            await message.answer(
                game.text(
                    uid,
                    "ℹ️ Ты уже играешь в саду. Реферальный бонус начисляется только новым садоводам!",
                    "ℹ️ You are already a garden player. The bonus is only for new gardeners!",
                )
            )
        elif status == "not_found":
            await message.answer(
                game.text(
                    uid,
                    "⚠️ Пригласивший пользователь не найден. Добро пожаловать в сад!",
                    "⚠️ Referrer not found. Welcome to the garden!",
                )
            )
        elif status == "ok":
            # Награда приглашённому
            await message.answer(
                game.text(
                    uid,
                    "🎉 <b>Добро пожаловать в сад!</b>\n"
                    "Ты перешёл по реферальной ссылке и получил: <b>+20 🪙</b>!",
                    "🎉 <b>Welcome to the garden!</b>\n"
                    "You joined via an invite link and received: <b>+20 🪙</b> bonus!",
                )
            )

            # Уведомление пригласившему
            try:
                inviter_id = res["inviter_id"]
                cnt = res["ref_count"]
                inviter_msg = game.text(
                    inviter_id,
                    f"👥 По твоей ссылке присоединился <b>{html.escape(message.from_user.full_name)}</b>!\n"
                    f"🪙 Начислено: <b>+10 монет</b>\n"
                    f"📊 Всего приглашено: <b>{cnt}</b>",
                    f"👥 <b>{html.escape(message.from_user.full_name)}</b> joined via your link!\n"
                    f"🪙 Reward: <b>+10 coins</b>\n"
                    f"📊 Total invited: <b>{cnt}</b>",
                )

                for milestone, case_title, reward_res in res["milestones"]:
                    inviter_msg += "\n\n" + game.text(
                        inviter_id,
                        f"🏆 <b>Достигнута цель {milestone} приглашённых!</b>\n"
                        f"Получен {case_title}: {reward_res['text_ru']}",
                        f"🏆 <b>Reached {milestone} referrals milestone!</b>\n"
                        f"Granted {case_title}: {reward_res['text_en']}",
                    )

                await bot.send_message(inviter_id, inviter_msg)
            except TelegramAPIError:
                logging.exception("Failed to notify inviter %s", res.get("inviter_id"))
    else:
        game.ensure(message.from_user)

    await send_screen(message, game.screen(uid, "home", bot_name=bot_username))


@dp.message(Command("id"))
async def show_id(message: Message):
    if await prepare_message(message):
        await message.answer(f"Telegram ID: <code>{message.from_user.id}</code>")


@dp.message(Command("paysupport"))
async def support(message: Message):
    if not await prepare_message(message):
        return
    uid = message.from_user.id
    await message.answer(
        game.text(
            uid,
            "Вопросы об оплате, возвратах и счетах:\n",
            "Payment, refund and invoice support:\n",
        ) + SUPPORT,
        parse_mode=None,
    )


@dp.message(
    Command(
        "garden", "shop", "cases", "coop", "collection",
        "admin", "language", "trades", "invoices", "menu",
        "streak", "referrals"
    )
)
async def commands(message: Message):
    if not await prepare_message(message):
        return

    uid = message.from_user.id
    command = message.text.split()[0].split("@")[0][1:]

    routes = {
        "garden": "home",
        "shop": "shop:0",
        "collection": "col:all:0",
        "streak": "streak",
        "referrals": "referrals",
    }
    route = routes.get(command, command)

    try:
        await send_screen(message, game.screen(uid, route, bot_name=bot_username))
    except ValueError as exc:
        await message.answer(str(exc), parse_mode=None)


@dp.message(Command("trade"))
async def trade(message: Message):
    if not await prepare_message(message):
        return

    uid = message.from_user.id
    parts = (message.text or "").split()

    if len(parts) != 4:
        await send_screen(message, game.screen(uid, "trades", bot_name=bot_username))
        return

    try:
        target = int(parts[1])
        tid = game.create_trade(uid, target, parts[2], parts[3])
    except ValueError as exc:
        await message.answer(str(exc), parse_mode=None)
        return

    await send_screen(message, game.screen(uid, f"offer:{tid}", bot_name=bot_username))
    text, rows = game.screen(target, f"offer:{tid}", bot_name=bot_username)

    try:
        await bot.send_message(target, text, reply_markup=markup(rows))
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
        await callback.answer("Open the bot privately.", show_alert=True)
        return

    uid = callback.from_user.id
    data = callback.data or ""

    try:
        game.ensure(callback.from_user)

        if data == "noop":
            await callback.answer()
            return

        # =================================================
        # COOP INVITE
        # =================================================
        if data == "invite":
            m = game.member(uid)
            if m is None or m["owner_id"] != uid:
                raise game.error(
                    uid,
                    "Приглашения доступны владельцу сада.",
                    "Only the garden owner can invite members.",
                )

            await callback.answer()
            link = f"https://t.me/{bot_username}?start=coop_{m['invite_token']}"
            await callback.message.answer(
                game.text(
                    uid,
                    f"🔗 <b>Приглашение в общий сад</b>\n\nОтправь ссылку друзьям:\n{link}",
                    f"🔗 <b>Shared garden invitation</b>\n\nSend this link to friends:\n{link}",
                )
            )
            return

        # =================================================
        # TELEGRAM STARS PAYMENTS
        # =================================================
        if data.startswith("pay:"):
            parts = data.split(":")
            if len(parts) != 3:
                raise ValueError("Invalid purchase")

            _, kind, product = parts
            now = time.monotonic()
            if now - last_purchase.get(uid, 0) < 3:
                await callback.answer(
                    game.text(uid, "Подожди пару секунд.", "Please wait a few seconds."),
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
                    prices=[LabeledPrice(label=title, amount=order["amount"])],
                )
            except TelegramAPIError:
                logging.exception("Invoice send failed: uid=%s payload=%s", uid, order["payload"])
                await callback.message.answer(
                    game.text(
                        uid,
                        "Не удалось отправить счёт. Попробуй позже.",
                        "Could not send invoice. Try again later.",
                    )
                )
            return

        # =================================================
        # GAME ACTIONS
        # =================================================
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
                logging.exception("Trade completion notification failed: uid=%s", uid)

    except ValueError as exc:
        try:
            await callback.answer(str(exc)[:190], show_alert=True)
        except TelegramAPIError:
            await callback.message.answer(str(exc), parse_mode=None)

    except Exception:
        logging.exception("Callback failed: uid=%s data=%s", uid, data)
        await callback.message.answer("Произошла ошибка. Попробуй /start.")


# =========================================================
# STARS PRE-CHECKOUT & SUCCESS
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
        logging.exception("Pre-checkout failed: uid=%s", query.from_user.id)
        valid = False

    if valid:
        await query.answer(ok=True)
    else:
        await query.answer(
            ok=False,
            error_message="Счёт недоступен или истёк. Создай новый / Invoice expired.",
        )


@dp.message(F.successful_payment)
async def successful_payment(message: Message):
    uid = message.from_user.id
    payment = message.successful_payment

    try:
        game.ensure(message.from_user)
        result = game.deliver(uid, payment.invoice_payload, payment)
    except Exception:
        logging.exception(
            "PAYMENT REVIEW NEEDED: uid=%s charge=%s",
            uid, payment.telegram_payment_charge_id
        )
        charge = html.escape(payment.telegram_payment_charge_id)
        await message.answer(
            f"Платёж требует проверки: /paysupport\n<code>{charge}</code>"
        )
        return

    try:
        await present_result(message, uid, result)
    except TelegramAPIError:
        logging.exception("Reward delivered, message failed: uid=%s", uid)


# =========================================================
# STARTUP & MAIN
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
        game.bot_username = bot_username

        await bot.set_my_commands(
            [
                BotCommand(command="start", description="My garden / Мой сад"),
                BotCommand(command="streak", description="📅 7-Day Streak"),
                BotCommand(command="referrals", description="👥 Referrals / Рефералы"),
                BotCommand(command="collection", description="Collection / Коллекция"),
                BotCommand(command="shop", description="Shop / Магазин"),
                BotCommand(command="cases", description="Cases / Кейсы"),
                BotCommand(command="menu", description="Progress / Развитие"),
                BotCommand(command="coop", description="Shared garden / Общий сад"),
                BotCommand(command="trades", description="Trading / Обмен"),
                BotCommand(command="invoices", description="Invoices / Счета"),
                BotCommand(command="language", description="Language / Язык"),
                BotCommand(command="paysupport", description="Support / Поддержка"),
                BotCommand(command="id", description="My Telegram ID"),
            ]
        )

        await bot.delete_webhook(drop_pending_updates=False)

        logging.info("🌱 Green Room started as @%s", bot_username)

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
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped manually.")