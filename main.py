import discord
from discord import app_commands
from discord.ext import commands
import json
import shutil
import os
from dotenv import load_dotenv
import threading
import socket
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

# Simple socket-based health server
def start_health_server():
    """Start simple health server using sockets"""
    try:
        port = int(os.getenv('PORT', 8080))
        print(f"Starting health server on port {port}")
        
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', port))
        sock.listen(1)
        
        print(f"✅ Health server listening on port {port}")
        
        # Start server in background
        def run_server():
            try:
                while True:
                    conn, addr = sock.accept()
                    data = conn.recv(1024).decode()
                    if 'GET /health' in data:
                        response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
                        conn.send(response.encode())
                    else:
                        response = "HTTP/1.1 404 Not Found\r\n\r\n"
                        conn.send(response.encode())
                    conn.close()
            except Exception as e:
                print(f"Health server error: {e}")
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        return True
            
    except Exception as e:
        print(f"❌ Failed to start health server: {e}")
        return False

# Load custom commands
def load_custom_commands():
    try:
        with open(COMMANDS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

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
            return json.load(f)
    except FileNotFoundError:
        return {
            "messages": [
                "🚀 Thanks for ordering with QuikEats! 🍔✨ Don’t forget to snap a pic 📸 and drop it in #vouch 🔥 Make sure to @ a provider to earn points 🎯 … stack them up & redeem for a FREE order 🆓🍕🙌"
            ],
            "index": 0
        }

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
    customer="The customer to thank (mention them with @)"
)
async def enjoy(interaction: discord.Interaction, customer: discord.Member):
    try:
        # Load messages and pick current one
        enjoy_data = load_enjoy_messages()
        messages = enjoy_data.get("messages", [])
        index = enjoy_data.get("index", 0)
        if not messages:
            await interaction.response.send_message("⚠️ No enjoy messages configured.")
            return

        # Get the raw message template
        message_template = messages[index % len(messages)]

        # Replace (user) placeholder with the customer's mention
        personalized_message = message_template.replace("(user)", customer.mention)

        # Send the personalized message
        await interaction.response.send_message(personalized_message)

        # Advance the index and save
        enjoy_data["index"] = (index + 1) % len(messages)
        save_enjoy_messages(enjoy_data)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error sending message: {e}", ephemeral=True)

@bot.tree.command(name="listcommands", description="List all custom commands")
async def listcommands(interaction: discord.Interaction):
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
    if interaction.type == discord.InteractionType.application_command:
        command_name = interaction.data['name']
        
        # Check if it's a custom command
        custom_commands = load_custom_commands()
        if command_name in custom_commands:
            response = custom_commands[command_name]
            await interaction.response.send_message(response)
            return
    
    # Let other interactions pass through
    pass

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore command not found errors
    else:
        print(f"Error: {error}")

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
    
    # Start health check server
    print("Starting health check server...")
    health_ready = start_health_server()
    
    if health_ready:
        print("✅ Health check server is ready")
    else:
        print("⚠️ Health check server failed, but continuing...")
    
    # Give health server a moment to fully start
    time.sleep(3)
    
    # Start the bot
    print("Connecting to Discord...")
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        exit(1)
