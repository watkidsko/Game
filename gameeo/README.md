# Discord Battle Arena Bot & Dashboard

A feature-rich Discord bot for a turn-based Battle Arena game with a live dashboard and admin panel.

## Features
- Emoji-based custom characters (create your own, up to 2 per user)
- PvP, team battles (2v2, 3v3, 4v4), and boss fights
- Turn-based combat with skills, status effects, and critical hits
- Adaptive AI (Groq AI integration for chat)
- Spectator mode, tournaments, and leaderboards (expandable)
- Shops, crafting, and in-game economy (expandable)
- Dynamic game grid, random events, and more (expandable)
- Web dashboard to view stats, manage characters/bosses, and see API keys
- Admin panel for adding admin characters and bosses

## Setup
1. **Clone the repo and install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or manually: pip install discord.py flask python-dotenv requests
   ```

2. **Create a `.env` file in the `gameeo/` folder:**
   ```env
   DISCORD_BOT_TOKEN=your_discord_token_here
   GROQ_API_KEY=your_groq_api_key_here
   DASHBOARD_ADMIN_PASS=your_dashboard_password_here
   # (Optional) Add other API keys as needed
   ```

3. **Run the bot:**
   ```bash
   python3 gameeo/bot.py
   ```
   The dashboard will be available at [http://localhost:5000](http://localhost:5000)

## Usage
- **!create_character <emoji> <name> <hp> <atk> <skill1,skill2,...>**  
  Create a custom character (max 2 per user, any emoji allowed)
- **!my_characters**  
  List your custom characters
- **!join <emoji>**  
  Join the arena with a character (default or custom)
- **!battle @user**  
  Start a PvP battle
- **!pvp @user1 @user2 ...**  
  Start a custom PvP battle (2-4 players)
- **!team_battle @user1 ...**  
  Start a team battle (4, 6, or 8 players)
- **!boss_battle <boss> @user1 ...**  
  Start a boss fight (1-4 players)
- **!attack**  
  Attack your opponent
- **!use_skill <skill name>**  
  Use a skill in battle
- **!skills <emoji>**  
  List skills for a character
- **@BotName <message>**  
  Chat with Groq AI (Llama 3)
- **!chat <message>**  
  Chat with Groq AI (Llama 3)

## Dashboard
- Visit [http://localhost:5000](http://localhost:5000) to view stats, characters, bosses, and API keys
- Admin panel at `/admin` (password from `.env`) to add admin characters and bosses

## Customization
- Add new skills in `bot.py` (see `SKILLS` dict and effect functions)
- Add new bosses in `BOSSES` dict or via the dashboard admin panel
- Expand the dashboard and bot features as needed!

---
MIT License
