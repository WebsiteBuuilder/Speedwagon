import discord
from discord import app_commands
from discord.ext import commands
import json
import shutil
import os
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
DEFAULT_BARRED_USERS: tuple[str, ...] = (
    "1405894979095892108",
)

# Built-in default /enjoy messages (50), using (user) placeholder and #vouch/#casino
DEFAULT_ENJOY_MESSAGES = [
    "✅ Thanks for ordering, (user)! Enjoy your meal 🍔 Don’t forget to vouch in #vouch for points—redeem for free food or gamble in #casino 🎰",
    "🚀 Order’s in, (user)! Feast mode ON 😋 Drop a vouch in #vouch to stack points → free orders or casino wins 🎡",
    "🍽️ Dig in, (user)! Be sure to post in #vouch for reward points 🎟️ Redeem for free eats or take your shot in #casino 🃏",
    "🎊 Appreciate you, (user)! Enjoy your QuikEats 🍕 Earn points by vouching in #vouch then try your luck in #casino 🎲",
    "✨ Enjoy every bite, (user) 😍 A quick vouch in #vouch = points toward free orders & casino plays 💎",
    "🥳 Thanks for riding with us, (user)! After your meal, vouch in #vouch for points → free meals or big wins in #casino 🎰",
    "🍔🍟 Chow time, (user)! Earn points by dropping a vouch in #vouch → redeem or gamble in #casino 🔥",
    "⚡ Enjoy your QuikEats drop, (user)! Share a vouch in #vouch for points & hit #casino to spin 🎲",
    "💯 Appreciate your order, (user)! Every vouch in #vouch = points 🪙 Free food or double down in #casino ♠️",
    "🍴 Cravings crushed, (user)! Don’t forget to vouch in #vouch → stack points, redeem, or gamble 💫",
    "🥢 Meal delivered 🥡, (user)! Vouch in #vouch for points → use for free eats or casino fun 🎰",
    "🏆 You’re a winner already, (user)! Thanks for ordering 💎 Drop a vouch in #vouch to claim points & play in #casino 🎲",
    "🍕🍔 Hot & ready, (user)! Enjoy 😋 Then vouch in #vouch → free orders or a casino jackpot 🎰",
    "🔥 Order locked in, (user)! Enjoy your food and vouch in #vouch for points → gamble them in #casino 🎡",
    "🎶 Dinner vibes active 😎, (user)! Drop a vouch in #vouch → earn points & spin the games in #casino 🃏",
    "💥 Thanks for rolling with QuikEats, (user)! Enjoy your food & claim points in #vouch → jackpot awaits in #casino 🎰",
    "🥤 Sip back, relax, (user) 🍔 Don’t forget to vouch in #vouch for points → redeem or risk in #casino 🎲",
    "🌟 Enjoy your QuikEats, (user)! Collect points in #vouch → freebies OR roulette, blackjack, slots in #casino 💎",
    "🕹️ Level up, (user)! Food’s here 🍕 Bonus points waiting in #vouch → free orders or casino action 🎰",
    "🍜 Slurp it up, (user)! Post your vouch in #vouch to stack points → gamble them in #casino 🎲",
    "🚨 QuikEats complete ✅, (user)! Enjoy & vouch in #vouch → rewards or casino wins 🎰",
    "🍴 Bon appétit, (user) 😍 Don’t miss your vouch in #vouch → points = free orders or casino shots 🎲",
    "🥂 Cheers to you, (user)! Thanks for ordering 🥳 Vouch in #vouch to stack points & gamble in #casino 🃏",
    "🤑 Rack up, (user)! Enjoy your food & vouch in #vouch → points for free meals or casino play 🎰",
    "🎯 Mission complete, (user)! Food delivered ✅ Vouch in #vouch for points → spend or spin 🎲",
    "🧃 Refresh & feast 😋, (user)! Drop a vouch in #vouch → free orders or casino jackpots 🎡",
    "🛎️ Your food’s in, (user)! Earn points by vouching in #vouch → free meals or casino fun 🎰",
    "🍔💨 Fast food, faster rewards, (user)! Don’t forget #vouch → free eats or casino thrills 🎲",
    "🌈 Taste the win, (user)! Vouch in #vouch for points → redeem or risk them in #casino 🎰",
    "🎁 Big thanks, (user)! Enjoy your QuikEats & vouch in #vouch → free meals or casino jackpots 💎",
    "💌 Thanks a bunch, (user)! Enjoy your order 💫 Don’t forget: vouch in #vouch to stack points & roll the dice in #casino 🎲",
    "🥳 Food secured, (user)! Feast away 😋 Vouch in #vouch for reward points → gamble or redeem 🎰",
    "🔑 Unlock rewards, (user)! Enjoy your food & claim points in #vouch → spend or spin them in #casino 🎡",
    "🍟 Fries hot, vibes hotter, (user)! Vouch in #vouch for points → free eats or jackpot chances 🎰",
    "🥤 Sip + snack = win, (user)! Be sure to vouch in #vouch → collect points, redeem, or risk 🎲",
    "🏅 You’re VIP, (user)! Thanks for ordering 🎉 Earn points by vouching in #vouch → play them in #casino 🃏",
    "🍴 Feast mode engaged, (user)! Vouch in #vouch for points toward free meals or casino fun 🎰",
    "🔔 Ding ding, order’s here, (user)! Enjoy + vouch in #vouch → stack rewards & gamble 🎡",
    "✌️ Big ups, (user)! Enjoy your QuikEats & earn by vouching in #vouch → points = food or casino shots 🎲",
    "🎨 Flavor unlocked, (user)! Post your vouch in #vouch → redeem or risk it in #casino 🎰",
    "🧨 Boom! Order’s dropped, (user)! Enjoy & vouch in #vouch → rack points, play in #casino 🔥",
    "🍔 Hungry no more, (user)! Thanks for choosing QuikEats 🙌 Don’t forget to vouch in #vouch → stack rewards 🎲",
    "🌟 Meal vibes strong, (user)! Drop a vouch in #vouch → points for free orders or casino jackpots 🎰",
    "🥢 Fresh eats delivered, (user)! Vouch in #vouch → free meals or risk it all in #casino 🎡",
    "🍩 Sweet win, (user)! Enjoy & don’t miss your vouch in #vouch → gamble points in #casino 🃏",
    "🚦 Green light to eat, (user)! Chow down 😋 Vouch in #vouch for points → freebies or casino 🎰",
    "📦 Delivery complete, (user)! Enjoy + earn points with a quick vouch in #vouch → redeem or spin 🎲",
    "💫 Thanks for choosing us, (user)! Drop a vouch in #vouch to unlock free orders or casino games 🎡",
    "🎉 Party plate unlocked, (user)! Enjoy & vouch in #vouch → rewards or gamble in #casino 🎰",
    "🔥 Feast up, (user)! Your meal’s ready—don’t forget to vouch in #vouch → stack points & try your luck 🎲",
]

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
    """
    Global check for all slash commands. Returns False to block barred users.
    This is registered with bot.tree.add_check() below.
    """
    if is_user_barred(interaction.user.id):
        # Return False to prevent command execution
        return False
    return True


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
        "messages": [
            "🚀 Thanks for ordering with QuikEats! 🍔✨ Drop a pic in #vouch 📸🔥 @ a provider to earn points 🎯 — stack them for a FREE order 🆓🍕🙌",
            "🎉 Appreciate your order with QuikEats! 🍟 Post your meal in #vouch 📸 and @ a provider to rack up points 🎯 — free food awaits 🆓🍕",
            "🍔 Order complete! Thanks for choosing QuikEats 🙌 Share a pic in #vouch 📸 and @ a provider to earn rewards 🎯",
            "⚡ QuikEats delivered! 🚗💨 Snap your meal 📸 in #vouch and @ a provider to build points 🎯 — free bites coming soon 🆓",
            "🔥 You’re awesome! Thanks for ordering QuikEats 😋 Share in #vouch 📸 + @ a provider for points 🎯",
            "🥳 Big thanks for your QuikEats order! Tap #vouch with a photo 📸 and @ a provider to earn 🎯",
            "💥 Thanks for rolling with QuikEats! 🍕 Show off in #vouch 📸 — don’t forget to @ a provider for points 🎯",
            "🍟 Thanks for ordering! Post in #vouch 📸 + @ a provider to collect points 🎯 — FREE order soon 🆓",
            "✨ QuikEats appreciates you! Share your feast 📸 in #vouch and @ a provider — level up rewards 🎯",
            "🚀 Order confirmed & delivered! Drop a photo in #vouch 📸, @ a provider, and climb to freebies 🆓",
            "💚 Thanks from QuikEats! Share in #vouch 📸 + @ a provider to keep stacking 🎯",
            "📦 Your QuikEats arrived! Post a pic in #vouch 📸 and @ a provider — points incoming 🎯",
            "🍔 Enjoy! When you can, snap a pic 📸 in #vouch and @ a provider for rewards 🎯",
            "🙌 Appreciate you! #vouch with a photo 📸 and @ a provider to earn 🎯 — free meal goal 🆓",
            "🔥 That meal looks good already 😮‍💨 Post in #vouch 📸 + @ a provider — points stack 🎯",
            "🍕 Thanks for choosing QuikEats! Toss a pic in #vouch 📸 and @ a provider for points 🎯",
            "💫 Much love! Share your order in #vouch 📸, remember to @ a provider — win rewards 🎯",
            "🎊 Order in! Drop a quick pic 📸 to #vouch and @ a provider — keep stacking 🎯",
            "🍜 Thanks again! #vouch 📸 + @ provider = points 🎯 — free meal soon 🆓",
            "⚡ Speedy eats, speedy thanks! Post in #vouch 📸 and @ a provider to earn 🎯",
            "🥤 Appreciate the support! Share in #vouch 📸 and tag a provider @ to collect 🎯",
            "💎 You rock! Show it off in #vouch 📸 and @ a provider — rewards add up 🎯",
            "🍩 Sweet! Post your order 📸 in #vouch — don’t forget @ a provider 🎯",
            "🌟 Thanks for the order! Snap 📸 to #vouch, @ a provider — points time 🎯",
            "🍱 Much appreciated! Share in #vouch 📸 and @provider — climb to FREE 🆓",
            "🍔 QuikEats thanks you! #vouch 📸 + @ provider — rewards unlocked 🎯",
            "🚗 Delivered! Post a quick #vouch 📸 + @ provider — score points 🎯",
            "🥡 Thanks! #vouch 📸 and @ a provider — stacking toward free 🆓",
            "🍟 Love to see it! Drop #vouch 📸 + @ provider — rewards incoming 🎯",
            "🎯 Don’t forget: #vouch 📸 + @ provider = points → FREE order 🆓"
        ],
        "index": 0
    })

# Ensure barred users config exists and seed default barred IDs
ensure_barred_users_config_exists()
for default_barred_id in DEFAULT_BARRED_USERS:
    add_barred_user(default_barred_id)

# Register global check to block barred users from ALL slash commands
bot.tree.add_check(global_barred_user_check)
print("✅ Registered global barred user check for command tree")

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
    
    try:
        # Find the user by name or mention
        target_user = None

        # If it's a mention (starts with <@), try to extract the user ID
        if customer.startswith('<@') and customer.endswith('>'):
            try:
                # Extract user ID from mention
                user_id = int(customer.strip('<@!&>'))
                target_user = interaction.guild.get_member(user_id)
            except (ValueError, AttributeError):
                pass
        else:
            # Look up by display name or username
            for member in interaction.guild.members:
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
                (c for c in interaction.guild.text_channels if c.name == 'vouch-📸'),
                None
            )
            if vouch_channel is None:
                vouch_channel = next(
                    (c for c in interaction.guild.text_channels if 'vouch' in c.name.lower()),
                    None
                )
            # Exact name first, then any channel containing 'casino' (ignoring suits)
            casino_channel = next(
                (c for c in interaction.guild.text_channels if c.name == '♠♥casino♣♦'),
                None
            )
            if casino_channel is None:
                casino_channel = next(
                    (c for c in interaction.guild.text_channels if 'casino' in c.name.lower()),
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
        # Find ALL channels with "open" or "closed" in the name and rename them
        renamed_channels = []
        for channel in interaction.guild.channels:
            if "open" in channel.name.lower() or "closed" in channel.name.lower():
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
        
        # Remove any deny permissions for @everyone
        if overwrites.view_channel is False:
            overwrites.view_channel = None
            await order_channel.set_permissions(everyone_role, overwrite=overwrites)
        
        await interaction.edit_original_response(content="✅ Business is now **OPEN**! 🟢\n- All status channels renamed to 🟢-open\n- Order-here channel is now public")
        
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
        # Find ALL channels with "open" or "closed" in the name and rename them
        renamed_channels = []
        for channel in interaction.guild.channels:
            if "open" in channel.name.lower() or "closed" in channel.name.lower():
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
        
        # Make order-here channel private (deny @everyone view)
        everyone_role = interaction.guild.default_role
        await order_channel.set_permissions(everyone_role, view_channel=False)
        
        await interaction.edit_original_response(content="✅ Business is now **CLOSED**! 🔴\n- All status channels renamed to 🔴-closed\n- Order-here channel is now private")
        
    except discord.Forbidden:
        await interaction.edit_original_response(content="❌ I don't have permission to modify channels!")
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Error: {str(e)}")

# Dynamic command handler for custom commands
@bot.event
async def on_interaction(interaction):
    # LAYER 2 DEFENSE: Immediately ignore ALL interactions from barred users
    # This is checked before any other processing as a safety net
    try:
        if interaction.user and is_user_barred(interaction.user.id):
            command_info = getattr(interaction, "data", {}) or {}
            command_name = command_info.get('name', 'unknown')
            print(f"🚫 [Layer 2] Silently ignoring interaction '{command_name}' from barred user {interaction.user.id}")
            return  # Exit immediately without acknowledging
    except Exception as e:
        print(f"⚠️ Error checking barred status in on_interaction: {e}")
    
    if interaction.type == discord.InteractionType.application_command:
        command_name = interaction.data['name']

        # Check if it's a custom command
        custom_commands = load_custom_commands()
        if command_name in custom_commands:
            response = custom_commands[command_name]
            await interaction.response.send_message(response)
            return

    # Let other interactions pass through to default handler
    await bot.process_application_commands(interaction)

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
