import hashlib
import json
import secrets
import sqlite3
import time
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
        "ru": "🎁 Лесной кейс", "en": "🎁 Forest Case", "price": 400,
        "drops": [
            ("sprout", 20), ("cactus", 20), ("berry", 18),
            ("strawberry", 15), ("carrot", 12), ("tulip", 7),
            ("daisy", 5), ("lavender", 2), ("rose", 1),
        ],
    },
    "flower": {
        "ru": "💎 Цветочный кейс", "en": "💎 Flower Case", "price": 800,
        "drops": [
            ("cactus", 12), ("berry", 12), ("tulip", 12),
            ("daisy", 10), ("lavender", 12), ("hibiscus", 10),
            ("lily", 9), ("rose", 8), ("sunflower", 6),
            ("dahlia", 4), ("lotus", 3), ("moonflower", 1), ("cherry", 1),
        ],
    },
    "royal": {
        "ru": "👑 Королевский кейс", "en": "👑 Royal Case", "price": 1500,
        "drops": [
            ("tulip", 8), ("daisy", 8), ("lavender", 8), ("hibiscus", 10),
            ("rose", 12), ("lily", 10), ("sunflower", 9), ("dahlia", 8),
            ("lotus", 7), ("moonflower", 5), ("mango", 4),
            ("pineapple", 3), ("dragonfruit", 2), ("cherry", 3),
            ("palm", 2), ("giant_tree", 1),
        ],
    },
    "mythic": {
        "ru": "🌌 Мифический кейс", "en": "🌌 Mythic Case", "price": 3000,
        "drops": [
            ("lavender", 7), ("hibiscus", 7), ("rose", 8), ("sunflower", 8),
            ("dahlia", 8), ("lotus", 8), ("moonflower", 7), ("mango", 7),
            ("pineapple", 6), ("watermelon", 5), ("dragonfruit", 5),
            ("starfruit", 4), ("passionfruit", 4), ("avocado", 4),
            ("glowshroom", 3), ("bamboo", 3), ("cherry", 3),
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
            admin_test INTEGER NOT NULL DEFAULT 1
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
        """)

        with self.db:
            self.column("users", "growth_streak", "INTEGER NOT NULL DEFAULT 0")
            self.column("users", "admin_test", "INTEGER NOT NULL DEFAULT 1")
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
        return self.one(
            "SELECT * FROM gf_profiles WHERE user_id = ?", (uid,)
        )

    def text(self, uid, ru, en):
        return ru if self.user(uid)["lang"] == "ru" else en

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

    def ensure(self, tg_user):
        uid = tg_user.id
        language = "ru" if (tg_user.language_code or "").startswith("ru") else "en"

        with self.db:
            self.db.execute(
                "INSERT OR IGNORE INTO users (id, lang) VALUES (?, ?)",
                (uid, language),
            )
            self.db.execute(
                "INSERT OR IGNORE INTO plants (user_id, plant_id) VALUES (?, 'sprout')",
                (uid,),
            )

            fresh = self.db.execute(
                "INSERT OR IGNORE INTO gf_profiles (user_id) VALUES (?)",
                (uid,),
            ).rowcount

            current = self.user(uid)
            if current["active_plant"] not in PLANTS or not self.owns(
                uid, current["active_plant"]
            ):
                self.db.execute(
                    "UPDATE users SET active_plant = 'sprout' WHERE id = ?",
                    (uid,),
                )

            if fresh:
                self.db.execute(
                    "INSERT OR IGNORE INTO gf_beds (user_id, plant_id) VALUES (?, 'sprout')",
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

    # -------------------- PAYMENT ORDERS --------------------

    def order(self, payload):
        return self.one(
            "SELECT * FROM orders WHERE payload = ?", (payload,)
        )

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
                    f"Цена {order['amount']} Stars. Если при обработке оплаты "
                    f"уже есть, получишь {order['duplicate_coins']} игровых монет.",
                    f"{self.name(uid, pid)}: starts at 0 cm, permanent unlock. "
                    f"Price: {order['amount']} Stars. If already owned when processed, "
                    f"receive {order['duplicate_coins']} in-game coins.",
                ),
            )

        return (
            CASES[pid][self.user(uid)["lang"]],
            self.text(
                uid,
                f"Одно случайное растение за {order['amount']} Stars. "
                "Шансы и компенсации показаны в карточке. "
                "Награда может быть значительно дешевле кейса. "
                "Нет обмена наград на деньги или Stars.",
                f"One random plant for {order['amount']} Stars. "
                "Odds and duplicate compensation are shown on the case card. "
                "The reward may cost much less than the case. No cash-out.",
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
                # После разрешения оплаты отменить счёт кнопкой нельзя.
                self.db.execute(
                    "UPDATE orders SET checked = 1 WHERE payload = ?",
                    (payload,),
                )
            return valid

    def deliver(self, uid, payload, payment=None):
        """
        Выдача и запись результата выполняются в одной транзакции.
        При повторном событии оплаты возвращается сохранённый результат.
        """
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

            # Исключение откатывает оба списания.
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

    def screen(self, uid, route="home"):
        import html

        t = lambda ru, en: self.text(uid, ru, en)
        u, p = self.user(uid), self.profile(uid)
        parts = route.split(":")
        action = parts[0]
        rows = []
        text = ""

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

            text = (
                "🌱 <b>GREEN ROOM</b>\n\n"
                f"<b>{self.name(uid, pid)}</b>\n"
                f"{self.rarity(uid, pid)}\n"
                f"{m[0]} {t(m[1], m[2])}\n\n"
                f"📏 {height} {t('см', 'cm')}\n{progress}\n\n"
                f"🪙 {u['coins']} · 🔥 {self.streak(uid)} {t('дн.', 'days')}"
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
                "🧭 <b>Развитие сада</b>\n\nМонеты за полив начисляются один раз в день на весь сад.",
                "🧭 <b>Garden progress</b>\n\nWatering coins are awarded once per day for the entire garden.",
            )
            rows = [
                [(t("🏆 Достижения", "🏆 Achievements"), "awards"), (t("📊 Рейтинг", "📊 Ranking"), "top")],
                [(t("⚒ Улучшения", "⚒ Upgrades"), "upgrades"), (t("🐾 Питомцы", "🐾 Pets"), "pets")],
                [(t("🧬 Мутации", "🧬 Mutations"), "mutations"), (t("📅 События", "📅 Events"), "events")],
                [(t("🤝 Обмен", "🤝 Trading"), "trades"), (t("🧾 Счета", "🧾 Invoices"), "invoices")],
            ]

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
            text += t(
                "\n\nПоливаются все выбранные растения. Смена грядок не сбрасывает дневной лимит.",
                "\n\nAll selected plants are watered together. Changing beds does not reset the daily limit.",
            )
            for pid in ids:
                rows.append([(f"➖ {self.name(uid, pid)}", f"bed:{pid}")])
            rows.append([(t("➕ Выбрать растения", "➕ Choose plants"), "col:all:0")])

        elif action == "cases":
            text = t(
                "🎁 <b>Кейсы</b>\n\nПеред покупкой открой карточку: там все награды, шансы и компенсации.",
                "🎁 <b>Cases</b>\n\nOpen a case card before purchasing to see rewards, odds and duplicate compensation.",
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
            text += t(
                "\n\nОдно растение, рост 0 см. Повтор заменяется указанными монетами. "
                "Росток уже есть у всех. Мутация при покупке не выдаётся.\n\n"
                "⚠️ Награда может быть значительно дешевле кейса. Сравни магазин. "
                "Награды нельзя обменять на деньги или Stars. "
                "Шансы не меняются от числа покупок.",
                "\n\nOne plant starting at 0 cm. Duplicates give the listed coins. "
                "Everyone already owns the sprout. Purchases do not grant mutations.\n\n"
                "⚠️ The reward may cost much less than the case. Compare shop prices. "
                "No cash-out or exchange for Stars. Odds do not change with purchases.",
            )
            rows.append([(
                t("👑 Открыть бесплатно", "👑 Open for free")
                if self.test(uid) else f"⭐ {case['price']}",
                f"pay:case:{cid}",
            )])

        elif action == "upgrades":
            text = t(
                "⚒ <b>Улучшения</b>\n\n"
                "Лейка: +1 базовый см за уровень.\n"
                "Удобрение: +2 монеты в день за уровень.\n"
                "Грядки: +1 место, максимум 3.",
                "⚒ <b>Upgrades</b>\n\n"
                "Can: +1 base cm per level.\n"
                "Fertilizer: +2 daily coins per level.\n"
                "Beds: +1 slot, maximum 3.",
            )
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
            text = t(
                "🐾 <b>Питомцы</b>\n\nБонус выбранного питомца начисляется один раз в день при поливе. "
                "Купленные питомцы сохраняются.",
                "🐾 <b>Pets</b>\n\nThe selected pet gives its bonus once daily when watering. "
                "Purchased pets stay in your collection.",
            )
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
                "🧬 <b>Мутации</b>\n\nПри поливе растения без мутации:\n"
                "98% — без изменений;\n"
                "1,6% — ✨ сияющее, x2;\n"
                "0,36% — 🌈 радужное, x3;\n"
                "0,04% — 👑 золотое, x4.\n\n"
                "Множитель действует на базовый рост с лейкой. "
                "Мутация постоянна. Купленный +1 см не умножается.",
                "🧬 <b>Mutations</b>\n\nWhen watering an unmutated plant:\n"
                "98% — no change;\n"
                "1.6% — ✨ sparkling, x2;\n"
                "0.36% — 🌈 rainbow, x3;\n"
                "0.04% — 👑 golden, x4.\n\n"
                "The multiplier affects base growth including the can upgrade. "
                "Mutations are permanent. Purchased +1 cm is not multiplied.",
            )

        elif action == "events":
            s = SEASONS[season_index()]
            w = week()
            text = f"<b>{t(s[0], s[1])}</b>\n\n{t(w[0], w[1])}"
            text += t(
                "\n\nВесной: +1 см каждому растению.\nОсенью: +2 монеты за полив.\n"
                "Зимой и летом числового сезонного бонуса нет.\n\n"
                "Событие на весь полив:\n80% — ничего;\n10% — дождь, +1 см каждому;\n"
                "7% — +5 монет;\n3% — +10 монет.\n\n"
                "Сезоны по месяцам UTC: зима — декабрь–февраль, весна — март–май, "
                "лето — июнь–август, осень — сентябрь–ноябрь.\n"
                "Сезонные покупки сохраняются навсегда.",
                "\n\nSpring: +1 cm per plant.\nAutumn: +2 watering coins.\n"
                "Winter and summer have no numeric season bonus.\n\n"
                "One event per watering:\n80% — nothing;\n10% — rain, +1 cm each;\n"
                "7% — +5 coins;\n3% — +10 coins.\n\n"
                "UTC seasons: winter Dec–Feb, spring Mar–May, summer Jun–Aug, autumn Sep–Nov.\n"
                "Seasonal purchases remain permanently.",
            )
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
            text += t(
                "\n\nПо суммарному росту. Платный рост учитывается. "
                "Администраторы и отмеченные тестовые аккаунты исключены.",
                "\n\nBy total height. Paid growth counts. "
                "Administrators and flagged test accounts are excluded.",
            )

        elif action == "coop":
            m = self.member(uid)
            text = t("👥 <b>Общий сад</b>", "👥 <b>Shared garden</b>")
            if m is None:
                text += t(
                    "\n\nСоздай сад и пригласи двух друзей. Каждый поливает общее дерево раз в день.",
                    "\n\nCreate a garden and invite two friends. Each member waters the shared tree once daily.",
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
                    text += (
                        f"\n\n{mark} {html.escape(person['display_name'])}"
                        f"\n📏 {person['contribution']}"
                    )
                rows += [
                    [(t("💧 Полить · +1 см", "💧 Water · +1 cm"), "coopwater")],
                    [(t("🔄 Обновить", "🔄 Refresh"), "coop")],
                ]
                if m["owner_id"] == uid:
                    rows.append([(t("🔗 Пригласить", "🔗 Invite"), "invite")])
                rows.append([(t("🚪 Выйти", "🚪 Leave"), "leave")])

        elif action == "leave":
            text = t(
                "🚪 Выйти из общего сада?\n\nДерево остаётся у участников. "
                "Если ты последний, общий сад удалится. Личный сад не изменится.",
                "🚪 Leave the shared garden?\n\nThe tree stays with other members. "
                "If you are the last member, the shared garden is deleted. Your personal garden is unaffected.",
            )
            rows.append([(t("Да, выйти", "Yes, leave"), "leaveyes")])

        elif action == "admin":
            if uid not in self.admins:
                raise self.error(uid, "Нет доступа.", "Access denied.")
            text = t(
                "👑 <b>Тестовый режим</b>\n\nВключённый режим делает покупки бесплатными "
                "и снимает лимит полива. Прогресс сохраняется.\n\n"
                "Тестовые аккаунты не торгуют и не участвуют в рейтинге.\n"
                "После выключения покупки Stars становятся платными.",
                "👑 <b>Test mode</b>\n\nEnabled mode makes purchases free "
                "and removes watering limits. Progress is saved.\n\n"
                "Test accounts cannot trade or enter rankings.\n"
                "Disabling it makes Stars purchases paid.",
            )
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
                "🤝 <b>Обмен</b>\n\n"
                "<code>/trade ID_игрока мой_plant_id его_plant_id</code>\n\n"
                "Пример:\n<code>/trade 123456789 cactus tulip</code>\n\n"
                "ID растения указан в карточке. Свой ID: /id.\n"
                "Комиссия — 20 монет с каждого. До 3 сделок в день.\n"
                "Команда подтверждает твою сторону, получатель подтверждает отдельно.\n"
                "Рост и мутация передаются. Деньги и Stars не обмениваются.\n"
                "Изменение растения до принятия требует нового предложения.",
                "🤝 <b>Trading</b>\n\n"
                "<code>/trade player_ID my_plant_id their_plant_id</code>\n\n"
                "Example:\n<code>/trade 123456789 cactus tulip</code>\n\n"
                "Plant IDs are on their cards. Your ID: /id.\n"
                "Fee: 20 coins each. Up to 3 trades daily.\n"
                "The command confirms your side; the recipient confirms separately.\n"
                "Height and mutation transfer. No money or Stars are exchanged.\n"
                "Changing a plant before acceptance requires a new offer.",
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
                + "\n\n" + t("Отправитель отдаёт:", "Sender gives:")
                + f"\n{self.name(uid, offer['offered'])}\n📏 {a['height']} · {t(ma[1], ma[2])}"
                + "\n\n" + t("Получатель отдаёт:", "Recipient gives:")
                + f"\n{self.name(uid, offer['requested'])}\n📏 {b['height']} · {t(mb[1], mb[2])}"
                + "\n\n" + t("Комиссия с каждого: ", "Fee per person: ")
                + f"{offer['fee']} 🪙"
            )
            expires = datetime.fromtimestamp(offer["expires"], timezone.utc)
            text += "\nUTC: " + expires.strftime("%Y-%m-%d %H:%M")
            if offer["status"] == "pending" and offer["expires"] > time.time():
                if uid == offer["target"]:
                    rows.append([(t("✅ Принять", "✅ Accept"), f"accept:{offer['id']}")])
                rows.append([(t("❌ Отменить / отклонить", "❌ Cancel / reject"), f"canceltrade:{offer['id']}")])
            else:
                text += t("\n\nПредложение закрыто.", "\n\nOffer closed.")

        elif action == "invoices":
            text = t(
                "🧾 <b>Счета</b>\n\nНеиспользованный счёт действует 15 минут. "
                "Можно отменить счёт, если платёж ещё не начат. "
                "Зависший начатый платёж: /paysupport.",
                "🧾 <b>Invoices</b>\n\nUnused invoices expire after 15 minutes. "
                "You can cancel before checkout starts. "
                "For a stuck checkout: /paysupport.",
            )
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
            return self.screen(uid, "home")

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
        """
        Возвращает: экран, короткое уведомление, ID для уведомления.
        Платёжные кнопки обрабатываются в bot.py.
        """
        parts = data.split(":")
        action = parts[0]
        route, notice, notify = data, None, None

        if action == "water":
            notice, route = self.water(uid), "home"

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