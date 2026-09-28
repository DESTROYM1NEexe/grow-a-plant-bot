import hashlib
import html
import json
import secrets
import sqlite3
import time
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone

DAILY_COINS = 10
TRADE_FEE = 20
TRADE_LIMIT = 3
PAGE_SIZE = 6
INVOICE_TTL = 15 * 60


def plant(emoji, ru, en, coins, stars, rarity):
    return {
        "emoji": emoji,
        "ru": ru,
        "en": en,
        "coins": coins,
        "stars": stars,
        "rarity": rarity,
    }


PLANTS = {
    "sprout": plant("🌱", "Росток", "Tiny Sprout", 0, 0, 0),
    "cactus": plant("🌵", "Пустынный кактус", "Desert Cactus", 30, 3, 0),
    "berry": plant("🫐", "Черничник", "Blueberry Bush", 50, 5, 0),
    "strawberry": plant("🍓", "Земляничник", "Strawberry Bush", 70, 7, 0),
    "carrot": plant("🥕", "Сладкая морковь", "Sweet Carrot", 90, 9, 0),
    "tulip": plant("🌷", "Розовый тюльпан", "Pink Tulip", 120, 12, 0),
    "daisy": plant("🌼", "Солнечная ромашка", "Sunny Daisy", 150, 15, 0),
    "lavender": plant("🪻", "Лавандовый куст", "Lavender Bush", 220, 22, 1),
    "hibiscus": plant("🌺", "Огненный гибискус", "Fire Hibiscus", 300, 30, 1),
    "rose": plant("🌹", "Багровая роза", "Crimson Rose", 450, 45, 1),
    "lotus": plant("🪷", "Лунный лотос", "Moon Lotus", 1100, 110, 2),
    "lily": plant("🌸", "Нежная лилия", "Soft Lily", 380, 38, 1),
    "dahlia": plant("🌺", "Пурпурная георгина", "Purple Dahlia", 750, 75, 2),
    "moonflower": plant("🌙", "Лунный цветок", "Moon Bloom", 1500, 150, 2),
    "sunflower": plant("🌻", "Золотой подсолнух", "Golden Sunflower", 550, 55, 1),
    "apple": plant("🍎", "Алое яблоко", "Crimson Apple", 180, 18, 0),
    "peach": plant("🍑", "Медовый персик", "Honey Peach", 260, 26, 1),
    "pear": plant("🍐", "Сочная груша", "Juicy Pear", 200, 20, 0),
    "mango": plant("🥭", "Солнечное манго", "Sun Mango", 1800, 180, 2),
    "banana": plant("🍌", "Золотой банан", "Golden Banana", 350, 35, 1),
    "coconut": plant("🥥", "Пальмовый кокос", "Palm Coconut", 650, 65, 1),
    "pineapple": plant("🍍", "Королевский ананас", "Royal Pineapple", 2200, 220, 2),
    "watermelon": plant("🍉", "Сахарный арбуз", "Sugar Melon", 2600, 260, 2),
    "dragonfruit": plant("🐉", "Драконий плод", "Dragonfruit", 4000, 400, 3),
    "starfruit": plant("⭐", "Звёздный плод", "Star Fruit", 5000, 500, 3),
    "raspberry": plant("🫐", "Малиновый куст", "Raspberry Bush", 160, 16, 0),
    "grape": plant("🍇", "Лунный виноград", "Moon Grapes", 420, 42, 1),
    "cranberry": plant("🔴", "Клюквенный куст", "Cranberry Bush", 240, 24, 1),
    "mulberry": plant("🫐", "Белая шелковица", "White Mulberry", 600, 60, 1),
    "papaya": plant("🥭", "Тропическая папайя", "Tropical Papaya", 900, 90, 2),
    "passionfruit": plant("🟣", "Дикая маракуйя", "Wild Passionfruit", 3000, 300, 2),
    "avocado": plant("🥑", "Изумрудный авокадо", "Emerald Avocado", 3200, 320, 2),
    "lime": plant("🍋", "Кислый лайм", "Sour Lime", 280, 28, 1),
    "mushroom": plant("🍄", "Светящийся гриб", "Glow Mushroom", 800, 80, 2),
    "glowshroom": plant("✨", "Неоновый гриб", "Neon Shroom", 6000, 600, 3),
    "bamboo": plant("🎋", "Древний бамбук", "Ancient Bamboo", 7000, 700, 3),
    "pitcher": plant("🌿", "Хищный кувшинник", "Pitcher Plant", 1300, 130, 2),
    "fern": plant("🌿", "Лунный папоротник", "Moon Fern", 1000, 100, 2),
    "cherry": plant("🌸", "Вишнёвое дерево", "Cherry Tree", 3500, 350, 3),
    "palm": plant("🌴", "Золотая пальма", "Golden Palm", 8000, 800, 3),
    "giant_tree": plant("🌳", "Древнее дерево", "Ancient Tree", 15000, 1500, 3),

    "season_frost": plant("❄️", "Морозный цветок", "Frost Flower", 900, 90, 2),
    "season_blossom": plant("🌸", "Весенний первоцвет", "Spring Primrose", 900, 90, 2),
    "season_sun": plant("☀️", "Солнечный цветок", "Sun Bloom", 900, 90, 2),
    "season_amber": plant("🍁", "Янтарный клён", "Amber Maple", 900, 90, 2),
}

CASES = {
    "forest": {
        "ru": "🎁 Лесной кейс", "en": "🎁 Forest Case", "price": 99,
        "drops": [
            ("sprout", 20), ("cactus", 20), ("berry", 18),
            ("strawberry", 15), ("carrot", 12), ("tulip", 7),
            ("daisy", 5), ("lavender", 2), ("rose", 1),
        ],
    },
    "flower": {
        "ru": "💎 Цветочный кейс", "en": "💎 Flower Case", "price": 299,
        "drops": [
            ("cactus", 12), ("berry", 12), ("tulip", 12),
            ("daisy", 10), ("lavender", 12), ("hibiscus", 10),
            ("lily", 9), ("rose", 8), ("sunflower", 6),
            ("dahlia", 4), ("lotus", 3), ("moonflower", 1), ("cherry", 1),
        ],
    },
    "royal": {
        "ru": "👑 Королевский кейс", "en": "👑 Royal Case", "price": 999,
        "drops": [
            ("tulip", 8), ("daisy", 8), ("lavender", 8), ("hibiscus", 10),
            ("rose", 12), ("lily", 10), ("sunflower", 9), ("dahlia", 8),
            ("lotus", 7), ("moonflower", 5), ("mango", 4),
            ("pineapple", 3), ("dragonfruit", 2), ("cherry", 3),
            ("palm", 2), ("giant_tree", 1),
        ],
    },
    "mythic": {
        "ru": "🌌 Мифический кейс", "en": "🌌 Mythic Case", "price": 1199,
        "drops": [
            ("lavender", 7), ("hibiscus", 7), ("rose", 8), ("sunflower", 8),
            ("dahlia", 8), ("lotus", 8), ("moonflower", 7), ("mango", 7),
            ("pineapple", 6), ("watermelon", 5), ("dragonfruit", 5),
            ("starfruit", 4), ("passionfruit", 4), ("avocado", 4),
            ("glowshroom", 3), ("bamboo", 3), ("cherry", 3),
            ("palm", 2), ("giant_tree", 1),
        ],
    },
    "legendary": {
        "ru": "👑 Легендарный кейс", "en": "👑 Legendary Case", "price": 1499,
        "drops": [
            ("lotus", 15), ("moonflower", 15), ("mango", 15),
            ("pineapple", 12), ("dragonfruit", 10), ("starfruit", 10),
            ("glowshroom", 8), ("bamboo", 7), ("cherry", 5),
            ("palm", 2), ("giant_tree", 1),
        ],
    },
}

MUTATIONS = {
    "none": ("", "Без мутации", "No mutation", 1),
    "spark": ("✨", "Сияющее", "Sparkling", 2),
    "rainbow": ("🌈", "Радужное", "Rainbow", 3),
    "gold": ("👑", "Золотое", "Golden", 4),
}

PETS = {
    "bee": ("🐝", "Пчела", "Bee", 150, 1),
    "snail": ("🐌", "Улитка", "Snail", 350, 2),
    "bird": ("🐦", "Птица", "Bird", 700, 3),
    "dragon": ("🐲", "Дракончик", "Baby Dragon", 1500, 5),
}

UPGRADES = {
    "can": ("💧 Лейка", "💧 Watering Can", [120, 300, 650]),
    "fert": ("🌾 Удобрение", "🌾 Fertilizer", [180, 450, 900]),
    "beds": ("🪴 Грядки", "🪴 Beds", [250, 600]),
}

SEASONS = [
    ("❄️ Зима", "❄️ Winter", "season_frost"),
    ("🌸 Весна", "🌸 Spring", "season_blossom"),
    ("☀️ Лето", "☀️ Summer", "season_sun"),
    ("🍂 Осень", "🍂 Autumn", "season_amber"),
]

WEEKS = [
    ("💧 Неделя воды: +1 см", "💧 Water week: +1 cm", 1, 0),
    ("🪙 Неделя монет: +3 🪙", "🪙 Coin week: +3 coins", 0, 3),
    ("🌿 Неделя роста: +2 см", "🌿 Growth week: +2 cm", 2, 0),
    ("🐝 Неделя пчёл: +1 см, +2 🪙", "🐝 Bee week: +1 cm, +2 coins", 1, 2),
]

AWARDS = [
    ("water1", "Первый полив", "First watering", 10),
    ("water7", "7 дней ухода", "7 watering days", 30),
    ("water30", "30 дней ухода", "30 watering days", 60),
    ("plants5", "5 растений", "5 plants", 20),
    ("plants15", "15 растений", "15 plants", 50),
    ("plants30", "30 растений", "30 plants", 100),
    ("height100", "Растение 100 см", "A 100 cm plant", 30),
    ("height500", "Растение 500 см", "A 500 cm plant", 60),
    ("mutation", "Первая мутация", "First mutation", 20),
    ("pet", "Первый питомец", "First pet", 10),
    ("season", "Сезонное растение", "Seasonal plant", 30),
    ("streak7", "Серия 7 дней", "7-day streak", 30),
]


def utc():
    return datetime.now(timezone.utc)


def today():
    return utc().date().isoformat()


def season_index():
    return (utc().month % 12) // 3


def week():
    index = (utc().date() - datetime(2024, 1, 1).date()).days // 7
    return WEEKS[index % len(WEEKS)]


def available(pid):
    return not pid.startswith("season_") or pid == SEASONS[season_index()][2]


def compensation(pid):
    return 3 if pid == "sprout" else max(1, PLANTS[pid]["coins"] // 10)


def roll_mutation():
    value = secrets.randbelow(10000)
    if value < 4:
        return "gold"
    if value < 40:
        return "rainbow"
    if value < 200:
        return "spark"
    return "none"


class Game:
    def __init__(self, path, admins):
        self.admins = set(admins)
        self.bot_username = ""
        self.db = sqlite3.connect(path, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA journal_mode = WAL")
        self.setup()

    def one(self, sql, args=()):
        return self.db.execute(sql, args).fetchone()

    def all(self, sql, args=()):
        return self.db.execute(sql, args).fetchall()

    def column(self, table, name, definition):
        columns = {
            row["name"]
            for row in self.db.execute(f"PRAGMA table_info({table})")
        }
        if name not in columns:
            self.db.execute(
                f"ALTER TABLE {table} ADD COLUMN {name} {definition}"
            )

    def setup(self):
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            lang TEXT NOT NULL DEFAULT 'en',
            coins INTEGER NOT NULL DEFAULT 0,
            active_plant TEXT NOT NULL DEFAULT 'sprout',
            last_water TEXT,
            growth_streak INTEGER NOT NULL DEFAULT 0,
            admin_test INTEGER NOT NULL DEFAULT 1,
            ref_code TEXT UNIQUE,
            referred_by INTEGER,
            streak_days INTEGER NOT NULL DEFAULT 0,
            streak_last_date TEXT
        );

        CREATE TABLE IF NOT EXISTS plants (
            user_id INTEGER NOT NULL REFERENCES users(id),
            plant_id TEXT NOT NULL,
            height INTEGER NOT NULL DEFAULT 0,
            mutation TEXT NOT NULL DEFAULT 'none',
            PRIMARY KEY (user_id, plant_id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            payload TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            plant_id TEXT NOT NULL,
            amount INTEGER NOT NULL DEFAULT 1,
            charge_id TEXT UNIQUE,
            paid INTEGER NOT NULL DEFAULT 0,
            kind TEXT NOT NULL DEFAULT 'growth',
            duplicate_coins INTEGER NOT NULL DEFAULT 0,
            terms TEXT
        );

        CREATE TABLE IF NOT EXISTS gf_profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            can INTEGER NOT NULL DEFAULT 0,
            fert INTEGER NOT NULL DEFAULT 0,
            beds INTEGER NOT NULL DEFAULT 0,
            active_pet TEXT,
            watering_days INTEGER NOT NULL DEFAULT 0,
            ranked INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS gf_beds (
            user_id INTEGER NOT NULL REFERENCES users(id),
            plant_id TEXT NOT NULL,
            PRIMARY KEY (user_id, plant_id)
        );

        CREATE TABLE IF NOT EXISTS gf_pets (
            user_id INTEGER NOT NULL REFERENCES users(id),
            pet_id TEXT NOT NULL,
            PRIMARY KEY (user_id, pet_id)
        );

        CREATE TABLE IF NOT EXISTS gf_awards (
            user_id INTEGER NOT NULL REFERENCES users(id),
            award_id TEXT NOT NULL,
            PRIMARY KEY (user_id, award_id)
        );

        CREATE TABLE IF NOT EXISTS coop_gardens (
            id TEXT PRIMARY KEY,
            owner_id INTEGER NOT NULL REFERENCES users(id),
            invite_token TEXT NOT NULL UNIQUE,
            height INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS coop_members (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            garden_id TEXT NOT NULL
                REFERENCES coop_gardens(id) ON DELETE CASCADE,
            display_name TEXT NOT NULL,
            contribution INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS coop_water_days (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            last_day TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS trades_v2 (
            id TEXT PRIMARY KEY,
            sender INTEGER NOT NULL REFERENCES users(id),
            target INTEGER NOT NULL REFERENCES users(id),
            offered TEXT NOT NULL,
            requested TEXT NOT NULL,
            snapshot TEXT NOT NULL,
            fee INTEGER NOT NULL,
            expires INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            completed_day TEXT
        );

        CREATE TABLE IF NOT EXISTS referrals (
            referrer_id INTEGER NOT NULL REFERENCES users(id),
            referee_id INTEGER PRIMARY KEY REFERENCES users(id),
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS referral_milestones (
            user_id INTEGER NOT NULL REFERENCES users(id),
            milestone INTEGER NOT NULL,
            reward_given TEXT NOT NULL,
            claimed_at INTEGER NOT NULL,
            PRIMARY KEY (user_id, milestone)
        );

        CREATE TABLE IF NOT EXISTS streak_claims (
            user_id INTEGER NOT NULL REFERENCES users(id),
            claim_date TEXT NOT NULL,
            day_number INTEGER NOT NULL,
            reward_desc TEXT NOT NULL,
            PRIMARY KEY (user_id, claim_date)
        );
        """)

        with self.db:
            self.column("users", "growth_streak", "INTEGER NOT NULL DEFAULT 0")
            self.column("users", "admin_test", "INTEGER NOT NULL DEFAULT 1")
            self.column("users", "ref_code", "TEXT")
            self.column("users", "referred_by", "INTEGER")
            self.column("users", "streak_days", "INTEGER NOT NULL DEFAULT 0")
            self.column("users", "streak_last_date", "TEXT")

            self.column("plants", "mutation", "TEXT NOT NULL DEFAULT 'none'")
            self.column("orders", "kind", "TEXT NOT NULL DEFAULT 'growth'")
            self.column("orders", "duplicate_coins", "INTEGER NOT NULL DEFAULT 0")
            self.column("orders", "terms", "TEXT")
            self.column("orders", "result_json", "TEXT")
            self.column("orders", "created_at", "INTEGER NOT NULL DEFAULT 0")
            self.column("orders", "checked", "INTEGER NOT NULL DEFAULT 0")
            self.column("orders", "cancelled", "INTEGER NOT NULL DEFAULT 0")

            self.db.execute("""
                INSERT OR IGNORE INTO gf_profiles (user_id)
                SELECT id FROM users
            """)
            self.db.execute("""
                INSERT OR IGNORE INTO gf_beds (user_id, plant_id)
                SELECT id, active_plant FROM users
            """)

            # Гарантируем, что у всех существующих пользователей есть реферальный код
            empty_codes = self.all(
                "SELECT id FROM users WHERE ref_code IS NULL OR ref_code = ''"
            )
            for row in empty_codes:
                self.db.execute(
                    "UPDATE users SET ref_code = ? WHERE id = ?",
                    (secrets.token_hex(4).upper(), row["id"]),
                )

            for uid in self.admins:
                self.db.execute(
                    "UPDATE gf_profiles SET ranked = 0 WHERE user_id = ?",
                    (uid,),
                )

        for cid, case in CASES.items():
            if sum(w for _, w in case["drops"]) != 100:
                raise RuntimeError(f"Invalid probabilities: {cid}")
            if not all(pid in PLANTS and w > 0 for pid, w in case["drops"]):
                raise RuntimeError(f"Invalid rewards: {cid}")

    def close(self):
        self.db.close()

    def user(self, uid):
        return self.one("SELECT * FROM users WHERE id = ?", (uid,))

    def profile(self, uid):
        return self.one("SELECT * FROM gf_profiles WHERE user_id = ?", (uid,))

    def text(self, uid, ru, en):
        u = self.user(uid)
        lang = u["lang"] if u else "en"
        return ru if lang == "ru" else en

    def name(self, uid, pid):
        p = PLANTS[pid]
        return f"{p['emoji']} {p[self.user(uid)['lang']]}"

    def rarity(self, uid, pid):
        labels = self.text(
            uid,
            ["⚪ Обычное", "🔵 Редкое", "🟣 Эпическое", "🟡 Легендарное"],
            ["⚪ Common", "🔵 Rare", "🟣 Epic", "🟡 Legendary"],
        )
        return labels[PLANTS[pid]["rarity"]]

    def test(self, uid):
        return uid in self.admins and bool(self.user(uid)["admin_test"])

    def owns(self, uid, pid):
        return self.item(uid, pid) is not None

    def item(self, uid, pid):
        return self.one(
            "SELECT * FROM plants WHERE user_id = ? AND plant_id = ?",
            (uid, pid),
        )

    def items(self, uid):
        return [
            row for row in self.all(
                "SELECT * FROM plants WHERE user_id = ? ORDER BY height DESC, plant_id",
                (uid,),
            )
            if row["plant_id"] in PLANTS
        ]

    def beds(self, uid):
        return [
            r["plant_id"]
            for r in self.all(
                """
                SELECT b.plant_id FROM gf_beds b
                JOIN plants p ON p.user_id = b.user_id
                             AND p.plant_id = b.plant_id
                WHERE b.user_id = ? ORDER BY b.plant_id
                """,
                (uid,),
            )
            if r["plant_id"] in PLANTS
        ]

    def get_ref_code(self, uid):
        u = self.user(uid)
        if not u:
            return secrets.token_hex(4).upper()
        code = u["ref_code"]
        if not code:
            code = secrets.token_hex(4).upper()
            with self.db:
                self.db.execute("UPDATE users SET ref_code = ? WHERE id = ?", (code, uid))
        return code

    def ensure(self, tg_user):
        uid = tg_user.id
        language = "ru" if (tg_user.language_code or "").startswith("ru") else "en"

        with self.db:
            existing = self.user(uid)
            if existing is None:
                code = secrets.token_hex(4).upper()
                self.db.execute(
                    """
                    INSERT INTO users (id, lang, coins, ref_code)
                    VALUES (?, ?, 0, ?)
                    """,
                    (uid, language, code),
                )
                self.db.execute(
                    "INSERT INTO plants (user_id, plant_id) VALUES (?, 'sprout')",
                    (uid,),
                )
                self.db.execute(
                    "INSERT INTO gf_profiles (user_id) VALUES (?)",
                    (uid,),
                )
                self.db.execute(
                    "INSERT INTO gf_beds (user_id, plant_id) VALUES (?, 'sprout')",
                    (uid,),
                )
            else:
                if not existing["ref_code"]:
                    code = secrets.token_hex(4).upper()
                    self.db.execute(
                        "UPDATE users SET ref_code = ? WHERE id = ?",
                        (code, uid),
                    )

            current = self.user(uid)
            if current["active_plant"] not in PLANTS or not self.owns(
                uid, current["active_plant"]
            ):
                self.db.execute(
                    "UPDATE users SET active_plant = 'sprout' WHERE id = ?",
                    (uid,),
                )

            if uid in self.admins:
                self.db.execute(
                    "UPDATE gf_profiles SET ranked = 0 WHERE user_id = ?",
                    (uid,),
                )

            self.db.execute(
                "UPDATE coop_members SET display_name = ? WHERE user_id = ?",
                (tg_user.full_name[:64], uid),
            )

    # -------------------- REFERRAL SYSTEM --------------------

    def find_inviter(self, ref_arg):
        clean = (ref_arg or "").strip()
        if clean.startswith("ref_"):
            clean = clean[4:]
        if not clean:
            return None

        # Ищем по ref_code (регистронезависимо) или по числовому Telegram ID
        inviter = self.one(
            "SELECT * FROM users WHERE UPPER(ref_code) = UPPER(?)",
            (clean,),
        )
        if not inviter and clean.isdigit():
            inviter = self.one("SELECT * FROM users WHERE id = ?", (int(clean),))
        return inviter

    def apply_referral(self, tg_user, ref_arg):
        """
        Обработка перехода по ссылке /start ref_XXXXX
        Возвращает словарь с результатом:
        - status: self_referral | not_found | already_referred | already_player | ok
        """
        uid = tg_user.id
        inviter = self.find_inviter(ref_arg)

        if not inviter:
            self.ensure(tg_user)
            return {"status": "not_found"}

        if inviter["id"] == uid:
            self.ensure(tg_user)
            return {"status": "self_referral", "inviter_id": uid}

        with self.db:
            existing = self.user(uid)
            if existing:
                if existing["referred_by"]:
                    return {"status": "already_referred", "inviter_id": existing["referred_by"]}

                prof = self.profile(uid)
                # Если игрок уже ухаживал за садом, он не считается новым приглашённым
                if (prof and prof["watering_days"] > 0) or existing["growth_streak"] > 0:
                    return {"status": "already_player"}

            # Создаём профиль или привязываем пригласившего
            self.ensure(tg_user)

            # Начисляем награды: приглашённому +20 🪙, пригласившему +10 🪙
            self.db.execute(
                "UPDATE users SET coins = coins + 20, referred_by = ? WHERE id = ?",
                (inviter["id"], uid),
            )
            self.db.execute(
                "UPDATE users SET coins = coins + 10 WHERE id = ?",
                (inviter["id"],),
            )
            self.db.execute(
                """
                INSERT OR IGNORE INTO referrals (referrer_id, referee_id, created_at)
                VALUES (?, ?, ?)
                """,
                (inviter["id"], uid, int(time.time())),
            )

            # Подсчёт общего числа рефералов
            ref_count = self.one(
                "SELECT COUNT(*) AS n FROM referrals WHERE referrer_id = ?",
                (inviter["id"],),
            )["n"]

            # Проверка майлстоунов (3 и 10)
            milestones = []
            if ref_count >= 3:
                m3 = self.one(
                    "SELECT 1 FROM referral_milestones WHERE user_id = ? AND milestone = 3",
                    (inviter["id"],),
                )
                if not m3:
                    reward = self.grant_case(inviter["id"], "forest")
                    self.db.execute(
                        """
                        INSERT INTO referral_milestones (user_id, milestone, reward_given, claimed_at)
                        VALUES (?, 3, ?, ?)
                        """,
                        (inviter["id"], reward["text_ru"], int(time.time())),
                    )
                    milestones.append((3, "🎁 Forest Case", reward))

            if ref_count >= 10:
                m10 = self.one(
                    "SELECT 1 FROM referral_milestones WHERE user_id = ? AND milestone = 10",
                    (inviter["id"],),
                )
                if not m10:
                    reward = self.grant_case(inviter["id"], "legendary")
                    self.db.execute(
                        """
                        INSERT INTO referral_milestones (user_id, milestone, reward_given, claimed_at)
                        VALUES (?, 10, ?, ?)
                        """,
                        (inviter["id"], reward["text_ru"], int(time.time())),
                    )
                    milestones.append((10, "👑 Legendary Case", reward))

            return {
                "status": "ok",
                "inviter_id": inviter["id"],
                "ref_count": ref_count,
                "milestones": milestones,
            }

    def referral_info(self, uid):
        count = self.one(
            "SELECT COUNT(*) AS n FROM referrals WHERE referrer_id = ?",
            (uid,),
        )["n"]

        if count < 3:
            progress_str = f"{count}/3 referrals"
        elif count < 10:
            progress_str = f"{count}/10 referrals"
        else:
            progress_str = f"{count}/10 referrals ✅"

        has_m3 = bool(self.one(
            "SELECT 1 FROM referral_milestones WHERE user_id = ? AND milestone = 3",
            (uid,),
        ))
        has_m10 = bool(self.one(
            "SELECT 1 FROM referral_milestones WHERE user_id = ? AND milestone = 10",
            (uid,),
        ))

        return {
            "count": count,
            "progress_str": progress_str,
            "has_m3": has_m3,
            "has_m10": has_m10,
        }

    # -------------------- 7-DAY STREAK --------------------

    def streak_info(self, uid):
        u = self.user(uid)
        d_today = today()
        d_yesterday = (utc().date() - timedelta(days=1)).isoformat()
        last = u["streak_last_date"]
        streak = u["streak_days"]

        if last == d_today:
            display_day = streak if streak > 0 else 1
            can_claim = False
            status_ru = "✅ Награда сегодня получена"
            status_en = "✅ Claimed today"
        elif last == d_yesterday:
            display_day = (streak % 7) + 1
            can_claim = True
            status_ru = "🎁 Доступно к получению!"
            status_en = "🎁 Ready to claim!"
        else:
            display_day = 1
            can_claim = True
            status_ru = "🎁 Доступно к получению (День 1)"
            status_en = "🎁 Ready to claim (Day 1)"

        return {
            "display_day": display_day,
            "streak_days": streak,
            "can_claim": can_claim,
            "progress_str": f"Day {display_day}/7",
            "status_text": self.text(uid, status_ru, status_en),
        }

    def claim_streak(self, uid):
        u = self.user(uid)
        d_today = today()
        d_yesterday = (utc().date() - timedelta(days=1)).isoformat()
        last = u["streak_last_date"]
        streak = u["streak_days"]

        if last == d_today and not self.test(uid):
            raise self.error(
                uid,
                "Сегодня награда уже получена. Возвращайся завтра!",
                "Already claimed today. Come back tomorrow!",
            )

        day_to_claim = (streak % 7) + 1 if last == d_yesterday else 1

        with self.db:
            if day_to_claim == 1:
                self.db.execute(
                    "UPDATE users SET coins = coins + 50 WHERE id = ?",
                    (uid,),
                )
                r_ru, r_en = "+50 🪙", "+50 🪙"

            elif day_to_claim == 2:
                res = self.grant_case(uid, "forest")
                r_ru = f"🎁 Forest Case → {res['text_ru']}"
                r_en = f"🎁 Forest Case → {res['text_en']}"

            elif day_to_claim == 3:
                res = self.grant_random_mutation(uid)
                r_ru = f"🧬 Мутация: {res['ru']}"
                r_en = f"🧬 Mutation: {res['en']}"

            elif day_to_claim == 4:
                res = self.grant_pet(uid, "bee")
                r_ru = f"🐾 Питомец: {res['ru']}"
                r_en = f"🐾 Pet: {res['en']}"

            elif day_to_claim == 5:
                res = self.grant_rare_plant(uid)
                r_ru = f"🌸 Редкое растение: {res['ru']}"
                r_en = f"🌸 Rare Plant: {res['en']}"

            elif day_to_claim == 6:
                res = self.grant_random_upgrade(uid)
                r_ru = f"⚒ Улучшение: {res['ru']}"
                r_en = f"⚒ Upgrade: {res['en']}"

            else:  # Day 7
                res = self.grant_case(uid, "legendary")
                r_ru = f"👑 Legendary Case → {res['text_ru']}"
                r_en = f"👑 Legendary Case → {res['text_en']}"

            text_desc = self.text(uid, r_ru, r_en)

            self.db.execute(
                """
                UPDATE users
                SET streak_days = ?, streak_last_date = ?
                WHERE id = ?
                """,
                (day_to_claim, d_today, uid),
            )
            self.db.execute(
                """
                INSERT OR REPLACE INTO streak_claims (user_id, claim_date, day_number, reward_desc)
                VALUES (?, ?, ?, ?)
                """,
                (uid, d_today, day_to_claim, text_desc),
            )

        return day_to_claim, text_desc

    # -------------------- REWARD GRANT HELPERS --------------------

    def grant_case(self, uid, case_id):
        if case_id not in CASES:
            raise ValueError(f"Unknown case: {case_id}")
        case = CASES[case_id]
        ticket = secrets.randbelow(100)
        chosen_pid = case["drops"][0][0]
        for pid, weight in case["drops"]:
            if ticket < weight:
                chosen_pid = pid
                break
            ticket -= weight

        duplicate = self.owns(uid, chosen_pid)
        if duplicate:
            refund = compensation(chosen_pid)
            self.db.execute(
                "UPDATE users SET coins = coins + ? WHERE id = ?",
                (refund, uid),
            )
            return {
                "case": case_id,
                "pid": chosen_pid,
                "duplicate": True,
                "coins": refund,
                "text_ru": f"{self.name(uid, chosen_pid)} (повтор: +{refund} 🪙)",
                "text_en": f"{self.name(uid, chosen_pid)} (duplicate: +{refund} 🪙)",
            }
        else:
            self.db.execute(
                "INSERT INTO plants (user_id, plant_id) VALUES (?, ?)",
                (uid, chosen_pid),
            )
            return {
                "case": case_id,
                "pid": chosen_pid,
                "duplicate": False,
                "coins": 0,
                "text_ru": f"{self.name(uid, chosen_pid)} (Новое растение!)",
                "text_en": f"{self.name(uid, chosen_pid)} (New plant!)",
            }

    def grant_random_mutation(self, uid):
        items = self.items(uid)
        u = self.user(uid)
        active_row = self.item(uid, u["active_plant"])

        target = None
        if active_row and active_row["mutation"] == "none":
            target = active_row["plant_id"]
        else:
            unmutated = [r["plant_id"] for r in items if r["mutation"] == "none"]
            if unmutated:
                target = secrets.choice(unmutated)

        mut_options = [("gold", 10), ("rainbow", 30), ("spark", 60)]
        roll = secrets.randbelow(100)
        chosen_mut = "spark"
        for m_key, weight in mut_options:
            if roll < weight:
                chosen_mut = m_key
                break
            roll -= weight

        m_data = MUTATIONS[chosen_mut]

        if target:
            self.db.execute(
                "UPDATE plants SET mutation = ? WHERE user_id = ? AND plant_id = ?",
                (chosen_mut, uid, target),
            )
            return {
                "ru": f"{m_data[0]} {m_data[1]} → {self.name(uid, target)}",
                "en": f"{m_data[0]} {m_data[2]} → {self.name(uid, target)}",
            }

        self.db.execute("UPDATE users SET coins = coins + 100 WHERE id = ?", (uid,))
        return {
            "ru": "+100 🪙 (все растения уже имеют мутации)",
            "en": "+100 🪙 (all plants already have mutations)",
        }

    def grant_pet(self, uid, pet_id="bee"):
        owned = self.one(
            "SELECT 1 FROM gf_pets WHERE user_id = ? AND pet_id = ?",
            (uid, pet_id),
        )
        pet = PETS[pet_id]
        if not owned:
            self.db.execute(
                "INSERT INTO gf_pets (user_id, pet_id) VALUES (?, ?)",
                (uid, pet_id),
            )
            p = self.profile(uid)
            if not p["active_pet"]:
                self.db.execute(
                    "UPDATE gf_profiles SET active_pet = ? WHERE user_id = ?",
                    (pet_id, uid),
                )
            return {
                "ru": f"{pet[0]} {pet[1]} (новый питомец добавлен!)",
                "en": f"{pet[0]} {pet[2]} (new pet unlocked!)",
            }
        else:
            coins = pet[3]
            self.db.execute(
                "UPDATE users SET coins = coins + ? WHERE id = ?",
                (coins, uid),
            )
            return {
                "ru": f"{pet[0]} {pet[1]} (уже есть: +{coins} 🪙)",
                "en": f"{pet[0]} {pet[2]} (already owned: +{coins} 🪙)",
            }

    def grant_rare_plant(self, uid):
        candidates = [
            pid for pid, d in PLANTS.items()
            if d["rarity"] >= 1 and not pid.startswith("season_")
        ]
        unowned = [pid for pid in candidates if not self.owns(uid, pid)]
        if unowned:
            chosen = secrets.choice(unowned)
            self.db.execute(
                "INSERT INTO plants (user_id, plant_id) VALUES (?, ?)",
                (uid, chosen),
            )
            return {
                "ru": f"{self.name(uid, chosen)} (Новое редкое растение!)",
                "en": f"{self.name(uid, chosen)} (New rare plant!)",
            }

        self.db.execute("UPDATE users SET coins = coins + 200 WHERE id = ?", (uid,))
        return {
            "ru": "+200 🪙 (вся коллекция редких растений собрана!)",
            "en": "+200 🪙 (all rare plants already collected!)",
        }

    def grant_random_upgrade(self, uid):
        p = self.profile(uid)
        available_upgrades = []
        for key in ("can", "fert", "beds"):
            if p[key] < len(UPGRADES[key][2]):
                available_upgrades.append(key)

        if available_upgrades:
            chosen = secrets.choice(available_upgrades)
            self.db.execute(
                f"UPDATE gf_profiles SET {chosen} = {chosen} + 1 WHERE user_id = ?",
                (uid,),
            )
            upg = UPGRADES[chosen]
            return {
                "ru": f"{upg[0]} (+1 уровень)",
                "en": f"{upg[1]} (+1 level)",
            }

        self.db.execute("UPDATE users SET coins = coins + 250 WHERE id = ?", (uid,))
        return {
            "ru": "+250 🪙 (все улучшения уже максимального уровня!)",
            "en": "+250 🪙 (all upgrades are maxed out!)",
        }

    # -------------------- WATERING & AWARDS --------------------

    def error(self, uid, ru, en):
        return ValueError(self.text(uid, ru, en))

    def spend(self, uid, amount):
        changed = self.db.execute(
            "UPDATE users SET coins = coins - ? WHERE id = ? AND coins >= ?",
            (amount, uid, amount),
        ).rowcount
        if not changed:
            raise self.error(uid, "Не хватает монет 🪙", "Not enough coins 🪙")

    def streak(self, uid):
        u = self.user(uid)
        yesterday = (utc().date() - timedelta(days=1)).isoformat()
        return u["growth_streak"] if u["last_water"] in (today(), yesterday) else 0

    def water(self, uid):
        u, p = self.user(uid), self.profile(uid)
        date = utc().date()
        day = date.isoformat()

        if u["last_water"] == day and not self.test(uid):
            raise self.error(uid, "Сегодня сад уже полит.", "Already watered today.")

        ids = self.beds(uid)
        if not ids:
            raise self.error(uid, "Сначала выбери растения для грядок.", "Choose plants for your beds first.")

        w = week()
        pet = PETS.get(p["active_pet"])
        coins = (
            DAILY_COINS + 2 * p["fert"] + w[3]
            + (pet[4] if pet else 0)
            + (2 if season_index() == 3 else 0)
        )

        event = secrets.randbelow(100)
        extra_growth = int(event < 10)
        if 10 <= event < 17:
            coins += 5
        elif 17 <= event < 20:
            coins += 10

        total, mutations = 0, 0
        streak = u["growth_streak"]
        first_today = u["last_water"] != day

        with self.db:
            for pid in ids:
                row = self.item(uid, pid)
                key = row["mutation"]
                if key not in MUTATIONS:
                    key = "none"
                if key == "none":
                    key = roll_mutation()
                    mutations += int(key != "none")

                growth = (
                    (1 + p["can"]) * MUTATIONS[key][3]
                    + w[2] + extra_growth
                    + int(season_index() == 1)
                )

                self.db.execute(
                    """
                    UPDATE plants SET height = height + ?, mutation = ?
                    WHERE user_id = ? AND plant_id = ?
                    """,
                    (growth, key, uid, pid),
                )
                total += growth

            if first_today:
                yesterday = (date - timedelta(days=1)).isoformat()
                streak = streak + 1 if u["last_water"] == yesterday else 1
                self.db.execute(
                    """
                    UPDATE gf_profiles SET watering_days = watering_days + 1
                    WHERE user_id = ?
                    """,
                    (uid,),
                )

            self.db.execute(
                """
                UPDATE users SET coins = coins + ?, last_water = ?, growth_streak = ?
                WHERE id = ?
                """,
                (coins, day, streak, uid),
            )

        return self.text(
            uid,
            f"💧 Растений: {len(ids)} · +{total} см\n🪙 +{coins} · 🔥 {streak} дн.\n🧬 Новых мутаций: {mutations}",
            f"💧 Plants: {len(ids)} · +{total} cm\n🪙 +{coins} · 🔥 {streak} days\n🧬 New mutations: {mutations}",
        )

    def eligible(self, uid):
        rows = self.items(uid)
        p = self.profile(uid)
        height = max((r["height"] for r in rows), default=0)
        return {
            "water1": p["watering_days"] >= 1,
            "water7": p["watering_days"] >= 7,
            "water30": p["watering_days"] >= 30,
            "plants5": len(rows) >= 5,
            "plants15": len(rows) >= 15,
            "plants30": len(rows) >= 30,
            "height100": height >= 100,
            "height500": height >= 500,
            "mutation": any(r["mutation"] != "none" for r in rows),
            "pet": bool(p["active_pet"]),
            "season": any(r["plant_id"].startswith("season_") for r in rows),
            "streak7": self.streak(uid) >= 7,
        }

    def claim(self, uid):
        eligible = self.eligible(uid)
        amount = 0
        with self.db:
            for key, _, _, reward in AWARDS:
                if eligible[key]:
                    added = self.db.execute(
                        "INSERT OR IGNORE INTO gf_awards (user_id, award_id) VALUES (?, ?)",
                        (uid, key),
                    ).rowcount
                    if added:
                        amount += reward

            self.db.execute(
                "UPDATE users SET coins = coins + ? WHERE id = ?",
                (amount, uid),
            )
        return amount

    # -------------------- ORDERS & PAYMENTS --------------------

    def order(self, payload):
        return self.one("SELECT * FROM orders WHERE payload = ?", (payload,))

    def prepare(self, uid, kind, product):
        free = self.test(uid)
        terms = {"test": free}
        duplicate = 0

        if kind == "growth":
            if not self.owns(uid, product):
                raise self.error(uid, "Растение отсутствует.", "Plant not owned.")
            amount = 1

        elif kind == "plant":
            if product not in PLANTS or PLANTS[product]["stars"] <= 0:
                raise ValueError("Unavailable product")
            if not available(product):
                raise self.error(uid, "Сейчас не сезон растения.", "The plant is out of season.")
            if self.owns(uid, product):
                raise self.error(uid, "Растение уже есть.", "Already owned.")
            amount = PLANTS[product]["stars"]
            duplicate = PLANTS[product]["coins"]

        elif kind == "case":
            if product not in CASES:
                raise ValueError("Unknown case")
            amount = CASES[product]["price"]
            terms["drops"] = [
                {"pid": pid, "weight": weight, "coins": compensation(pid)}
                for pid, weight in CASES[product]["drops"]
            ]
        else:
            raise ValueError("Unknown order kind")

        payload = uuid.uuid4().hex
        with self.db:
            self.db.execute(
                """
                INSERT INTO orders (
                    payload, user_id, plant_id, amount, kind,
                    duplicate_coins, terms, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload, uid, product, amount, kind, duplicate,
                    json.dumps(terms), int(time.time()),
                ),
            )
        return self.order(payload)

    def invoice_text(self, uid, order):
        pid, kind = order["plant_id"], order["kind"]
        if kind == "growth":
            return (
                self.text(uid, "Рост растения +1 см", "Plant growth +1 cm"),
                self.text(
                    uid,
                    f"{self.name(uid, pid)}: +1 см за 1 Star. Разовая покупка.",
                    f"{self.name(uid, pid)}: +1 cm for 1 Star. One-time purchase.",
                ),
            )

        if kind == "plant":
            return (
                self.text(uid, "Растение для сада", "Garden plant"),
                self.text(
                    uid,
                    f"{self.name(uid, pid)}: рост 0 см, навсегда в коллекцию. "
                    f"Цена {order['amount']} Stars.",
                    f"{self.name(uid, pid)}: starts at 0 cm, permanent unlock. "
                    f"Price: {order['amount']} Stars.",
                ),
            )

        return (
            CASES[pid][self.user(uid)["lang"]],
            self.text(
                uid,
                f"Одно случайное растение за {order['amount']} Stars. "
                "Шансы и компенсации показаны в карточке.",
                f"One random plant for {order['amount']} Stars. "
                "Odds and duplicate compensation are shown on the case card.",
            ),
        )

    def checkout(self, uid, payload, currency, amount):
        with self.db:
            order = self.order(payload)
            if order is None:
                return False

            terms = json.loads(order["terms"] or "{}")
            valid = (
                order["user_id"] == uid
                and not order["paid"]
                and not order["cancelled"]
                and not terms.get("test")
                and not self.test(uid)
                and currency == "XTR"
                and amount == order["amount"]
                and order["created_at"] >= time.time() - INVOICE_TTL
            )

            if valid and order["kind"] == "plant":
                valid = (
                    order["plant_id"] in PLANTS
                    and not self.owns(uid, order["plant_id"])
                )
            elif valid and order["kind"] == "growth":
                valid = self.owns(uid, order["plant_id"]) and amount == 1
            elif valid and order["kind"] == "case":
                valid = all(
                    d["pid"] in PLANTS for d in terms.get("drops", [])
                ) and bool(terms.get("drops"))

            if valid:
                self.db.execute(
                    "UPDATE orders SET checked = 1 WHERE payload = ?",
                    (payload,),
                )
            return valid

    def deliver(self, uid, payload, payment=None):
        with self.db:
            order = self.order(payload)
            if order is None or order["user_id"] != uid:
                raise ValueError("Unknown order")

            terms = json.loads(order["terms"] or "{}")
            free = bool(terms.get("test"))

            if free:
                if payment is not None or not self.test(uid):
                    raise ValueError("Invalid test purchase")
                charge = None
            else:
                if (
                    payment is None
                    or payment.currency != "XTR"
                    or payment.total_amount != order["amount"]
                ):
                    raise ValueError("Invalid payment")
                charge = payment.telegram_payment_charge_id

            if order["paid"]:
                if order["charge_id"] != charge:
                    raise ValueError("Another charge for completed order")
                return json.loads(order["result_json"]) if order["result_json"] else None

            if charge and self.one(
                "SELECT 1 FROM orders WHERE charge_id = ?", (charge,)
            ):
                raise ValueError("Charge already used")

            kind, pid = order["kind"], order["plant_id"]
            coins, duplicate = 0, False

            if kind == "growth":
                if pid not in PLANTS or not self.owns(uid, pid):
                    raise ValueError("Growth target unavailable")
                self.db.execute(
                    "UPDATE plants SET height = height + 1 WHERE user_id = ? AND plant_id = ?",
                    (uid, pid),
                )
            elif kind in ("plant", "case"):
                if kind == "case":
                    drops = terms["drops"]
                    if sum(d["weight"] for d in drops) != 100:
                        raise ValueError("Invalid odds")
                    ticket = secrets.randbelow(100)
                    for drop in drops:
                        if ticket < drop["weight"]:
                            pid = drop["pid"]
                            refund_coins = drop["coins"]
                            break
                        ticket -= drop["weight"]
                else:
                    refund_coins = order["duplicate_coins"]

                if pid not in PLANTS:
                    raise ValueError("Plant unavailable")

                duplicate = self.owns(uid, pid)
                if duplicate:
                    coins = refund_coins
                    self.db.execute(
                        "UPDATE users SET coins = coins + ? WHERE id = ?",
                        (coins, uid),
                    )
                else:
                    self.db.execute(
                        "INSERT INTO plants (user_id, plant_id) VALUES (?, ?)",
                        (uid, pid),
                    )
                    if kind == "plant":
                        self.db.execute(
                            "UPDATE users SET active_plant = ? WHERE id = ?",
                            (pid, uid),
                        )
            else:
                raise ValueError("Unknown order kind")

            result = {
                "kind": kind, "pid": pid, "coins": coins,
                "duplicate": duplicate, "free": free,
            }

            self.db.execute(
                """
                UPDATE orders
                SET paid = 1, charge_id = ?, result_json = ?
                WHERE payload = ?
                """,
                (charge, json.dumps(result), payload),
            )
            return result

    def cancel_order(self, uid, payload):
        with self.db:
            changed = self.db.execute(
                """
                UPDATE orders SET cancelled = 1
                WHERE payload = ? AND user_id = ?
                  AND paid = 0 AND checked = 0
                """,
                (payload, uid),
            ).rowcount
        if not changed:
            raise self.error(
                uid,
                "Счёт уже оплачен или платёж начат. Обратись в /paysupport.",
                "Already paid or checkout started. Contact /paysupport.",
            )

    def growth_order_pending(self, uid, pid):
        orders = self.all(
            """
            SELECT * FROM orders
            WHERE user_id = ? AND plant_id = ? AND kind = 'growth'
              AND paid = 0 AND cancelled = 0
            """,
            (uid, pid),
        )
        for order in orders:
            terms = json.loads(order["terms"] or "{}")
            if terms.get("test"):
                continue
            if order["checked"] or order["created_at"] >= time.time() - INVOICE_TTL:
                return True
        return False

    # -------------------- SHARED GARDEN --------------------

    def member(self, uid):
        return self.one(
            """
            SELECT m.*, g.owner_id, g.invite_token, g.height
            FROM coop_members m JOIN coop_gardens g ON g.id = m.garden_id
            WHERE m.user_id = ?
            """,
            (uid,),
        )

    def create_coop(self, uid, display_name):
        with self.db:
            if self.member(uid):
                return
            gid = uuid.uuid4().hex
            self.db.execute(
                "INSERT INTO coop_gardens (id, owner_id, invite_token) VALUES (?, ?, ?)",
                (gid, uid, secrets.token_urlsafe(16)),
            )
            self.db.execute(
                "INSERT INTO coop_members (user_id, garden_id, display_name) VALUES (?, ?, ?)",
                (uid, gid, display_name[:64]),
            )

    def join_coop(self, uid, display_name, token):
        with self.db:
            garden = self.one(
                "SELECT * FROM coop_gardens WHERE invite_token = ?", (token,)
            )
            if garden is None:
                raise self.error(uid, "Приглашение недействительно.", "Invalid invitation.")
            if self.member(uid):
                raise self.error(uid, "Ты уже состоишь в общем саду.", "You already belong to a shared garden.")

            count = self.one(
                "SELECT COUNT(*) AS n FROM coop_members WHERE garden_id = ?",
                (garden["id"],),
            )["n"]
            if count >= 3:
                raise self.error(uid, "В саду уже 3 участника.", "The garden already has 3 members.")

            self.db.execute(
                "INSERT INTO coop_members (user_id, garden_id, display_name) VALUES (?, ?, ?)",
                (uid, garden["id"], display_name[:64]),
            )

    def water_coop(self, uid):
        with self.db:
            m = self.member(uid)
            if m is None:
                raise self.error(uid, "Сначала вступи в сад.", "Join a garden first.")

            last = self.one(
                "SELECT last_day FROM coop_water_days WHERE user_id = ?", (uid,)
            )
            if last and last["last_day"] == today() and not self.test(uid):
                raise self.error(uid, "Сегодня дерево уже полито тобой.", "You already watered the tree today.")

            if not self.test(uid):
                self.db.execute(
                    """
                    INSERT INTO coop_water_days (user_id, last_day)
                    VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET last_day = excluded.last_day
                    """,
                    (uid, today()),
                )

            self.db.execute(
                "UPDATE coop_gardens SET height = height + 1 WHERE id = ?",
                (m["garden_id"],),
            )
            self.db.execute(
                "UPDATE coop_members SET contribution = contribution + 1 WHERE user_id = ?",
                (uid,),
            )

    def leave_coop(self, uid):
        with self.db:
            m = self.member(uid)
            if m is None:
                return

            self.db.execute("DELETE FROM coop_members WHERE user_id = ?", (uid,))
            other = self.one(
                "SELECT user_id FROM coop_members WHERE garden_id = ? ORDER BY user_id LIMIT 1",
                (m["garden_id"],),
            )
            if other is None:
                self.db.execute("DELETE FROM coop_gardens WHERE id = ?", (m["garden_id"],))
            elif m["owner_id"] == uid:
                self.db.execute(
                    "UPDATE coop_gardens SET owner_id = ?, invite_token = ? WHERE id = ?",
                    (other["user_id"], secrets.token_urlsafe(16), m["garden_id"]),
                )

    # -------------------- TRADING --------------------

    def tradeable_users(self, uid, target):
        for person in (uid, target):
            p = self.profile(person)
            if p is None or not p["ranked"] or person in self.admins:
                raise self.error(
                    uid,
                    "Получатель должен открыть бота. Тестовые профили не торгуют.",
                    "The recipient must start the bot. Test profiles cannot trade.",
                )

    def snapshot(self, owner, pid):
        item = self.item(owner, pid)
        if item is None:
            return None
        return {"height": item["height"], "mutation": item["mutation"]}

    def create_trade(self, uid, target, offered, requested):
        if uid == target or offered == requested or "sprout" in (offered, requested):
            raise self.error(uid, "Нельзя обменять росток, одинаковые растения или торговать с собой.", "Sprouts, identical plants and self-trades are not allowed.")

        if offered not in PLANTS or requested not in PLANTS:
            raise self.error(uid, "Неверный ID растения.", "Invalid plant ID.")

        self.tradeable_users(uid, target)

        with self.db:
            a, b = self.snapshot(uid, offered), self.snapshot(target, requested)
            if a is None or b is None:
                raise self.error(uid, "У участника нет нужного растения.", "A participant does not own the plant.")
            if self.owns(uid, requested) or self.owns(target, offered):
                raise self.error(uid, "Получатель уже имеет это растение.", "A recipient already owns this plant.")

            count = self.one(
                """
                SELECT COUNT(*) AS n FROM trades_v2
                WHERE sender = ? AND status = 'pending' AND expires > ?
                """,
                (uid, int(time.time())),
            )["n"]
            if count >= 3:
                raise self.error(uid, "Уже есть 3 активных предложения.", "You already have 3 active offers.")

            tid = uuid.uuid4().hex
            self.db.execute(
                """
                INSERT INTO trades_v2 (
                    id, sender, target, offered, requested, snapshot, fee, expires
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tid, uid, target, offered, requested,
                    json.dumps({"a": a, "b": b}),
                    TRADE_FEE, int(time.time()) + 86400,
                ),
            )
        return tid

    def accept_trade(self, uid, tid):
        with self.db:
            offer = self.one("SELECT * FROM trades_v2 WHERE id = ?", (tid,))
            if (
                offer is None or offer["target"] != uid
                or offer["status"] != "pending"
                or offer["expires"] <= time.time()
            ):
                raise self.error(uid, "Предложение недоступно.", "Offer unavailable.")

            sender, target = offer["sender"], offer["target"]
            self.tradeable_users(uid, target)
            self.tradeable_users(uid, sender)

            for person in (sender, target):
                count = self.one(
                    """
                    SELECT COUNT(*) AS n FROM trades_v2
                    WHERE status = 'done' AND completed_day = ?
                      AND (sender = ? OR target = ?)
                    """,
                    (today(), person, person),
                )["n"]
                if count >= TRADE_LIMIT:
                    raise self.error(uid, "Достигнут дневной лимит обменов.", "Daily trade limit reached.")

            a = self.snapshot(sender, offer["offered"])
            b = self.snapshot(target, offer["requested"])
            saved = json.loads(offer["snapshot"])

            if a is None or b is None or a != saved["a"] or b != saved["b"]:
                raise self.error(uid, "Растения изменились. Создайте новое предложение.", "Plants changed. Create a new offer.")

            if self.owns(sender, offer["requested"]) or self.owns(target, offer["offered"]):
                raise self.error(uid, "У получателя уже есть растение.", "A recipient already owns the plant.")

            for owner, pid in (
                (sender, offer["offered"]), (target, offer["requested"])
            ):
                if self.growth_order_pending(owner, pid):
                    raise self.error(
                        uid,
                        "Есть незавершённый счёт роста. Открой раздел «Счета».",
                        "A growth invoice is pending. Open Invoices.",
                    )

            self.spend(sender, offer["fee"])
            self.spend(target, offer["fee"])

            for owner, recipient, pid, item in (
                (sender, target, offer["offered"], a),
                (target, sender, offer["requested"], b),
            ):
                self.db.execute(
                    "DELETE FROM gf_beds WHERE user_id = ? AND plant_id = ?",
                    (owner, pid),
                )
                self.db.execute(
                    "DELETE FROM plants WHERE user_id = ? AND plant_id = ?",
                    (owner, pid),
                )
                self.db.execute(
                    "INSERT INTO plants (user_id, plant_id, height, mutation) VALUES (?, ?, ?, ?)",
                    (recipient, pid, item["height"], item["mutation"]),
                )
                self.db.execute(
                    "UPDATE users SET active_plant = 'sprout' WHERE id = ? AND active_plant = ?",
                    (owner, pid),
                )

            self.db.execute(
                "UPDATE trades_v2 SET status = 'done', completed_day = ? WHERE id = ?",
                (today(), tid),
            )
        return sender

    # -------------------- SCREENS --------------------

    def nav(self, uid):
        t = lambda ru, en: self.text(uid, ru, en)
        return [
            [(t("🏡 Сад", "🏡 Garden"), "home"), (t("🌿 Коллекция", "🌿 Collection"), "col:all:0")],
            [(t("🛍 Магазин", "🛍 Shop"), "shop:0"), (t("🎁 Кейсы", "🎁 Cases"), "cases")],
            [(t("🧭 Развитие", "🧭 Progress"), "menu"), (t("👥 Общий сад", "👥 Shared garden"), "coop")],
        ]

    def screen(self, uid, route="home", bot_name=None):
        t = lambda ru, en: self.text(uid, ru, en)
        u, p = self.user(uid), self.profile(uid)
        parts = route.split(":")
        action = parts[0]
        rows = []
        text = ""

        current_bot = bot_name or self.bot_username or "bot"

        if action == "home":
            pid = u["active_plant"]
            item = self.item(uid, pid)
            m = MUTATIONS.get(item["mutation"], MUTATIONS["none"])
            thresholds = [0, 10, 30, 100, 500, 1000]
            height = item["height"]
            next_level = next((x for x in thresholds if x > height), None)
            progress = t("Высшая стадия ✨", "Highest stage ✨")
            if next_level is not None:
                lower = max(x for x in thresholds if x <= height)
                filled = (height - lower) * 10 // (next_level - lower)
                progress = "▰" * filled + "▱" * (10 - filled)
                progress += f"\n🎯 {next_level}"

            s_info = self.streak_info(uid)
            r_info = self.referral_info(uid)

            text = (
                "🌱 <b>GREEN ROOM</b>\n\n"
                f"<b>{self.name(uid, pid)}</b>\n"
                f"{self.rarity(uid, pid)}\n"
                f"{m[0]} {t(m[1], m[2])}\n\n"
                f"📏 {height} {t('см', 'cm')}\n{progress}\n\n"
                f"🪙 {u['coins']} · 🔥 {self.streak(uid)} {t('дн.', 'days')}\n"
                f"📅 <b>{s_info['progress_str']}</b> · 👥 <b>{r_info['progress_str']}</b>"
            )

            ids = self.beds(uid)
            text += f"\n\n🪴 {len(ids)}/{1 + p['beds']}"
            for bed in ids:
                text += f"\n• {self.name(uid, bed)}"

            ready = self.test(uid) or u["last_water"] != today()
            text += "\n\n" + (
                t("💧 Можно полить", "💧 Ready to water")
                if ready else t("✅ Сегодня полито", "✅ Watered today")
            )
            text += "\n" + t("Новый день: 00:00 UTC", "New day: 00:00 UTC")
            if self.test(uid):
                text += t("\n\n👑 Бесплатный тестовый режим", "\n\n👑 Free test mode")

            rows = [
                [(t("💧 Полить грядки", "💧 Water beds"), "water")],
                [
                    (t("📅 7-Day Streak", "📅 7-Day Streak"), "streak"),
                    (t("👥 Рефералы", "👥 Referrals"), "referrals"),
                ],
                [(t("🪴 Настроить грядки", "🪴 Manage beds"), "beds")],
                [(
                    t("👑 +1 см бесплатно", "👑 +1 cm free")
                    if self.test(uid) else t("⭐ +1 см за 1 Star", "⭐ +1 cm for 1 Star"),
                    f"pay:growth:{pid}",
                )],
                *self.nav(uid),
                [("🌐 Русский / English", "language")],
            ]
            if uid in self.admins:
                rows.append([(t("👑 Администратор", "👑 Admin"), "admin")])
            return text, rows

        if action == "menu":
            text = t(
                "🧭 <b>Развитие сада</b>\n\nВыбирай разделы для улучшений, наград и заданий:",
                "🧭 <b>Garden progress</b>\n\nSelect a section to improve your garden, claim rewards and tasks:",
            )
            rows = [
                [(t("📅 7-Day Streak", "📅 7-Day Streak"), "streak"), (t("👥 Рефералы", "👥 Referrals"), "referrals")],
                [(t("🏆 Достижения", "🏆 Achievements"), "awards"), (t("📊 Рейтинг", "📊 Ranking"), "top")],
                [(t("⚒ Улучшения", "⚒ Upgrades"), "upgrades"), (t("🐾 Питомцы", "🐾 Pets"), "pets")],
                [(t("🧬 Мутации", "🧬 Mutations"), "mutations"), (t("📅 События", "📅 Events"), "events")],
                [(t("🤝 Обмен", "🤝 Trading"), "trades"), (t("🧾 Счета", "🧾 Invoices"), "invoices")],
            ]

        elif action == "streak":
            s_info = self.streak_info(uid)
            cur_day = s_info["display_day"]
            can_claim = s_info["can_claim"]

            text = t(
                "📅 <b>7-Day Streak</b>\n\n"
                f"Серия: <b>{s_info['progress_str']}</b>\n"
                f"Статус: <b>{s_info['status_text']}</b>\n\n",
                "📅 <b>7-Day Streak</b>\n\n"
                f"Streak: <b>{s_info['progress_str']}</b>\n"
                f"Status: <b>{s_info['status_text']}</b>\n\n",
            )

            streak_rewards = [
                ("1", "Day 1 → 50 🪙", "Day 1 → 50 🪙"),
                ("2", "Day 2 → 🎁 Forest Case", "Day 2 → 🎁 Forest Case"),
                ("3", "Day 3 → 🧬 Случайная Mutation", "Day 3 → 🧬 Random Mutation"),
                ("4", "Day 4 → 🐝 Bee 🐝", "Day 4 → 🐝 Bee 🐝"),
                ("5", "Day 5 → 🌸 Rare Plant", "Day 5 → 🌸 Rare Plant"),
                ("6", "Day 6 → ⚒ Случайный Upgrade", "Day 6 → ⚒ Random Upgrade"),
                ("7", "Day 7 → 👑 Legendary Case", "Day 7 → 👑 Legendary Case"),
            ]

            for d_idx, ru_line, en_line in streak_rewards:
                d_num = int(d_idx)
                if d_num < cur_day or (d_num == cur_day and not can_claim):
                    badge = "✅"
                elif d_num == cur_day and can_claim:
                    badge = "👉 🎁"
                else:
                    badge = "🔒"
                text += f"{badge} {t(ru_line, en_line)}\n"

            text += t(
                "\n<i>Заходи каждый день! Пропуск дня возвращает на День 1. После Дня 7 серия продолжается с начала.</i>",
                "\n<i>Check in every day! Missing a day resets the streak to Day 1. It loops back after Day 7.</i>",
            )

            if can_claim:
                rows.append([(
                    t(f"🎁 Забрать: День {cur_day}", f"🎁 Claim: Day {cur_day}"),
                    "claimstreak",
                )])
            else:
                rows.append([(
                    t("✅ Сегодня получено", "✅ Claimed today"),
                    "noop",
                )])

        elif action == "referrals":
            r_info = self.referral_info(uid)
            ref_code = self.get_ref_code(uid)
            link = f"https://t.me/{current_bot}?start=ref_{ref_code}"

            m3_mark = "✅" if r_info["has_m3"] else ("🔓" if r_info["count"] >= 3 else "🔒")
            m10_mark = "✅" if r_info["has_m10"] else ("🔓" if r_info["count"] >= 10 else "🔒")

            text = t(
                "👥 <b>Реферальная система</b>\n\n"
                f"📊 Прогресс: <b>{r_info['progress_str']}</b>\n"
                f"Приглашено друзей: <b>{r_info['count']}</b>\n\n"
                "🎁 <b>Награды:</b>\n"
                "• Приглашённый друг: <b>+20 🪙</b>\n"
                "• Ты получаешь: <b>+10 🪙</b> за каждого\n\n"
                "🎯 <b>Цели:</b>\n"
                f"{m3_mark} <b>3 приглашённых</b> → 🎁 Forest Case ({min(r_info['count'], 3)}/3)\n"
                f"{m10_mark} <b>10 приглашённых</b> → 👑 Legendary Case ({min(r_info['count'], 10)}/10)\n\n"
                "🔗 <b>Твоя персональная ссылка:</b>\n"
                f"<code>{link}</code>\n\n"
                "<i>(Нажми на ссылку выше, чтобы скопировать её)</i>",
                "👥 <b>Referral System</b>\n\n"
                f"📊 Progress: <b>{r_info['progress_str']}</b>\n"
                f"Invited friends: <b>{r_info['count']}</b>\n\n"
                "🎁 <b>Rewards:</b>\n"
                "• Invited friend gets: <b>+20 🪙</b>\n"
                "• You receive: <b>+10 🪙</b> each\n\n"
                "🎯 <b>Milestones:</b>\n"
                f"{m3_mark} <b>3 friends</b> → 🎁 Forest Case ({min(r_info['count'], 3)}/3)\n"
                f"{m10_mark} <b>10 friends</b> → 👑 Legendary Case ({min(r_info['count'], 10)}/10)\n\n"
                "🔗 <b>Your personal invite link:</b>\n"
                f"<code>{link}</code>\n\n"
                "<i>(Tap the link above to copy it)</i>",
            )

            # Нативная кнопка «Поделиться ссылкой» с корректным URL-encode
            share_text = self.text(
                uid,
                "🌱 Выращивай сад со мной в Green Room! Заходи по ссылке и получи +20 🪙 на старте: ",
                "🌱 Grow a plant with me in Green Room! Use my link to claim +20 🪙 bonus: ",
            )
            share_url = (
                f"https://t.me/share/url?url={urllib.parse.quote(link, safe='')}"
                f"&text={urllib.parse.quote(share_text, safe='')}"
            )

            rows.append([(t("🚀 Поделиться ссылкой", "🚀 Share invite link"), share_url)])
            rows.append([(t("🔄 Обновить", "🔄 Refresh"), "referrals")])

        elif action in ("shop", "col"):
            owned = {r["plant_id"]: r for r in self.items(uid)}
            if action == "shop":
                ids = sorted(
                    [pid for pid in PLANTS if pid != "sprout" and available(pid)],
                    key=lambda pid: PLANTS[pid]["coins"],
                )
                page = int(parts[1]) if len(parts) > 1 else 0
                prefix = "shop"
                text = t("🛍 <b>Магазин</b>", "🛍 <b>Shop</b>")
                text += f"\n\n🪙 {u['coins']}"
            else:
                level = parts[1] if len(parts) > 1 else "all"
                if level not in ("all", "0", "1", "2", "3"):
                    raise ValueError("Invalid filter")
                ids = [
                    pid for pid in owned
                    if level == "all" or PLANTS[pid]["rarity"] == int(level)
                ]
                page = int(parts[2]) if len(parts) > 2 else 0
                prefix = f"col:{level}"
                text = t("🌿 <b>Коллекция</b>", "🌿 <b>Collection</b>")
                text += f"\n\n{len(owned)}/{len(PLANTS)}"
                rows.append([
                    ("🌿", "col:all:0"), ("⚪", "col:0:0"),
                    ("🔵", "col:1:0"), ("🟣", "col:2:0"), ("🟡", "col:3:0"),
                ])

            pages = max(1, (len(ids) + PAGE_SIZE - 1) // PAGE_SIZE)
            page = max(0, min(page, pages - 1))

            for pid in ids[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]:
                mark = "✅ " if pid in owned else ""
                if action == "shop":
                    price = PLANTS[pid]
                    label = f"{mark}{self.name(uid, pid)} · {price['coins']}🪙 / {price['stars']}⭐"
                else:
                    item = owned[pid]
                    m = MUTATIONS.get(item["mutation"], MUTATIONS["none"])
                    label = f"{m[0]} {self.name(uid, pid)} · {item['height']}"
                rows.append([(label, f"plant:{pid}")])

            arrows = []
            if page > 0:
                arrows.append(("⬅️", f"{prefix}:{page - 1}"))
            arrows.append((f"{page + 1}/{pages}", "noop"))
            if page + 1 < pages:
                arrows.append(("➡️", f"{prefix}:{page + 1}"))
            rows.append(arrows)

        elif action == "plant":
            pid = parts[1]
            if pid not in PLANTS:
                raise ValueError("Unknown plant")
            item = self.item(uid, pid)
            data = PLANTS[pid]
            text = (
                f"<b>{self.name(uid, pid)}</b>\n{self.rarity(uid, pid)}"
                f"\n\n🪙 {data['coins']} / ⭐ {data['stars']}"
                f"\nID: <code>{pid}</code>"
            )

            if item:
                m = MUTATIONS.get(item["mutation"], MUTATIONS["none"])
                text += f"\n\n📏 {item['height']} · {m[0]} {t(m[1], m[2])}"
                rows += [
                    [(t("🌿 Сделать главным", "🌿 Set as main"), f"select:{pid}")],
                    [(
                        t("➖ Убрать с грядки", "➖ Remove from bed")
                        if pid in self.beds(uid) else t("🪴 На грядку", "🪴 Add to bed"),
                        f"bed:{pid}",
                    )],
                ]
            elif available(pid):
                free = self.test(uid)
                rows += [
                    [(
                        t("👑 За монеты бесплатно", "👑 Free coin purchase")
                        if free else f"🪙 {data['coins']}",
                        f"coin:{pid}",
                    )],
                    [(
                        t("👑 За Stars бесплатно", "👑 Free Stars test")
                        if free else f"⭐ {data['stars']}",
                        f"pay:plant:{pid}",
                    )],
                ]
            else:
                text += t("\n\n📅 Доступно только в свой сезон.", "\n\n📅 Available only in its season.")

        elif action == "beds":
            ids = self.beds(uid)
            text = t("🪴 <b>Грядки</b>", "🪴 <b>Plant beds</b>")
            text += f"\n\n{len(ids)}/{1 + p['beds']}"
            for pid in ids:
                rows.append([(f"➖ {self.name(uid, pid)}", f"bed:{pid}")])
            rows.append([(t("➕ Выбрать растения", "➕ Choose plants"), "col:all:0")])

        elif action == "cases":
            text = t(
                "🎁 <b>Кейсы</b>\n\nОткрой кейс, чтобы испытать удачу и вырастить редкие плоды!",
                "🎁 <b>Cases</b>\n\nOpen a case to test your luck and unlock rare plants!",
            )
            for cid, case in CASES.items():
                rows.append([(
                    f"{case[u['lang']]} · {case['price']} ⭐", f"case:{cid}"
                )])

        elif action == "case":
            cid = parts[1]
            case = CASES[cid]
            text = f"<b>{case[u['lang']]}</b>\n\n⭐ {case['price']}"
            for pid, weight in case["drops"]:
                text += (
                    f"\n\n{self.name(uid, pid)} — <b>{weight}%</b>\n"
                    + t("Повтор: ", "Duplicate: ")
                    + f"{compensation(pid)} 🪙"
                )
            rows.append([(
                t("👑 Открыть бесплатно", "👑 Open for free")
                if self.test(uid) else f"⭐ {case['price']}",
                f"pay:case:{cid}",
            )])

        elif action == "upgrades":
            text = t("⚒ <b>Улучшения</b>\n\nЛейка: +1 см.\nУдобрение: +2 монеты.\nГрядки: +1 место.",
                     "⚒ <b>Upgrades</b>\n\nCan: +1 cm.\nFertilizer: +2 coins.\nBeds: +1 slot.")
            text += f"\n\n🪙 {u['coins']}"
            for key, (ru, en, prices) in UPGRADES.items():
                level = p[key]
                name = t(ru, en)
                text += f"\n\n{name}: {level}/{len(prices)}"
                if level < len(prices):
                    cost = "👑 FREE" if self.test(uid) else f"{prices[level]} 🪙"
                    rows.append([(f"{name} · {cost}", f"upgrade:{key}")])

        elif action == "pets":
            owned = {
                r["pet_id"]
                for r in self.all("SELECT pet_id FROM gf_pets WHERE user_id = ?", (uid,))
            }
            text = t("🐾 <b>Питомцы</b>\n\nБонус питомца начисляется при поливе.",
                     "🐾 <b>Pets</b>\n\nPet bonus is applied when watering.")
            text += f"\n\n🪙 {u['coins']}"
            for key, (emoji, ru, en, price, bonus) in PETS.items():
                mark = "✅ " if p["active_pet"] == key else ""
                cost = t("Выбрать", "Select") if key in owned else (
                    "👑 FREE" if self.test(uid) else f"{price} 🪙"
                )
                text += f"\n\n{emoji} {t(ru, en)} · +{bonus} 🪙"
                rows.append([(f"{mark}{emoji} {t(ru, en)} · {cost}", f"pet:{key}")])

        elif action == "awards":
            earned = self.eligible(uid)
            claimed = {
                r["award_id"]
                for r in self.all("SELECT award_id FROM gf_awards WHERE user_id = ?", (uid,))
            }
            text = t("🏆 <b>Достижения</b>", "🏆 <b>Achievements</b>")
            for key, ru, en, coins in AWARDS:
                mark = "✅" if key in claimed else "🎁" if earned[key] else "🔒"
                text += f"\n\n{mark} {t(ru, en)} · {coins} 🪙"
            rows.append([(t("🎁 Забрать награды", "🎁 Claim rewards"), "claim")])

        elif action == "mutations":
            text = t(
                "🧬 <b>Мутации</b>\n\nШансы при поливе:\n"
                "98% — без изменений;\n"
                "1,6% — ✨ сияющее, x2;\n"
                "0,36% — 🌈 радужное, x3;\n"
                "0,04% — 👑 золотое, x4.",
                "🧬 <b>Mutations</b>\n\nWatering chances:\n"
                "98% — none;\n"
                "1.6% — ✨ sparkling, x2;\n"
                "0.36% — 🌈 rainbow, x3;\n"
                "0.04% — 👑 golden, x4.",
            )

        elif action == "events":
            s = SEASONS[season_index()]
            w = week()
            text = f"<b>{t(s[0], s[1])}</b>\n\n{t(w[0], w[1])}"
            rows.append([(self.name(uid, s[2]), f"plant:{s[2]}")])

        elif action == "top":
            results = self.all("""
                SELECT p.user_id, SUM(p.height) AS height, COUNT(*) AS count
                FROM plants p JOIN gf_profiles g ON g.user_id = p.user_id
                WHERE g.ranked = 1
                GROUP BY p.user_id ORDER BY height DESC, p.user_id
            """)
            results = [r for r in results if r["user_id"] not in self.admins][:10]
            text = t("📊 <b>Рейтинг</b>", "📊 <b>Ranking</b>")
            for index, result in enumerate(results, 1):
                alias = hashlib.sha256(str(result["user_id"]).encode()).hexdigest()[:6]
                you = t(" · ты", " · you") if result["user_id"] == uid else ""
                text += f"\n\n{index}. #{alias}{you}\n📏 {result['height']} · 🌿 {result['count']}"

        elif action == "coop":
            m = self.member(uid)
            text = t("👥 <b>Общий сад</b>", "👥 <b>Shared garden</b>")
            if m is None:
                text += t(
                    "\n\nСоздай сад и пригласи двух друзей поливать общее дерево.",
                    "\n\nCreate a garden and invite two friends to grow a shared tree.",
                )
                rows.append([(t("🌱 Создать", "🌱 Create"), "coopcreate")])
            else:
                members = self.all(
                    "SELECT * FROM coop_members WHERE garden_id = ?",
                    (m["garden_id"],),
                )
                text += f"\n\n🌳 {m['height']} · 👥 {len(members)}/3"
                for person in members:
                    mark = "👑" if person["user_id"] == m["owner_id"] else "🌿"
                    text += f"\n\n{mark} {html.escape(person['display_name'])}\n📏 {person['contribution']}"
                rows += [
                    [(t("💧 Полить · +1 см", "💧 Water · +1 cm"), "coopwater")],
                    [(t("🔄 Обновить", "🔄 Refresh"), "coop")],
                ]
                if m["owner_id"] == uid:
                    rows.append([(t("🔗 Пригласить", "🔗 Invite"), "invite")])
                rows.append([(t("🚪 Выйти", "🚪 Leave"), "leave")])

        elif action == "leave":
            text = t("🚪 Выйти из общего сада?", "🚪 Leave the shared garden?")
            rows.append([(t("Да, выйти", "Yes, leave"), "leaveyes")])

        elif action == "admin":
            if uid not in self.admins:
                raise self.error(uid, "Нет доступа.", "Access denied.")
            text = t("👑 <b>Тестовый режим администратора</b>", "👑 <b>Admin test mode</b>")
            text += f"\n\n{'🟢 ON' if self.test(uid) else '⚪ OFF'}"
            rows.append([(
                t("Выключить", "Disable") if self.test(uid) else t("Включить", "Enable"),
                "adminoff" if self.test(uid) else "adminon",
            )])

        elif action == "language":
            text = "Выбери язык / Choose your language"
            rows = [[("🇷🇺 Русский", "lang:ru"), ("🇬🇧 English", "lang:en")]]

        elif action == "trades":
            text = t(
                "🤝 <b>Обмен</b>\n\n<code>/trade ID_игрока твой_plant_id его_plant_id</code>",
                "🤝 <b>Trading</b>\n\n<code>/trade player_ID your_plant_id their_plant_id</code>",
            )
            offers = self.all(
                """
                SELECT * FROM trades_v2 WHERE (sender = ? OR target = ?)
                AND status = 'pending' AND expires > ?
                ORDER BY expires DESC LIMIT 12
                """,
                (uid, uid, int(time.time())),
            )
            for offer in offers:
                label = f"{self.name(uid, offer['offered'])} ↔ {self.name(uid, offer['requested'])}"
                rows.append([(label, f"offer:{offer['id']}")])

        elif action == "offer":
            offer = self.one("SELECT * FROM trades_v2 WHERE id = ?", (parts[1],))
            if offer is None or uid not in (offer["sender"], offer["target"]):
                raise self.error(uid, "Предложение недоступно.", "Offer unavailable.")
            snap = json.loads(offer["snapshot"])
            a, b = snap["a"], snap["b"]
            ma = MUTATIONS.get(a["mutation"], MUTATIONS["none"])
            mb = MUTATIONS.get(b["mutation"], MUTATIONS["none"])
            text = (
                t("🤝 <b>Предложение обмена</b>", "🤝 <b>Trade offer</b>")
                + f"\n\nОтправитель: {self.name(uid, offer['offered'])} 📏 {a['height']} · {t(ma[1], ma[2])}"
                + f"\nПолучатель: {self.name(uid, offer['requested'])} 📏 {b['height']} · {t(mb[1], mb[2])}"
                + f"\n\nКомиссия: {offer['fee']} 🪙"
            )
            if offer["status"] == "pending" and offer["expires"] > time.time():
                if uid == offer["target"]:
                    rows.append([(t("✅ Принять", "✅ Accept"), f"accept:{offer['id']}")])
                rows.append([(t("❌ Отменить", "❌ Cancel"), f"canceltrade:{offer['id']}")])

        elif action == "invoices":
            text = t("🧾 <b>Счета</b>", "🧾 <b>Invoices</b>")
            orders = self.all(
                """
                SELECT * FROM orders WHERE user_id = ? AND paid = 0
                AND cancelled = 0 AND (checked = 1 OR created_at >= ?)
                ORDER BY created_at DESC LIMIT 10
                """,
                (uid, int(time.time()) - INVOICE_TTL),
            )
            for order in orders:
                if json.loads(order["terms"] or "{}").get("test"):
                    continue
                text += f"\n\n#{order['payload'][:8]} · {order['amount']} ⭐"
                if not order["checked"]:
                    rows.append([(
                        t("❌ Отменить ", "❌ Cancel ") + order["payload"][:8],
                        f"cancelorder:{order['payload']}",
                    )])

        else:
            return self.screen(uid, "home", bot_name=current_bot)

        return text, rows + self.nav(uid)

    def result_screen(self, uid, result):
        t = lambda ru, en: self.text(uid, ru, en)
        name = self.name(uid, result["pid"])

        if result["kind"] == "growth":
            text = f"<b>{name}</b>\n\n" + t("🌱 Рост +1 см", "🌱 Growth +1 cm")
        else:
            text = t("🎉 <b>Награда получена!</b>", "🎉 <b>Reward received!</b>")
            text += f"\n\n<b>{name}</b>\n{self.rarity(uid, result['pid'])}"
            if result["duplicate"]:
                text += t(
                    f"\n\nПовтор → {result['coins']} монет 🪙",
                    f"\n\nDuplicate → {result['coins']} coins 🪙",
                )
            else:
                text += t("\n\nДобавлено в коллекцию.", "\n\nAdded to your collection.")

        text += (
            t("\n\n👑 Бесплатный тест", "\n\n👑 Free test")
            if result["free"]
            else t("\n\n⭐ Оплата подтверждена", "\n\n⭐ Payment confirmed")
        )
        return text, [
            [(t("🌿 Коллекция", "🌿 Collection"), "col:all:0")],
            [(t("🏡 В сад", "🏡 Garden"), "home")],
        ]

    # -------------------- BUTTON ACTIONS --------------------

    def click(self, uid, data, display_name):
        parts = data.split(":")
        action = parts[0]
        route, notice, notify = data, None, None

        if action == "water":
            notice, route = self.water(uid), "home"

        elif action == "streak":
            route = "streak"

        elif action == "referrals":
            route = "referrals"

        elif action == "claimstreak":
            day_num, reward_text = self.claim_streak(uid)
            notice = f"🎁 Day {day_num}: {reward_text}"
            route = "streak"

        elif action == "select":
            pid = parts[1]
            if not self.owns(uid, pid) or pid not in PLANTS:
                raise ValueError("Plant unavailable")
            with self.db:
                self.db.execute(
                    "UPDATE users SET active_plant = ? WHERE id = ?", (pid, uid)
                )
            route = "home"

        elif action == "bed":
            pid = parts[1]
            if not self.owns(uid, pid) or pid not in PLANTS:
                raise ValueError("Plant unavailable")
            with self.db:
                current = self.beds(uid)
                if pid in current:
                    self.db.execute(
                        "DELETE FROM gf_beds WHERE user_id = ? AND plant_id = ?",
                        (uid, pid),
                    )
                else:
                    if len(current) >= 1 + self.profile(uid)["beds"]:
                        raise self.error(uid, "Все грядки заняты.", "All beds are occupied.")
                    self.db.execute(
                        "INSERT INTO gf_beds (user_id, plant_id) VALUES (?, ?)",
                        (uid, pid),
                    )
            route = "beds"

        elif action == "coin":
            pid = parts[1]
            if pid not in PLANTS or pid == "sprout" or not available(pid):
                raise self.error(uid, "Растение сейчас недоступно.", "Plant currently unavailable.")
            with self.db:
                if self.owns(uid, pid):
                    raise self.error(uid, "Уже есть в коллекции.", "Already owned.")
                if not self.test(uid):
                    self.spend(uid, PLANTS[pid]["coins"])
                self.db.execute(
                    "INSERT INTO plants (user_id, plant_id) VALUES (?, ?)", (uid, pid)
                )
            notice = self.text(uid, "🌱 Растение куплено.", "🌱 Plant purchased.")
            route = f"plant:{pid}"

        elif action == "upgrade":
            key = parts[1]
            if key not in UPGRADES:
                raise ValueError("Invalid upgrade")
            with self.db:
                level = self.profile(uid)[key]
                prices = UPGRADES[key][2]
                if level >= len(prices):
                    raise self.error(uid, "Максимальный уровень.", "Maximum level.")
                if not self.test(uid):
                    self.spend(uid, prices[level])
                self.db.execute(
                    f"UPDATE gf_profiles SET {key} = {key} + 1 WHERE user_id = ?", (uid,)
                )
            route = "upgrades"

        elif action == "pet":
            key = parts[1]
            if key not in PETS:
                raise ValueError("Invalid pet")
            with self.db:
                owned = self.one(
                    "SELECT 1 FROM gf_pets WHERE user_id = ? AND pet_id = ?", (uid, key)
                )
                if not owned:
                    if not self.test(uid):
                        self.spend(uid, PETS[key][3])
                    self.db.execute(
                        "INSERT INTO gf_pets (user_id, pet_id) VALUES (?, ?)", (uid, key)
                    )
                self.db.execute(
                    "UPDATE gf_profiles SET active_pet = ? WHERE user_id = ?", (key, uid)
                )
            route = "pets"

        elif action == "claim":
            notice, route = f"🪙 +{self.claim(uid)}", "awards"

        elif action == "lang":
            if parts[1] not in ("ru", "en"):
                raise ValueError("Invalid language")
            with self.db:
                self.db.execute("UPDATE users SET lang = ? WHERE id = ?", (parts[1], uid))
            route = "home"

        elif action in ("adminon", "adminoff"):
            if uid not in self.admins:
                raise self.error(uid, "Нет доступа.", "Access denied.")
            with self.db:
                self.db.execute(
                    "UPDATE users SET admin_test = ? WHERE id = ?",
                    (int(action == "adminon"), uid),
                )
                self.db.execute(
                    "UPDATE gf_profiles SET ranked = 0 WHERE user_id = ?", (uid,)
                )
            route = "admin"

        elif action == "coopcreate":
            self.create_coop(uid, display_name)
            route = "coop"

        elif action == "coopwater":
            self.water_coop(uid)
            notice, route = "🌳 +1", "coop"

        elif action == "leaveyes":
            self.leave_coop(uid)
            route = "coop"

        elif action == "accept":
            notify = self.accept_trade(uid, parts[1])
            notice = self.text(uid, "🤝 Обмен завершён.", "🤝 Trade completed.")
            route = "trades"

        elif action == "canceltrade":
            with self.db:
                self.db.execute(
                    """
                    UPDATE trades_v2 SET status = 'cancelled'
                    WHERE id = ? AND status = 'pending'
                      AND (sender = ? OR target = ?)
                    """,
                    (parts[1], uid, uid),
                )
            route = "trades"

        elif action == "cancelorder":
            self.cancel_order(uid, parts[1])
            route = "invoices"

        return self.screen(uid, route), notice, notify