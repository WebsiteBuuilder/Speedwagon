# Speedwagon Discord Bot 🚗

A Discord bot for managing customer interactions, vouch points, and custom commands for your business.

## Features

### 🎯 Core Commands
- **`/vouch`** - Thank customers and award vouch points with food pics
- **`/neck`** - Display payment method links (Apple Pay, Zelle, Cash App, etc.)
- **`/points`** - Check your current vouch points
- **`/editcommand`** - Create/edit custom commands (Provider role only)

### 🔧 Custom Commands System
- Providers can create unlimited custom commands
- Commands are stored persistently
- Easy to manage and update

### 🏆 Vouch Points System
- Random point rewards (5-15 points per vouch)
- Persistent storage of customer data
- Track vouch history and providers
- Points can be used for giveaways and rewards

## Setup

### 1. Prerequisites
- Python 3.8+
- Discord Bot Token
- Server with "Provider" role

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd Speedwagon

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env_example.txt .env

# Edit .env with your bot token
# DISCORD_TOKEN=your_actual_token_here
```

### 3. Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to Bot section
4. Copy the token and add it to `.env`
5. Enable required intents:
   - Message Content Intent
   - Server Members Intent
6. Invite bot to your server with proper permissions

### 4. Server Setup
1. Create a role called "Provider" in your Discord server
2. Assign this role to staff who should manage custom commands
3. Ensure bot has permissions to:
   - Send Messages
   - Use Slash Commands
   - Attach Files
   - Embed Links

### 5. Run the Bot
```bash
python main.py
```

## Railway Deployment

### 1. Connect to Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Add environment variables
railway variables set DISCORD_TOKEN=your_token_here
```

### 2. Deploy
```bash
railway up
```

## Usage Examples

### Creating Custom Commands
```
/editcommand command_name:menu response:Check out our latest menu at https://example.com/menu
```

### Vouching a Customer
```
/vouch customer:@username food_pic:[upload food image]
```

### Checking Points
```
/points
```

## File Structure
```
Speedwagon/
├── main.py              # Main bot file
├── requirements.txt     # Python dependencies
├── env_example.txt     # Environment variables template
├── README.md           # This file
├── custom_commands.json # Custom commands storage
└── vouch_data.json     # Vouch points data
```

## Customization

### Payment Links
Edit the `/neck` command in `main.py` to update your actual payment URLs:
```python
embed.add_field(
    name="🍎 Apple Pay",
    value="[Add to Apple Wallet](https://your-actual-url.com)",
    inline=False
)
```

### Vouch Points Range
Modify the points range in the vouch command:
```python
points_earned = random.randint(5, 15)  # Change min/max values
```

## Support

For issues or questions:
1. Check the bot logs for error messages
2. Ensure all required roles and permissions are set
3. Verify your bot token is correct
4. Make sure the bot has proper server permissions

## License

This project is open source and available under the MIT License.

 fo fs s