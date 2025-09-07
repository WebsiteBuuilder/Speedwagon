import discord
from discord import app_commands
from discord.ext import commands
import json
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

# Data storage files
COMMANDS_FILE = 'custom_commands.json'
LINKS_FILE = 'payment_links.json'

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
            "apple_pay": "",
            "zelle": "",
            "cashapp": "",
            "credit": ""
        }

# Save payment links
def save_payment_links(links_dict):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links_dict, f, indent=2)

# Initialize data files
if not os.path.exists(COMMANDS_FILE):
    save_custom_commands({})

if not os.path.exists(LINKS_FILE):
    save_payment_links({
        "apple_pay": "",
        "zelle": "",
        "cashapp": "",
        "credit": ""
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
    links = load_payment_links()
    
    embed = discord.Embed(
        title="💳 Payment Methods",
        description="Here are our accepted payment methods:",
        color=0x0099ff
    )
    
    # Add fields only if links are set
    if links.get("apple_pay"):
        embed.add_field(
            name="🍎 Apple Pay",
            value=f"[Add to Apple Wallet]({links['apple_pay']})",
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
            name="📱 Cash App",
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
    payment_method="Which payment method to set (apple_pay, zelle, cashapp, credit)",
    url="The URL/link for this payment method"
)
@app_commands.choices(payment_method=[
    app_commands.Choice(name="Apple Pay", value="apple_pay"),
    app_commands.Choice(name="Zelle", value="zelle"),
    app_commands.Choice(name="Cash App", value="cashapp"),
    app_commands.Choice(name="Credit/Debit", value="credit")
])
async def setlink(interaction: discord.Interaction, payment_method: str, url: str):
    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    # Load existing links
    links = load_payment_links()
    
    # Update the specified payment method
    links[payment_method] = url
    save_payment_links(links)
    
    # Get display name for payment method
    method_names = {
        "apple_pay": "Apple Pay",
        "zelle": "Zelle", 
        "cashapp": "Cash App",
        "credit": "Credit/Debit"
    }
    
    await interaction.response.send_message(
        f"✅ {method_names[payment_method]} link has been set!\n`{url}`", 
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
    links = load_payment_links()
    
    embed = discord.Embed(
        title="🔗 Current Payment Links",
        description="Here are the currently set payment links:",
        color=0x00ff00
    )
    
    method_names = {
        "apple_pay": "🍎 Apple Pay",
        "zelle": "💸 Zelle",
        "cashapp": "📱 Cash App", 
        "credit": "💳 Credit/Debit"
    }
    
    for method, name in method_names.items():
        link = links.get(method, "")
        if link:
            embed.add_field(name=name, value=f"`{link}`", inline=False)
        else:
            embed.add_field(name=name, value="*Not set*", inline=False)
    
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
        # Find or create the status channel
        status_channel = None
        for channel in interaction.guild.channels:
            if channel.name.startswith("🟢-") or channel.name.startswith("🔴-") or channel.name == "status":
                status_channel = channel
                break
        
        # If no status channel exists, create one
        if not status_channel:
            status_channel = await interaction.guild.create_text_channel("🟢-open")
        
        # Find the order channel (look for order-here in name)
        order_channel = None
        for channel in interaction.guild.channels:
            if "order-here" in channel.name.lower() or "order" in channel.name.lower():
                order_channel = channel
                break
        
        if not order_channel:
            await interaction.edit_original_response(content="❌ Could not find order channel! Please create a channel with 'order' in the name.")
            return
        
        # Rename status channel to show OPEN
        await status_channel.edit(name="🟢-open")
        
        # Make order channel public (remove @everyone overwrite if it exists)
        everyone_role = interaction.guild.default_role
        overwrites = order_channel.overwrites_for(everyone_role)
        
        # Remove any deny permissions for @everyone
        if overwrites.view_channel is False:
            overwrites.view_channel = None
            await order_channel.set_permissions(everyone_role, overwrite=overwrites)
        
        await interaction.edit_original_response(content="✅ Business is now **OPEN**! 🟢\n- Status channel renamed to 🟢-open\n- Order channel is now public")
        
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
        # Find or create the status channel
        status_channel = None
        for channel in interaction.guild.channels:
            if channel.name.startswith("🟢-") or channel.name.startswith("🔴-") or channel.name == "status":
                status_channel = channel
                break
        
        # If no status channel exists, create one
        if not status_channel:
            status_channel = await interaction.guild.create_text_channel("🔴-closed")
        
        # Find the order channel (look for order-here in name)
        order_channel = None
        for channel in interaction.guild.channels:
            if "order-here" in channel.name.lower() or "order" in channel.name.lower():
                order_channel = channel
                break
        
        if not order_channel:
            await interaction.edit_original_response(content="❌ Could not find order channel! Please create a channel with 'order' in the name.")
            return
        
        # Rename status channel to show CLOSED
        await status_channel.edit(name="🔴-closed")
        
        # Make order channel private (deny @everyone view)
        everyone_role = interaction.guild.default_role
        await order_channel.set_permissions(everyone_role, view_channel=False)
        
        await interaction.edit_original_response(content="✅ Business is now **CLOSED**! 🔴\n- Status channel renamed to 🔴-closed\n- Order channel is now private")
        
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
