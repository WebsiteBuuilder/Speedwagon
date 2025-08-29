import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Data storage for custom commands only
COMMANDS_FILE = 'custom_commands.json'

# Simple HTTP server for health checks
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress access logs for cleaner output
        pass

def start_health_server():
    """Start health server in background thread"""
    try:
        # Use Railway's PORT environment variable
        port = int(os.getenv('PORT', 8080))
        print(f"Starting health server on port {port}")
        
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        print(f"Health server created successfully")
        
        # Start server in background
        def run_server():
            try:
                server.serve_forever()
            except Exception as e:
                print(f"Health server error: {e}")
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        # Test if server is responding
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"✅ Health server is responding on port {port}")
            return True
        else:
            print(f"❌ Health server not responding on port {port}")
            return False
            
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

# Initialize custom commands file
if not os.path.exists(COMMANDS_FILE):
    save_custom_commands({})

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
    embed = discord.Embed(
        title="💳 Payment Methods",
        description="Here are our accepted payment methods:",
        color=0x0099ff
    )
    
    embed.add_field(
        name="🍎 Apple Pay",
        value="[Add to Apple Wallet](https://example.com/apple-wallet)",
        inline=False
    )
    embed.add_field(
        name="💸 Zelle",
        value="[Send to Zelle](https://example.com/zelle)",
        inline=False
    )
    embed.add_field(
        name="📱 Cash App",
        value="[Send via Cash App](https://example.com/cashapp)",
        inline=False
    )
    embed.add_field(
        name="💳 Credit/Debit",
        value="[Pay Online](https://example.com/credit)",
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

@bot.tree.command(name="open", description="Open the business - rename status channel and make order channel public (Provider role only)")
async def open_business(interaction: discord.Interaction):
    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    try:
        # Find the status channel
        status_channel = discord.utils.get(interaction.guild.channels, name="status")
        if not status_channel:
            await interaction.response.send_message("❌ Could not find #status channel!", ephemeral=True)
            return
        
        # Find the order channel
        order_channel = discord.utils.get(interaction.guild.channels, name="orderhere")
        if not order_channel:
            await interaction.response.send_message("❌ Could not find #orderhere channel!", ephemeral=True)
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
        
        await interaction.response.send_message("✅ Business is now **OPEN**! 🟢\n- Status channel renamed to 🟢-open\n- Order channel is now public", ephemeral=True)
        
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to modify channels!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="close", description="Close the business - rename status channel and make order channel private (Provider role only)")
async def close_business(interaction: discord.Interaction):
    # Check if user has Provider role
    provider_role = discord.utils.get(interaction.guild.roles, name="Provider")
    if not provider_role or provider_role not in interaction.user.roles:
        await interaction.response.send_message("❌ You need the Provider role to use this command!", ephemeral=True)
        return
    
    try:
        # Find the status channel
        status_channel = discord.utils.get(interaction.guild.channels, name="status")
        if not status_channel:
            await interaction.response.send_message("❌ Could not find #status channel!", ephemeral=True)
            return
        
        # Find the order channel
        order_channel = discord.utils.get(interaction.guild.channels, name="orderhere")
        if not order_channel:
            await interaction.response.send_message("❌ Could not find #orderhere channel!", ephemeral=True)
            return
        
        # Rename status channel to show CLOSED
        await status_channel.edit(name="🔴-closed")
        
        # Make order channel private (deny @everyone view)
        everyone_role = interaction.guild.default_role
        await order_channel.set_permissions(everyone_role, view_channel=False)
        
        await interaction.response.send_message("✅ Business is now **CLOSED**! 🔴\n- Status channel renamed to 🔴-closed\n- Order channel is now private", ephemeral=True)
        
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to modify channels!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

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
