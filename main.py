import discord
from discord import AllowedMentions, app_commands
from discord.ext import commands
import json
import shutil
import re
import os
import random
from dotenv import load_dotenv
import threading
import socketserver
from http.server import BaseHTTPRequestHandler
import time

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Data storage files (configurable directory for persistence)
def resolve_data_dir() -> str:
    # 1) Explicit env var wins
    env_dir = os.getenv('DATA_DIR')
    if env_dir:
        return env_dir
    # 2) If Railway volume is mounted at /data, use it automatically
    try:
        if os.path.isdir('/data'):
            return '/data'
    except Exception:
        pass
    # 3) Fallback to current directory
    return '.'

DATA_DIR = resolve_data_dir()
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception as _e:
    print(f"⚠️ Could not ensure data directory {DATA_DIR}: {_e}")
print(f"📦 Using data directory: {DATA_DIR}")

COMMANDS_FILE = os.path.join(DATA_DIR, 'custom_commands.json')
LINKS_FILE = os.path.join(DATA_DIR, 'payment_links.json')
ENJOY_FILE = os.path.join(DATA_DIR, 'enjoy_messages.json')
BARRED_USERS_FILE = os.path.join(DATA_DIR, 'barred_users.json')
ACCOUNTS_FILE = os.path.join(DATA_DIR, 'accounts.json')
WELCOME_FILE = os.path.join(DATA_DIR, 'welcome_messages.json')
DEFAULT_BARRED_USERS: tuple[str, ...] = (
    "1405894979095892108",
)

# Built-in default /enjoy messages (50), using (user) placeholder and #vouch/#casino
DEFAULT_ENJOY_MESSAGES = [
    "✅ Thanks for ordering, (user)! Enjoy your meal 🍔 Don’t forget to vouch in #vouch for points—redeem for free food or gamble in #casino 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🚀 Order’s in, (user)! Feast mode ON 😋 Drop a vouch in #vouch to stack points → free orders or casino wins 🎡 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍽️ Dig in, (user)! Be sure to post in #vouch for reward points 🎟️ Redeem for free eats or take your shot in #casino 🃏 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🎊 Appreciate you, (user)! Enjoy your GUHDeats 🍕 Earn points by vouching in #vouch then try your luck in #casino 🎲 STILL GUHHD with GUHDeats 💪",
    "✨ Enjoy every bite, (user) 😍 A quick vouch in #vouch = points toward free orders & casino plays 💎 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🥳 Thanks for riding with us, (user)! After your meal, vouch in #vouch for points → free meals or big wins in #casino 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍔🍟 Chow time, (user)! Earn points by dropping a vouch in #vouch → redeem or gamble in #casino 🔥 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "⚡ Enjoy your GUHDeats drop, (user)! Share a vouch in #vouch for points & hit #casino to spin 🎲 STILL GUHHD with GUHDeats 💪",
    "💯 Appreciate your order, (user)! Every vouch in #vouch = points 🪙 Free food or double down in #casino ♠️ Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍴 Cravings crushed, (user)! Don’t forget to vouch in #vouch → stack points, redeem, or gamble 💫 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🥢 Meal delivered 🥡, (user)! Vouch in #vouch for points → use for free eats or casino fun 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🏆 You’re a winner already, (user)! Thanks for ordering 💎 Drop a vouch in #vouch to claim points & play in #casino 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍕🍔 Hot & ready, (user)! Enjoy 😋 Then vouch in #vouch → free orders or a casino jackpot 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🔥 Order locked in, (user)! Enjoy your food and vouch in #vouch for points → gamble them in #casino 🎡 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🎶 Dinner vibes active 😎, (user)! Drop a vouch in #vouch → earn points & spin the games in #casino 🃏 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "💥 Thanks for rolling with GUHDeats, (user)! Enjoy your food & claim points in #vouch → jackpot awaits in #casino 🎰 STILL GUHHD with GUHDeats 💪",
    "🥤 Sip back, relax, (user) 🍔 Don’t forget to vouch in #vouch for points → redeem or risk in #casino 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🌟 Enjoy your GUHDeats, (user)! Collect points in #vouch → freebies OR roulette, blackjack, slots in #casino 💎 STILL GUHHD with GUHDeats 💪",
    "🕹️ Level up, (user)! Food’s here 🍕 Bonus points waiting in #vouch → free orders or casino action 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍜 Slurp it up, (user)! Post your vouch in #vouch to stack points → gamble them in #casino 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🚨 GUHDeats complete ✅, (user)! Enjoy & vouch in #vouch → rewards or casino wins 🎰 STILL GUHHD with GUHDeats 💪",
    "🍴 Bon appétit, (user) 😍 Don’t miss your vouch in #vouch → points = free orders or casino shots 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🥂 Cheers to you, (user)! Thanks for ordering 🥳 Vouch in #vouch to stack points & gamble in #casino 🃏 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🤑 Rack up, (user)! Enjoy your food & vouch in #vouch → points for free meals or casino play 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🎯 Mission complete, (user)! Food delivered ✅ Vouch in #vouch for points → spend or spin 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🧃 Refresh & feast 😋, (user)! Drop a vouch in #vouch → free orders or casino jackpots 🎡 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🛎️ Your food’s in, (user)! Earn points by vouching in #vouch → free meals or casino fun 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍔💨 Fast food, faster rewards, (user)! Don’t forget #vouch → free eats or casino thrills 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🌈 Taste the win, (user)! Vouch in #vouch for points → redeem or risk them in #casino 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🎁 Big thanks, (user)! Enjoy your GUHDeats & vouch in #vouch → free meals or casino jackpots 💎 STILL GUHHD with GUHDeats 💪",
    "💌 Thanks a bunch, (user)! Enjoy your order 💫 Don’t forget: vouch in #vouch to stack points & roll the dice in #casino 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🥳 Food secured, (user)! Feast away 😋 Vouch in #vouch for reward points → gamble or redeem 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🔑 Unlock rewards, (user)! Enjoy your food & claim points in #vouch → spend or spin them in #casino 🎡 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍟 Fries hot, vibes hotter, (user)! Vouch in #vouch for points → free eats or jackpot chances 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🥤 Sip + snack = win, (user)! Be sure to vouch in #vouch → collect points, redeem, or risk 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🏅 You’re VIP, (user)! Thanks for ordering 🎉 Earn points by vouching in #vouch → play them in #casino 🃏 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍴 Feast mode engaged, (user)! Vouch in #vouch for points toward free meals or casino fun 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🔔 Ding ding, order’s here, (user)! Enjoy + vouch in #vouch → stack rewards & gamble 🎡 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "✌️ Big ups, (user)! Enjoy your GUHDeats & earn by vouching in #vouch → points = food or casino shots 🎲 STILL GUHHD with GUHDeats 💪",
    "🎨 Flavor unlocked, (user)! Post your vouch in #vouch → redeem or risk it in #casino 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🧨 Boom! Order’s dropped, (user)! Enjoy & vouch in #vouch → rack points, play in #casino 🔥 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍔 Hungry no more, (user)! Thanks for choosing GUHDeats 🙌 Don’t forget to vouch in #vouch → stack rewards 🎲 STILL GUHHD with GUHDeats 💪",
    "🌟 Meal vibes strong, (user)! Drop a vouch in #vouch → points for free orders or casino jackpots 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🥢 Fresh eats delivered, (user)! Vouch in #vouch → free meals or risk it all in #casino 🎡 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🍩 Sweet win, (user)! Enjoy & don’t miss your vouch in #vouch → gamble points in #casino 🃏 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🚦 Green light to eat, (user)! Chow down 😋 Vouch in #vouch for points → freebies or casino 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "📦 Delivery complete, (user)! Enjoy + earn points with a quick vouch in #vouch → redeem or spin 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "💫 Thanks for choosing us, (user)! Drop a vouch in #vouch to unlock free orders or casino games 🎡 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🎉 Party plate unlocked, (user)! Enjoy & vouch in #vouch → rewards or gamble in #casino 🎰 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪",
    "🔥 Feast up, (user)! Your meal’s ready—don’t forget to vouch in #vouch → stack points & try your luck 🎲 Thanks for choosing GUHDeats! STILL GUHHD with GUHDeats 💪"
]

# Fresh rotating welcome lines for new members.
DEFAULT_WELCOME_MESSAGES = [
    "🎉 Welcome to GUHD EATS, (user)! We do 50% off Uber Eats—check out the casino channels and hit /daily (chances go up with orders!).",
    "🍔 Glad you joined GUHD EATS, (user)! Enjoy 50% off Uber Eats, explore the casino, and grab /daily every day—your odds rise with each order.",
    "💫 Big welcome, (user)! Dive into 50% off Uber Eats deals, visit the casino rooms, and be sure to run /daily (better odds when you order).",
    "🎰 Hey (user), welcome aboard! Snag 50% off Uber Eats, roll into the casino, and tap /daily—the chances keep climbing with orders.",
    "🚀 Stoked to have you, (user)! Remember: 50% off Uber Eats, casino fun waiting, and /daily gets sweeter as you place orders."
]


TIME_OF_DAY_SNIPPETS: dict[str, list[str]] = {
    "morning": [
        "☀️ Early bird energy! Pair your first /daily spin with a breakfast steal.",
        "🌞 Sunrise special—line up an order now and watch those /daily odds grow." 
    ],
    "afternoon": [
        "🌤️ Midday munchies? Queue a lunch order for that extra /daily boost.",
        "🍽️ Perfect time for a double-dip: place an order and smash /daily!"
    ],
    "evening": [
        "🌙 Prime dinner time—keep the casino buzzing after you run /daily.",
        "🍝 Night crowd's rolling—grab your 50% off bite and cash in on /daily." 
    ],
    "overnight": [
        "🌌 Late-night cravings hit different. Tap /daily and ride the lucky streak.",
        "🦉 Night owl status unlocked—orders now supercharge your /daily chances." 
    ],
}


MEMBER_COUNT_SNIPPETS = [
    "You're member #{count} sliding in—let's make it legendary!",
    "Lucky #{count}! Ping a provider if you want help snagging that first order.",
    "Crew count just hit #{count}! Drop into the casino and say hi."
]


WELCOME_ROLLOUT_SNIPPETS = [
    "🎟️ Need a plug? Pop a ticket anytime—mods are on standby.",
    "🎲 Feeling bold? Casino jackpots hit different after a fresh order.",
    "📈 Orders = better /daily luck. Stack them and flex in #vouch.",
    "🛎️ Questions about 50% off? Staff are one ping away.",
    "💬 Jump into chat and let folks know what you're craving tonight!"
]


def _time_slot_from_hour(hour: int) -> str:
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 23:
        return "evening"
    return "overnight"


def _needs_welcome_update(data: dict) -> bool:
    try:
        messages = data.get("messages", [])
        if not messages:
            return True
        required_phrases = ("50% off", "uber eats", "/daily", "casino")
        for message in messages:
            normalized = message.lower()
            if not all(phrase in normalized for phrase in required_phrases):
                return True
        return False
    except Exception:
        return True

def _needs_enjoy_update(data: dict) -> bool:
    try:
        msgs = data.get("messages", [])
        if len(msgs) != 50:
            return True
        # Require that all messages contain (user) and at least one message contains #casino
        if not all("(user)" in m for m in msgs):
            return True
        if not any("#casino" in m for m in msgs):
            return True
        return False
    except Exception:
        return True

# One-time migration: copy legacy files from project root into DATA_DIR if present
def migrate_legacy_file(legacy_path: str, new_path: str) -> None:
    try:
        if os.path.exists(legacy_path) and not os.path.exists(new_path):
            shutil.copy2(legacy_path, new_path)
            print(f"✅ Migrated {legacy_path} -> {new_path}")
    except Exception as e:
        print(f"⚠️ Migration failed for {legacy_path}: {e}")

migrate_legacy_file('custom_commands.json', COMMANDS_FILE)
migrate_legacy_file('payment_links.json', LINKS_FILE)
migrate_legacy_file('enjoy_messages.json', ENJOY_FILE)

# Simple HTTP health server used by deployment platforms
class _HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple handler that always returns HTTP 200 with a plain text body."""

    # Disable default logging to stderr to avoid noisy output on health probes
    def log_message(self, format, *args):
        return

    def _write_ok(self):
        body = b"OK"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        # For HEAD requests we do not write a body
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self):  # noqa: N802 (discord bot project - keep discord naming conventions)
        self._write_ok()

    def do_HEAD(self):  # noqa: N802
        self._write_ok()


class _ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


_health_server: _ThreadedTCPServer | None = None


def _resolve_port(default: int = 8080) -> int:
    raw_port = os.getenv('PORT')
    if not raw_port:
        return default
    try:
        value = int(raw_port)
        if value <= 0:
            raise ValueError("Port must be positive")
        return value
    except (TypeError, ValueError) as exc:
        print(f"⚠️ Invalid PORT value '{raw_port}': {exc}. Falling back to {default}.")
        return default


def start_health_server():
    """Start a tiny multithreaded HTTP health check server."""
    global _health_server
    try:
        port = _resolve_port()
        if _health_server is not None:
            print("ℹ️ Health server already running; reusing existing instance")
            return True

        print(f"Starting health server on port {port}")
        server = _ThreadedTCPServer(('0.0.0.0', port), _HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        _health_server = server
        print(f"✅ Health server listening on port {port}")
        return True
    except OSError as exc:
        print(f"❌ Failed to bind health server on port {port}: {exc}")
        return False
    except Exception as exc:  # Fallback for unexpected issues
        print(f"❌ Failed to start health server: {exc}")
        return False

# Load custom commands
def load_custom_commands():
    try:
        with open(COMMANDS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def ensure_accounts_store() -> None:
    """Create an empty accounts database if it does not already exist."""
    if not os.path.exists(ACCOUNTS_FILE):
        save_accounts({})


def normalize_account_line(account_line: str) -> str:
    """Return a trimmed, single-line representation that is easy to copy & paste."""
    clean_line = account_line.strip()
    # Collapse tabs or repeated whitespace to a single space to avoid odd formatting
    clean_line = re.sub(r"\s+", " ", clean_line)
    return clean_line


def load_accounts() -> dict[str, list[str]]:
    """Load the stored accounts grouped by category name."""
    ensure_accounts_store()
    with open(ACCOUNTS_FILE, 'r') as f:
        data = json.load(f)
        # Ensure the structure is always mapping -> list[str]
        if not isinstance(data, dict):
            return {}
        normalized: dict[str, list[str]] = {}
        for key, value in data.items():
            if isinstance(value, list):
                normalized[key] = [normalize_account_line(str(entry)) for entry in value]
        return normalized


def save_accounts(accounts: dict[str, list[str]]) -> None:
    """Persist the provided accounts dictionary to disk."""
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=2)


def parse_accounts_from_text(raw_text: str) -> list[str]:
    """Extract account lines that contain an e-mail address from arbitrary text."""
    parsed: list[str] = []
    for line in raw_text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if EMAIL_REGEX.search(candidate):
            parsed.append(normalize_account_line(candidate))
    return parsed


def load_barred_users() -> set[str]:
    """Load barred user IDs stored in the barred users config."""
    ensure_barred_users_config_exists()
    with open(BARRED_USERS_FILE, 'r') as f:
        data = json.load(f)
        return set(data.get("barred_users", []))


def is_user_barred(user_id: int) -> bool:
    """Return True if the given user_id is present in the barred users config."""
    barred_ids = load_barred_users()
    return str(user_id) in barred_ids


def ensure_barred_users_config_exists():
    """Ensure a JSON file exists to store barred user IDs."""
    if not os.path.exists(BARRED_USERS_FILE):
        with open(BARRED_USERS_FILE, 'w') as f:
            json.dump({"barred_users": []}, f, indent=2)


def save_barred_users(user_ids: set[str]) -> None:
    """Persist the provided set of barred user IDs to disk."""
    ensure_barred_users_config_exists()
    with open(BARRED_USERS_FILE, 'w') as f:
        json.dump({"barred_users": sorted(user_ids)}, f, indent=2)


def add_barred_user(user_id: int | str) -> None:
    """Add a user ID to the barred list if it is not already present."""
    user_id_str = str(user_id)
    barred_users = load_barred_users()
    if user_id_str not in barred_users:
        barred_users.add(user_id_str)
        save_barred_users(barred_users)
        print(f"🚫 Added barred user ID: {user_id_str}")


# Global command tree check to block barred users
async def global_barred_user_check(interaction: discord.Interaction) -> bool:
    """Global slash-command check that blocks any barred user."""
    if interaction.user and is_user_barred(interaction.user.id):
        # Returning False prevents the command from executing.
        return False
    return True


# Simple email matcher used when parsing account dumps
EMAIL_REGEX = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


# Save custom commands
def save_custom_commands(commands_dict):
    with open(COMMANDS_FILE, 'w') as f:
        json.dump(commands_dict, f, indent=2)

# Load payment links
def load_payment_links():
    try:
        with open(LINKS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "neck": {
                "apple_pay": "",
                "zelle": "",
                "cashapp": "",
                "credit": ""
            },
            "sb": {
                "apple_pay": "",
                "zelle": "",
                "cashapp": "",
                "credit": ""
            },
            "angie": {
                "apple_pay": "",
                "zelle": "",
                "cashapp": "",
                "credit": ""
            }
        }

# Save payment links
def save_payment_links(links_dict):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links_dict, f, indent=2)

# Load enjoy messages
def load_enjoy_messages():
    try:
        with open(ENJOY_FILE, 'r') as f:
            data = json.load(f)
            # Auto-heal: ensure exactly the 50 personalized messages with (user) and #casino
            if _needs_enjoy_update(data):
                healed = {"messages": DEFAULT_ENJOY_MESSAGES, "index": 0}
                save_enjoy_messages(healed)
                print("🔧 Auto-updated enjoy_messages.json to default 50 personalized prompts")
                return healed
            return data
    except FileNotFoundError:
        default_data = {"messages": DEFAULT_ENJOY_MESSAGES, "index": 0}
        save_enjoy_messages(default_data)
        return default_data

# Save enjoy messages
def save_enjoy_messages(enjoy_data):
    with open(ENJOY_FILE, 'w') as f:
        json.dump(enjoy_data, f, indent=2)

# Initialize data files
if not os.path.exists(COMMANDS_FILE):
    save_custom_commands({})

if not os.path.exists(LINKS_FILE):
    save_payment_links({
        "neck": {
            "apple_pay": "",
            "zelle": "",
            "cashapp": "",
            "credit": ""
        },
        "sb": {
            "apple_pay": "",
            "zelle": "",
            "cashapp": "",
            "credit": ""
        },
        "angie": {
            "apple_pay": "",
            "zelle": "",
            "cashapp": "",
            "credit": ""
        }
    })

# Initialize enjoy messages file
if not os.path.exists(ENJOY_FILE):
    save_enjoy_messages({
        "messages": DEFAULT_ENJOY_MESSAGES,
        "index": 0,
    })

if not os.path.exists(WELCOME_FILE):
    with open(WELCOME_FILE, 'w') as f:
        json.dump({"messages": DEFAULT_WELCOME_MESSAGES, "index": 0}, f, indent=2)

if not os.path.exists(ACCOUNTS_FILE):
    save_accounts({})

# Ensure barred users config exists and seed default barred IDs
ensure_barred_users_config_exists()
for default_barred_id in DEFAULT_BARRED_USERS:
    add_barred_user(default_barred_id)

# Register the check via the tree's interaction_check hook
bot.tree.interaction_check = global_barred_user_check
print("✅ Registered global barred user check for command tree")


def load_welcome_messages() -> dict:
    try:
        with open(WELCOME_FILE, 'r') as f:
            data = json.load(f)
            if _needs_welcome_update(data):
                healed = {"messages": DEFAULT_WELCOME_MESSAGES, "index": 0}
                save_welcome_messages(healed)
                print("🔧 Auto-updated welcome_messages.json to spotlight latest promos")
                return healed
            messages = data.get("messages", [])
            if not messages:
                data = {"messages": DEFAULT_WELCOME_MESSAGES, "index": 0}
                save_welcome_messages(data)
            return data
    except FileNotFoundError:
        data = {"messages": DEFAULT_WELCOME_MESSAGES, "index": 0}
        save_welcome_messages(data)
        return data


def save_welcome_messages(data: dict) -> None:
    with open(WELCOME_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_next_welcome_message(member: discord.Member) -> str | None:
    if member.bot:
        return None
    data = load_welcome_messages()
    messages: list[str] = data.get("messages", DEFAULT_WELCOME_MESSAGES)
    if not messages:
        return None
    index = data.get("index", 0) % len(messages)
    template = messages[index]
    data["index"] = (index + 1) % len(messages)
    save_welcome_messages(data)
    base_line = template.replace("(user)", member.mention)

    now_hour = time.localtime().tm_hour
    slot = _time_slot_from_hour(now_hour)
    time_variant = random.choice(TIME_OF_DAY_SNIPPETS.get(slot, TIME_OF_DAY_SNIPPETS["evening"]))

    extras: list[str] = [time_variant]

    if member.guild and member.guild.member_count:
        count_formatted = f"{member.guild.member_count:,}"
        extras.append(random.choice(MEMBER_COUNT_SNIPPETS).format(count=count_formatted))

    extras.append(random.choice(WELCOME_ROLLOUT_SNIPPETS))

    return "\n".join([base_line] + extras)


@bot.event
async def on_member_join(member: discord.Member):
    welcome_line = get_next_welcome_message(member)
    if not welcome_line:
        return
    guild = member.guild
    if guild is None:
        return

    fallback_channels: list[discord.abc.MessageableChannel] = []

    system_channel = getattr(guild, "system_channel", None)
    if system_channel is not None:
        fallback_channels.append(system_channel)

    preferred_names = ("welcome", "introductions", "general")
    for name in preferred_names:
        channel = discord.utils.get(guild.text_channels, name=name)
        if channel is not None and channel not in fallback_channels:
            fallback_channels.append(channel)

    if not fallback_channels:
        bot_member = getattr(guild, "me", None) or guild.get_member(bot.user.id)
        for channel in guild.text_channels:
            try:
                if bot_member and channel.permissions_for(bot_member).send_messages:
                    fallback_channels.append(channel)
                    break
            except Exception:
                continue

    for channel in fallback_channels:
        try:
            await channel.send(welcome_line)
            return
        except Exception as channel_exc:
            print(
                "⚠️ Failed to deliver welcome message for %s via %s: %s"
                % (member.id, getattr(channel, "name", "unknown"), channel_exc)
            )

    if not fallback_channels:
        print(f"⚠️ Failed to deliver welcome message for {member.id}: no accessible channel")


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="createcommand", description="Create a new custom command (Provider role only)")
@app_commands.describe(
    command_name="Name of the command (without /)",
    response="What the command should respond with"
)
async def createcommand(interaction: discord.Interaction, command_name: str, response: str):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    # Load existing commands
    custom_commands = load_custom_commands()
    
    # Check if command already exists
    if command_name.lower() in custom_commands:
        await interaction.response.send_message(f"❌ Command `/{command_name}` already exists! Use `/editcommand` to modify it.", ephemeral=True)
        return
    
    # Add new command
    custom_commands[command_name.lower()] = response
    save_custom_commands(custom_commands)
    
    await interaction.response.send_message(f"✅ New command `/{command_name}` has been created!", ephemeral=True)

@bot.tree.command(name="editcommand", description="Edit an existing custom command (Provider role only)")
@app_commands.describe(
    command_name="Name of the command to edit",
    response="New response for the command"
)
async def editcommand(interaction: discord.Interaction, command_name: str, response: str):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    # Load existing commands
    custom_commands = load_custom_commands()
    
    # Check if command exists
    if command_name.lower() not in custom_commands:
        await interaction.response.send_message(f"❌ Command `/{command_name}` doesn't exist! Use `/createcommand` to create it.", ephemeral=True)
        return
    
    # Update command
    custom_commands[command_name.lower()] = response
    save_custom_commands(custom_commands)
    
    await interaction.response.send_message(f"✅ Command `/{command_name}` has been updated!", ephemeral=True)


@bot.tree.command(name="bulkadd", description="Bulk add accounts to a category (Provider role only)")
@app_commands.describe(
    category="Name of the account category",
    entries="Text containing accounts (one per line)"
)
async def bulkadd(interaction: discord.Interaction, category: str, entries: str):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return

    parsed_accounts = parse_accounts_from_text(entries)
    if not parsed_accounts:
        await interaction.response.send_message("⚠️ I couldn't find any account lines containing an email address.", ephemeral=True)
        return

    accounts_store = load_accounts()
    category_key = category.strip().lower()
    stored_accounts = accounts_store.setdefault(category_key, [])

    existing = set(stored_accounts)
    added = 0
    for account in parsed_accounts:
        if account not in existing:
            stored_accounts.append(account)
            existing.add(account)
            added += 1

    save_accounts(accounts_store)

    duplicates = len(parsed_accounts) - added
    response_lines = [f"✅ Added {added} new account(s) to `{category}`."]
    response_lines.append(f"📦 `{category}` now has {len(stored_accounts)} account(s) available.")
    if duplicates > 0:
        response_lines.append(f"ℹ️ Skipped {duplicates} duplicate line(s).")

    await interaction.response.send_message("\n".join(response_lines), ephemeral=True)


@bot.tree.command(name="getaccount", description="Retrieve and remove the next account from a category")
@app_commands.describe(category="Name of the account category to pull from")
async def getaccount(interaction: discord.Interaction, category: str):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return

    accounts_store = load_accounts()
    category_key = category.strip().lower()
    queued_accounts = accounts_store.get(category_key, [])

    if not queued_accounts:
        await interaction.response.send_message(f"⚠️ No accounts stored for `{category}`.", ephemeral=True)
        return

    account_line = normalize_account_line(queued_accounts.pop(0))
    if not queued_accounts:
        accounts_store.pop(category_key, None)
    save_accounts(accounts_store)

    await interaction.response.send_message(
        account_line,
        ephemeral=True,
        allowed_mentions=AllowedMentions.none()
    )

    await interaction.followup.send(
        f"✅ Removed the retrieved `{category}` entry from the queue. {len(queued_accounts)} account(s) remain.",
        ephemeral=True
    )


@bot.tree.command(name="listaccounts", description="List stored account categories and counts (Provider role only)")
async def listaccounts(interaction: discord.Interaction):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return

    accounts_store = load_accounts()
    if not accounts_store:
        await interaction.response.send_message("📭 No accounts have been stored yet.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🗂️ Stored Account Categories",
        description="Current categories and the number of accounts remaining in each queue:",
        color=0x3498db
    )

    for category_key, items in sorted(accounts_store.items()):
        display_name = category_key
        embed.add_field(name=display_name, value=f"{len(items)} account(s)", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="clearaccount", description="Remove all accounts from a category (Provider role only)")
@app_commands.describe(category="Name of the account category to clear")
async def clearaccount(interaction: discord.Interaction, category: str):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return

    accounts_store = load_accounts()
    category_key = category.strip().lower()

    if category_key not in accounts_store:
        await interaction.response.send_message(f"⚠️ `{category}` doesn't have any stored accounts.", ephemeral=True)
        return

    removed = len(accounts_store.pop(category_key, []))
    save_accounts(accounts_store)

    await interaction.response.send_message(
        f"🗑️ Cleared `{removed}` account(s) from `{category}`.",
        ephemeral=True
    )


@bot.tree.command(name="neck", description="Get payment method links")
async def neck(interaction: discord.Interaction):
    # LAYER 4 DEFENSE: Individual command guard
    if is_user_barred(interaction.user.id):
        return
    
    # Load payment links
    all_links = load_payment_links()
    links = all_links.get("neck", {})
    
    embed = discord.Embed(
        title="💳 Payment Methods - Neck",
        description="Here are our accepted payment methods:",
        color=0x0099ff
    )
    
    # Add fields only if links are set
    if links.get("apple_pay"):
        embed.add_field(
            name="🍎 Apple Pay",
            value=links['apple_pay'],
            inline=False
        )
    
    if links.get("zelle"):
        embed.add_field(
            name="💸 Zelle",
            value=f"[Send to Zelle]({links['zelle']})",
            inline=False
        )
    
    if links.get("cashapp"):
        embed.add_field(
            name="📱 Cash App (Add 25¢ for fees)",
            value=f"[Send via Cash App]({links['cashapp']})",
            inline=False
        )
    
    if links.get("credit"):
        embed.add_field(
            name="💳 Credit/Debit",
            value=f"[Pay Online]({links['credit']})",
            inline=False
        )
    
    # If no links are set, show a message
    if not any(links.values()):
        embed.add_field(
            name="⚠️ No Payment Links Set",
            value="Contact an admin to set up payment methods using `/setlink`",
            inline=False
        )
    
    embed.set_footer(text="Contact support if you need help with payment!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="sb", description="Get payment method links")
async def sb(interaction: discord.Interaction):
    # LAYER 4 DEFENSE: Individual command guard
    if is_user_barred(interaction.user.id):
        return
    
    # Load payment links
    all_links = load_payment_links()
    links = all_links.get("sb", {})
    
    embed = discord.Embed(
        title="💳 Payment Methods - SB",
        description="Here are our accepted payment methods:",
        color=0x0099ff
    )
    
    # Add fields only if links are set
    if links.get("apple_pay"):
        embed.add_field(
            name="🍎 Apple Pay",
            value=links['apple_pay'],
            inline=False
        )
    
    if links.get("zelle"):
        embed.add_field(
            name="💸 Zelle",
            value=f"[Send to Zelle]({links['zelle']})",
            inline=False
        )
    
    if links.get("cashapp"):
        embed.add_field(
            name="📱 Cash App (Add 25¢ for fees)",
            value=f"[Send via Cash App]({links['cashapp']})",
            inline=False
        )
    
    if links.get("credit"):
        embed.add_field(
            name="💳 Credit/Debit",
            value=f"[Pay Online]({links['credit']})",
            inline=False
        )
    
    # If no links are set, show a message
    if not any(links.values()):
        embed.add_field(
            name="⚠️ No Payment Links Set",
            value="Contact an admin to set up payment methods using `/setlink`",
            inline=False
        )
    
    embed.set_footer(text="Contact support if you need help with payment!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="angie", description="Get payment method links")
async def angie(interaction: discord.Interaction):
    # LAYER 4 DEFENSE: Individual command guard
    if is_user_barred(interaction.user.id):
        return
    
    # Load payment links
    all_links = load_payment_links()
    links = all_links.get("angie", {})
    
    embed = discord.Embed(
        title="💳 Payment Methods - Angie",
        description="Here are our accepted payment methods:",
        color=0x0099ff
    )
    
    # Add fields only if links are set
    if links.get("apple_pay"):
        embed.add_field(
            name="🍎 Apple Pay",
            value=links['apple_pay'],
            inline=False
        )
    
    if links.get("zelle"):
        embed.add_field(
            name="💸 Zelle",
            value=f"[Send to Zelle]({links['zelle']})",
            inline=False
        )
    
    if links.get("cashapp"):
        embed.add_field(
            name="📱 Cash App (Add 25¢ for fees)",
            value=f"[Send via Cash App]({links['cashapp']})",
            inline=False
        )
    
    if links.get("credit"):
        embed.add_field(
            name="💳 Credit/Debit",
            value=f"[Pay Online]({links['credit']})",
            inline=False
        )
    
    # If no links are set, show a message
    if not any(links.values()):
        embed.add_field(
            name="⚠️ No Payment Links Set",
            value="Contact an admin to set up payment methods using `/setlink`",
            inline=False
        )
    
    embed.set_footer(text="Contact support if you need help with payment!")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="enjoy", description="Send a personalized thank-you message to a customer")
@app_commands.describe(
    customer="The customer to thank (type their name or mention them with @)"
)
async def enjoy(interaction: discord.Interaction, customer: str):
    # LAYER 4 DEFENSE: Individual command guard
    if is_user_barred(interaction.user.id):
        return

    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used inside a server.", ephemeral=True
        )
        return

    try:
        # Find the user by name or mention
        target_user = None

        # If it's a mention (starts with <@), try to extract the user ID
        if customer.startswith('<@') and customer.endswith('>'):
            try:
                # Extract user ID from mention
                user_id = int(customer.strip('<@!&>'))
                target_user = guild.get_member(user_id)
            except (ValueError, AttributeError):
                pass
        else:
            # Look up by display name or username
            for member in guild.members:
                if member.display_name.lower() == customer.lower() or member.name.lower() == customer.lower():
                    target_user = member
                    break

        if not target_user:
            await interaction.response.send_message(f"❌ Could not find user '{customer}'. Please type their exact name or mention them with @", ephemeral=True)
            return

        # Load messages and pick current one
        enjoy_data = load_enjoy_messages()
        messages = enjoy_data.get("messages", [])
        index = enjoy_data.get("index", 0)

        print(f"DEBUG: Loaded {len(messages)} messages, current index: {index}")  # Debug log

        if not messages:
            await interaction.response.send_message("⚠️ No enjoy messages configured.")
            return

        # Get the raw message template
        message_template = messages[index % len(messages)]
        print(f"DEBUG: Raw message template: {message_template}")  # Debug log

        # Replace (user) placeholder with the customer's mention (creates @ping)
        personalized_message = message_template.replace("(user)", target_user.mention)

        # Convert #vouch and #casino placeholders into channel mentions
        vouch_channel = None
        casino_channel = None
        try:
            # Prefer exact channel name 'vouch-📸', then any channel containing 'vouch'
            vouch_channel = next(
                (c for c in guild.text_channels if c.name == 'vouch-📸'),
                None
            )
            if vouch_channel is None:
                vouch_channel = next(
                    (c for c in guild.text_channels if 'vouch' in c.name.lower()),
                    None
                )
            # Exact name first, then any channel containing 'casino' (ignoring suits)
            casino_channel = next(
                (c for c in guild.text_channels if c.name == '♠♥casino♣♦'),
                None
            )
            if casino_channel is None:
                casino_channel = next(
                    (c for c in guild.text_channels if 'casino' in c.name.lower()),
                    None
                )
        except Exception:
            pass

        if vouch_channel is not None:
            personalized_message = personalized_message.replace('#vouch', f'<#{vouch_channel.id}>')
            personalized_message = personalized_message.replace('#vouch-📸', f'<#{vouch_channel.id}>')

        if casino_channel is not None:
            personalized_message = personalized_message.replace('#casino', f'<#{casino_channel.id}>')
            personalized_message = personalized_message.replace('#♠♥casino♣♦', f'<#{casino_channel.id}>')

        print(f"DEBUG: Personalized message: {personalized_message}")  # Debug log

        # Send the personalized message
        await interaction.response.send_message(personalized_message)

        # Advance the index and save
        enjoy_data["index"] = (index + 1) % len(messages)
        save_enjoy_messages(enjoy_data)
        print(f"DEBUG: Advanced index to: {enjoy_data['index']}")  # Debug log
    except Exception as e:
        print(f"ERROR in enjoy command: {e}")  # Debug log
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="listcommands", description="List all custom commands")
async def listcommands(interaction: discord.Interaction):
    # LAYER 4 DEFENSE: Individual command guard
    if is_user_barred(interaction.user.id):
        return
    
    custom_commands = load_custom_commands()
    
    if not custom_commands:
        await interaction.response.send_message("📝 No custom commands created yet!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📝 Custom Commands",
        description="Here are all your custom commands:",
        color=0x00ff00
    ) 
    
    for cmd_name, response in custom_commands.items():
        # Truncate long responses for display
        display_response = response[:50] + "..." if len(response) > 50 else response
        embed.add_field(name=f"/{cmd_name}", value=display_response, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="deletecommand", description="Delete a custom command (Provider role only)")
@app_commands.describe(
    command_name="Name of the command to delete"
)
async def deletecommand(interaction: discord.Interaction, command_name: str):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    custom_commands = load_custom_commands()
    
    if command_name.lower() not in custom_commands:
        await interaction.response.send_message(f"❌ Command `/{command_name}` doesn't exist!", ephemeral=True)
        return
    
    # Delete the command
    del custom_commands[command_name.lower()]
    save_custom_commands(custom_commands)
    
    await interaction.response.send_message(f"🗑️ Command `/{command_name}` has been deleted!", ephemeral=True)

@bot.tree.command(name="setlink", description="Set a payment method link (Provider role only)")
@app_commands.describe(
    provider="Which provider to set links for (neck, sb, angie)",
    payment_method="Which payment method to set (apple_pay, zelle, cashapp, credit)",
    url="The URL/link for this payment method"
)
@app_commands.choices(provider=[
    app_commands.Choice(name="Neck", value="neck"),
    app_commands.Choice(name="SB", value="sb"),
    app_commands.Choice(name="Angie", value="angie")
])
@app_commands.choices(payment_method=[
    app_commands.Choice(name="Apple Pay", value="apple_pay"),
    app_commands.Choice(name="Zelle", value="zelle"),
    app_commands.Choice(name="Cash App", value="cashapp"),
    app_commands.Choice(name="Credit/Debit", value="credit")
])
async def setlink(interaction: discord.Interaction, provider: str, payment_method: str, url: str):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    # Load existing links
    all_links = load_payment_links()
    
    # Make sure the provider exists in the links
    if provider not in all_links:
        all_links[provider] = {
            "apple_pay": "",
            "zelle": "",
            "cashapp": "",
            "credit": ""
        }
    
    # For Apple Pay, convert phone number to clickable link
    if payment_method == "apple_pay":
        # Check if it's just a phone number (digits only, possibly with + at start)
        if url.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
            # Format phone number and create clickable link for iMessage
            clean_number = url.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            clickable_link = f"[Message {url}](sms:{clean_number})"
            all_links[provider][payment_method] = clickable_link
        else:
            # If it's already a full URL, use it as is
            all_links[provider][payment_method] = url
    else:
        # For other payment methods, use the URL as provided
        all_links[provider][payment_method] = url
    
    save_payment_links(all_links)
    
    # Get display names
    provider_names = {
        "neck": "Neck",
        "sb": "SB",
        "angie": "Angie"
    }
    method_names = {
        "apple_pay": "Apple Pay",
        "zelle": "Zelle", 
        "cashapp": "Cash App",
        "credit": "Credit/Debit"
    }
    
    await interaction.response.send_message(
        f"✅ {method_names[payment_method]} link has been set for {provider_names[provider]}!\n`{url}`", 
        ephemeral=True
    )

@bot.tree.command(name="viewlinks", description="View all current payment links (Provider role only)")
async def viewlinks(interaction: discord.Interaction):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    # Load payment links
    all_links = load_payment_links()
    
    embed = discord.Embed(
        title="🔗 Current Payment Links",
        description="Here are the currently set payment links for all providers:",
        color=0x00ff00
    )
    
    provider_names = {
        "neck": "Neck",
        "sb": "SB",
        "angie": "Angie"
    }
    method_names = {
        "apple_pay": "🍎 Apple Pay",
        "zelle": "💸 Zelle",
        "cashapp": "📱 Cash App", 
        "credit": "💳 Credit/Debit"
    }
    
    for provider, provider_display in provider_names.items():
        provider_links = all_links.get(provider, {})
        if any(provider_links.values()):
            embed.add_field(
                name=f"**{provider_display}**", 
                value="", 
                inline=False
            )
            for method, method_display in method_names.items():
                link = provider_links.get(method, "")
                if link:
                    embed.add_field(name=method_display, value=f"`{link}`", inline=False)
                else:
                    embed.add_field(name=method_display, value="*Not set*", inline=False)
        else:
            embed.add_field(
                name=f"**{provider_display}**", 
                value="*No links set*", 
                inline=False
            )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="open", description="Open the business - rename status channel and make order channel public (Provider role only)")
async def open_business(interaction: discord.Interaction):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    # Respond immediately to prevent timeout
    await interaction.response.send_message("🔄 Opening business...", ephemeral=True)
    
    try:
        # Find ALL channels with "open", "closed", "pause" or status emoji in the name and rename them
        renamed_channels = []
        for channel in interaction.guild.channels:
            if "open" in channel.name.lower() or "closed" in channel.name.lower() or "pause" in channel.name.lower() or "🟢" in channel.name or "🔴" in channel.name or "🟡" in channel.name:
                await channel.edit(name="🟢-open")
                renamed_channels.append(channel.name)
        
        if not renamed_channels:
            await interaction.edit_original_response(content="❌ Could not find any channels with 'open' or 'closed' in the name! Please create a status channel first.")
            return
        
        # Find the order-here channel specifically
        order_channel = None
        for channel in interaction.guild.channels:
            if "order-here" in channel.name.lower():
                order_channel = channel
                break
        
        if not order_channel:
            await interaction.edit_original_response(content="❌ Could not find order-here channel!")
            return
        
        # Make order-here channel public (remove @everyone overwrite if it exists)
        everyone_role = interaction.guild.default_role
        overwrites = order_channel.overwrites_for(everyone_role)
        
        # Set permissions for @everyone: can view and react, but cannot send messages
        overwrites.view_channel = True
        overwrites.send_messages = False
        overwrites.add_reactions = True
        await order_channel.set_permissions(everyone_role, overwrite=overwrites)
        
        await interaction.edit_original_response(content="✅ Business is now **OPEN**! 🟢\n- All status channels renamed to 🟢-open\n- Order-here channel is now read-only (view + react, no sending)")
        
    except discord.Forbidden:
        await interaction.edit_original_response(content="❌ I don't have permission to modify channels!")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Error: {str(e)}")

@bot.tree.command(name="close", description="Close the business - rename status channel and make order channel private (Provider role only)")
async def close_business(interaction: discord.Interaction):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    # Respond immediately to prevent timeout
    await interaction.response.send_message("🔄 Closing business...", ephemeral=True)
    
    try:
        # Find ALL channels with "open", "closed", "pause" or status emoji in the name and rename them
        renamed_channels = []
        for channel in interaction.guild.channels:
            if "open" in channel.name.lower() or "closed" in channel.name.lower() or "pause" in channel.name.lower() or "🟢" in channel.name or "🔴" in channel.name or "🟡" in channel.name:
                await channel.edit(name="🔴-closed")
                renamed_channels.append(channel.name)
        
        if not renamed_channels:
            await interaction.edit_original_response(content="❌ Could not find any channels with 'open' or 'closed' in the name! Please create a status channel first.")
            return
        
        # Find the order-here channel specifically
        order_channel = None
        for channel in interaction.guild.channels:
            if "order-here" in channel.name.lower():
                order_channel = channel
                break
        
        if not order_channel:
            await interaction.edit_original_response(content="❌ Could not find order-here channel!")
            return
        
        # Make order-here channel private (deny @everyone view, send, and history)
        everyone_role = interaction.guild.default_role
        await order_channel.set_permissions(
            everyone_role, 
            view_channel=False,
            send_messages=False,
            read_message_history=False
        )
        
        await interaction.edit_original_response(content="✅ Business is now **CLOSED**! 🔴\n- All status channels renamed to 🔴-closed\n- Order-here channel is now private (no view, send, or history)")
        
    except discord.Forbidden:
        await interaction.edit_original_response(content="❌ I don't have permission to modify channels!")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Error: {str(e)}")

@bot.tree.command(name="pause", description="Pause the business with a custom message (Provider role only)")
@app_commands.describe(
    message="Custom message to display (e.g., 'will be open in 10')"
)
async def pause_business(interaction: discord.Interaction, message: str):
    if is_user_barred(interaction.user.id):
        await interaction.response.send_message("❌ You are barred from using this command!", ephemeral=True)
        return

    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    # Respond immediately to prevent timeout
    await interaction.response.send_message("🔄 Pausing business...", ephemeral=True)
    
    try:
        # Find ALL channels with "open", "closed", "pause" or status emoji in the name
        renamed_channels = []
        for channel in interaction.guild.channels:
            if "open" in channel.name.lower() or "closed" in channel.name.lower() or "pause" in channel.name.lower() or "🟢" in channel.name or "🔴" in channel.name or "🟡" in channel.name:
                # Format: 🟡-{message} with spaces replaced by hyphens (message first for visibility)
                safe_message = message.replace(" ", "-")
                await channel.edit(name=f"🟡-{safe_message}")
                renamed_channels.append(channel.name)
        
        if not renamed_channels:
            await interaction.edit_original_response(content="❌ Could not find any status channels!")
            return
        
        # Find the order-here channel and set same permissions as /close
        order_channel = None
        for channel in interaction.guild.channels:
            if "order-here" in channel.name.lower():
                order_channel = channel
                break
        
        if not order_channel:
            await interaction.edit_original_response(content="❌ Could not find order-here channel!")
            return
        
        # Make order-here channel private (same as /close)
        everyone_role = interaction.guild.default_role
        await order_channel.set_permissions(
            everyone_role, 
            view_channel=False,
            send_messages=False,
            read_message_history=False
        )
        
        await interaction.edit_original_response(
            content=f"✅ Business is now **PAUSED**! 🟡\n- Status: {message}\n- All status channels updated\n- Order-here channel is now private"
        )
        
    except discord.Forbidden:
        await interaction.edit_original_response(content="❌ I don't have permission to modify channels!")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Error: {str(e)}")

# Dynamic command handler for custom commands
@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Handle incoming interactions and fall back to the default command tree."""

    # LAYER 2 DEFENSE: Immediately ignore ALL interactions from barred users.
    # This is checked before any other processing as a safety net.
    try:
        if interaction.user and is_user_barred(interaction.user.id):
            command_info = getattr(interaction, "data", {}) or {}
            command_name = command_info.get('name', 'unknown')
            print(
                f"🚫 [Layer 2] Silently ignoring interaction '{command_name}' from barred user {interaction.user.id}"
            )
            return  # Exit immediately without acknowledging
    except Exception as e:
        print(f"⚠️ Error checking barred status in on_interaction: {e}")

    handled = False

    if interaction.type == discord.InteractionType.application_command:
        command_name = interaction.data.get('name') if interaction.data else None

        if command_name:
            # Check if it's a custom command stored in our JSON config.
            custom_commands = load_custom_commands()
            if command_name in custom_commands:
                response = custom_commands[command_name]
                await interaction.response.send_message(response)
                handled = True

    if not handled:
        # Let other interactions pass through to the default handler that discord.py
        # normally provides. ``CommandTree._call`` mirrors the library's built-in
        # processing (``process_application_commands`` existed only in forks such as
        # py-cord), so using it keeps behaviour identical across library versions.
        try:
            await bot.tree._call(interaction)
        except AttributeError:
            print("⚠️ CommandTree._call is unavailable; interaction was not handled.")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore command not found errors
    else:
        print(f"Error: {error}")

# App command (slash command) error handler
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    # LAYER 3 DEFENSE: Silently ignore ALL errors from barred users
    try:
        if interaction.user and is_user_barred(interaction.user.id):
            print(f"🚫 [Layer 3] Silently ignoring error from barred user {interaction.user.id}: {type(error).__name__}")
            return  # Don't send any response or acknowledge the error
    except Exception as e:
        print(f"⚠️ Error checking barred status in error handler: {e}")
    
    # For non-barred users, handle CheckFailure silently (could be other checks)
    if isinstance(error, app_commands.CheckFailure):
        print(f"⚠️ Command check failed for user {interaction.user.id if interaction.user else 'unknown'}: {error}")
        return

# Run the bot
if __name__ == "__main__":
    print("Starting Speedwagon Discord bot...")
    
    # Check if DISCORD_TOKEN exists
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ ERROR: DISCORD_TOKEN environment variable not found!")
        print("Please set DISCORD_TOKEN in Railway variables")
        exit(1)
    
    print(f"✅ Discord token found (length: {len(token)})")
    
    # Start health check server FIRST before anything else
    print("Starting health check server...")
    health_ready = start_health_server()
    
    if health_ready:
        print("✅ Health check server is ready")
        # Give health server a moment to fully bind and start accepting connections
        time.sleep(1)
    else:
        print("⚠️ Health check server failed, but continuing...")
        # Still sleep briefly to allow any partial startup
        time.sleep(0.5)
    
    # Start the bot
    print("Connecting to Discord...")
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        exit(1)
