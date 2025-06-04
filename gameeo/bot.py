import discord
from discord.ext import commands
import random
from typing import List
import dashboard
from dotenv import load_dotenv
import os
import requests

# Intents are required for bots to function properly
intents = discord.Intents.default()
intents.message_content = True

# Set up bot to respond to @mention for chat, and ! for commands
from discord.ext.commands import when_mentioned_or

bot = commands.Bot(command_prefix=when_mentioned_or('!'), intents=intents)

# Placeholder for player and battle data
players = {}
battles = {}

class Skill:
    def __init__(self, name, description, effect_func):
        self.name = name
        self.description = description
        self.effect_func = effect_func  # Function to apply the skill effect

    def use(self, user, target, ctx=None):
        return self.effect_func(user, target, ctx)

    def display(self):
        return f"**{self.name}**: {self.description}"

# Example skill effect functions
def fire_breath(user, target, ctx):
    dmg = int(user['atk'] * 1.5)
    target['hp'] -= dmg
    return f"{user['name']} breathes fire for {dmg} damage!"

def tail_whip(user, target, ctx):
    dmg = int(user['atk'] * 0.8)
    target['hp'] -= dmg
    target['status'] = 'Stunned'
    return f"{user['name']} uses Tail Whip for {dmg} damage and stuns the target!"

def rainbow_blast(user, target, ctx):
    dmg = user['atk']
    target['hp'] -= dmg
    return f"{user['name']} blasts a rainbow for {dmg} damage!"

def heal(user, target, ctx):
    heal_amt = 20
    user['hp'] = min(user['hp'] + heal_amt,  user.get('max_hp', 100))
    return f"{user['name']} heals for {heal_amt} HP!"

def laser_beam(user, target, ctx):
    dmg = int(user['atk'] * 1.2)
    target['hp'] -= dmg
    return f"{user['name']} fires a laser beam for {dmg} damage!"

def mind_control(user, target, ctx):
    target['status'] = 'Confused'
    return f"{user['name']} uses Mind Control! The target is confused."

# Define skills
SKILLS = {
    'Fire Breath': Skill('Fire Breath', 'Deal heavy fire damage.', fire_breath),
    'Tail Whip': Skill('Tail Whip', 'Deal damage and stun the target.', tail_whip),
    'Rainbow Blast': Skill('Rainbow Blast', 'Deal magical rainbow damage.', rainbow_blast),
    'Heal': Skill('Heal', 'Restore HP to yourself.', heal),
    'Laser Beam': Skill('Laser Beam', 'Deal high energy damage.', laser_beam),
    'Mind Control': Skill('Mind Control', 'Confuse the target.', mind_control),
}

class Character:
    def __init__(self, emoji, name, hp, atk, skills):
        self.emoji = emoji
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.skills = skills  # List of skill names
        self.upgrades = []
        self.status = None

    def to_dict(self):
        return {
            'emoji': self.emoji,
            'name': self.name,
            'hp': self.hp,
            'max_hp': self.max_hp,
            'atk': self.atk,
            'skills': self.skills,
            'upgrades': self.upgrades,
            'status': self.status,
        }

    def display(self):
        return f"{self.emoji} **{self.name}** | HP: {self.hp}/{self.max_hp} | ATK: {self.atk} | Skills: {', '.join(self.skills)}"

# Updated character data using Character class
CHARACTERS = {
    '🐉': Character('🐉', 'Dragon', 100, 20, ['Fire Breath', 'Tail Whip']),
    '🦄': Character('🦄', 'Unicorn', 90, 18, ['Rainbow Blast', 'Heal']),
    '👾': Character('👾', 'Alien', 80, 22, ['Laser Beam', 'Mind Control']),
}

# Add a dictionary to store custom characters per user
custom_characters = {}  # user_id: {emoji: Character, ...}

def sync_dashboard_data():
    # Sync characters and bosses to dashboard
    dashboard.DASHBOARD_DATA['characters'] = [
        { 'emoji': c.emoji, 'name': c.name, 'hp': c.max_hp, 'atk': c.atk, 'skills': c.skills }
        for c in CHARACTERS.values()
    ]
    # Add custom characters
    for user_chars in custom_characters.values():
        for c in user_chars.values():
            dashboard.DASHBOARD_DATA['characters'].append({
                'emoji': c.emoji, 'name': c.name, 'hp': c.max_hp, 'atk': c.atk, 'skills': c.skills
            })
    # Add admin characters from dashboard
    for c in dashboard.DASHBOARD_DATA.get('characters', []):
        if c['emoji'] not in CHARACTERS:
            CHARACTERS[c['emoji']] = Character(c['emoji'], c['name'], c['hp'], c['atk'], c['skills'])
    # Sync bosses
    dashboard.DASHBOARD_DATA['bosses'] = [
        { 'emoji': b['emoji'], 'name': b['name'], 'hp': b['hp'], 'atk': b['atk'], 'skills': b['skills'] }
        for b in dashboard.DASHBOARD_DATA.get('bosses', [])
    ]
    for b in dashboard.DASHBOARD_DATA['bosses']:
        if b['name'].lower() not in BOSSES:
            BOSSES[b['name'].lower()] = b

# Start dashboard on bot startup
@bot.event
async def on_ready():
    dashboard.start_dashboard_thread()
    sync_dashboard_data()
    print(f'Logged in as {bot.user}')

@bot.command()
async def characters(ctx):
    """List all available emoji-based characters and their stats."""
    msg = '**Available Characters:**\n'
    for char in CHARACTERS.values():
        msg += char.display() + '\n'
    await ctx.send(msg)

@bot.command()
async def create_character(ctx, emoji: str, name: str, hp: int, atk: int, *, skills: str):
    """Create a custom character. Usage: !create_character <emoji> <name> <hp> <atk> <skill1,skill2,...> (max 2 per user, any emoji allowed)"""
    user_id = ctx.author.id
    # Limit to 2 custom characters per user
    if user_id not in custom_characters:
        custom_characters[user_id] = {}
    if len(custom_characters[user_id]) >= 2:
        await ctx.send('You can only have 2 custom characters!')
        return
    # Prevent duplicate emoji across all users and default characters
    if emoji in CHARACTERS or any(emoji in chars for chars in custom_characters.values()):
        await ctx.send('This emoji is already taken by another character!')
        return
    # Accept any emoji (no restriction), but check for valid skills
    skill_list = [s.strip() for s in skills.split(',') if s.strip() in SKILLS]
    if not skill_list:
        await ctx.send('You must provide at least one valid skill (comma separated, e.g. Fire Breath,Heal).')
        return
    char = Character(emoji, name, hp, atk, skill_list)
    custom_characters[user_id][emoji] = char
    await ctx.send(f'{ctx.author.mention} created custom character {name} {emoji}!')

@bot.command()
async def my_characters(ctx):
    """List your custom characters."""
    user_id = ctx.author.id
    chars = custom_characters.get(user_id, {})
    if not chars:
        await ctx.send('You have no custom characters.')
        return
    msg = '**Your Custom Characters:**\n'
    for char in chars.values():
        msg += char.display() + '\n'
    await ctx.send(msg)

@bot.command()
async def join(ctx, emoji: str):
    """Join the arena with a character (emoji)."""
    user_id = ctx.author.id
    # Check default and custom characters
    char = CHARACTERS.get(emoji)
    if not char:
        char = custom_characters.get(user_id, {}).get(emoji)
    if not char:
        await ctx.send('Invalid character emoji! Use !characters or !my_characters to see options.')
        return
    # Create a fresh copy for the player
    players[user_id] = char.to_dict()
    await ctx.send(f'{ctx.author.mention} joined as {char.name} {char.emoji}!')

@bot.command()
async def battle(ctx, opponent: discord.Member):
    """Start a PvP battle with another player."""
    if ctx.author.id not in players or opponent.id not in players:
        await ctx.send('Both players must join first using !join <emoji>.')
        return
    battle_id = f'{ctx.author.id}-{opponent.id}'
    battles[battle_id] = {
        'players': [ctx.author.id, opponent.id],
        'turn': 0,
        'log': [],
    }
    await ctx.send(f'Battle started between {ctx.author.mention} and {opponent.mention}!')
    await show_status(ctx, battle_id)

# Helper to create a battle
async def start_battle(ctx, player_ids: List[int], boss: dict = None):
    battle_id = '-'.join(map(str, player_ids))
    battles[battle_id] = {
        'players': player_ids,
        'turn': 0,
        'log': [],
        'boss': boss,
    }
    if boss:
        await ctx.send(f"Boss battle started! Boss: {boss['name']} {boss['emoji']} vs. " + ', '.join(ctx.guild.get_member(pid).mention for pid in player_ids))
    else:
        await ctx.send(f"Battle started between: " + ', '.join(ctx.guild.get_member(pid).mention for pid in player_ids))
    await show_status(ctx, battle_id)

@bot.command()
async def pvp(ctx, *members: discord.Member):
    """Start a custom PvP battle. Usage: !pvp @user1 @user2 ... (2-4 players)"""
    player_ids = [ctx.author.id] + [m.id for m in members]
    if not (2 <= len(player_ids) <= 4):
        await ctx.send('PvP battles must have 2-4 players.')
        return
    for pid in player_ids:
        if pid not in players:
            await ctx.send(f"{ctx.guild.get_member(pid).mention} must join first using !join <emoji>.")
            return
    await start_battle(ctx, player_ids)

@bot.command()
async def team_battle(ctx, *members: discord.Member):
    """Start a team battle. Usage: !team_battle @user1 @user2 ... (total 4, 6, or 8 players for 2v2, 3v3, 4v4)"""
    player_ids = [ctx.author.id] + [m.id for m in members]
    if len(player_ids) not in (4, 6, 8):
        await ctx.send('Team battles must have 4 (2v2), 6 (3v3), or 8 (4v4) players.')
        return
    for pid in player_ids:
        if pid not in players:
            await ctx.send(f"{ctx.guild.get_member(pid).mention} must join first using !join <emoji>.")
            return
    await start_battle(ctx, player_ids)

# Boss system
BOSSES = {
    'slime': {'emoji': '🟢', 'name': 'Giant Slime', 'hp': 200, 'atk': 15, 'skills': ['Tail Whip']},
    'dragon': {'emoji': '🐲', 'name': 'Ancient Dragon', 'hp': 400, 'atk': 30, 'skills': ['Fire Breath', 'Tail Whip']},
}

@bot.command()
async def boss_battle(ctx, boss_name: str, *members: discord.Member):
    """Start a boss fight. Usage: !boss_battle <boss> @user1 @user2 ... (1-4 players)"""
    boss = BOSSES.get(boss_name.lower())
    if not boss:
        await ctx.send('Boss not found! Available: ' + ', '.join(BOSSES.keys()))
        return
    player_ids = [ctx.author.id] + [m.id for m in members]
    if not (1 <= len(player_ids) <= 4):
        await ctx.send('Boss battles must have 1-4 players.')
        return
    for pid in player_ids:
        if pid not in players:
            await ctx.send(f"{ctx.guild.get_member(pid).mention} must join first using !join <emoji>.")
            return
    await start_battle(ctx, player_ids, boss)

# Update show_status to display boss if present
async def show_status(ctx, battle_id):
    battle = battles[battle_id]
    msg = ''
    for pid in battle['players']:
        p = players[pid]
        msg += f"{ctx.guild.get_member(pid).mention} ({p['emoji']}) HP: {p['hp']}\n"
    if battle.get('boss'):
        boss = battle['boss']
        msg += f"**Boss** {boss['name']} {boss['emoji']} HP: {boss['hp']}\n"
    await ctx.send(msg)

@bot.command()
async def attack(ctx):
    """Attack your opponent in a battle."""
    # Find the battle the user is in
    battle_id = next((bid for bid, b in battles.items() if ctx.author.id in b['players']), None)
    if not battle_id:
        await ctx.send('You are not in a battle!')
        return
    battle = battles[battle_id]
    attacker = ctx.author.id
    defender = [pid for pid in battle['players'] if pid != attacker][0]
    # Simple turn logic
    if battle['players'][battle['turn'] % 2] != attacker:
        await ctx.send('It is not your turn!')
        return
    # Calculate damage (with crit chance)
    crit = random.random() < 0.2
    dmg = players[attacker]['atk'] * (2 if crit else 1)
    players[defender]['hp'] -= dmg
    battle['log'].append(f"{ctx.author.display_name} attacked for {dmg}{' (CRIT!)' if crit else ''}")
    await ctx.send(f"{ctx.author.mention} attacks for {dmg} damage!{' **CRITICAL HIT!**' if crit else ''}")
    # Check for win
    if players[defender]['hp'] <= 0:
        await ctx.send(f"{ctx.guild.get_member(defender).mention} has been defeated!")
        del battles[battle_id]
        return
    battle['turn'] += 1
    await show_status(ctx, battle_id)

@bot.command()
async def skills(ctx, emoji: str):
    """List all skills for a given character emoji."""
    if emoji not in CHARACTERS:
        await ctx.send('Invalid character emoji! Use !characters to see options.')
        return
    char = CHARACTERS[emoji]
    msg = f"**Skills for {char.name} {char.emoji}:**\n"
    for skill_name in char.skills:
        skill = SKILLS.get(skill_name)
        if skill:
            msg += skill.display() + '\n'
        else:
            msg += f"{skill_name}: No description.\n"
    await ctx.send(msg)

@bot.command()
async def use_skill(ctx, skill_name: str):
    """Use a skill in your current battle. Usage: !use_skill <skill name>"""
    # Find the battle the user is in
    battle_id = next((bid for bid, b in battles.items() if ctx.author.id in b['players']), None)
    if not battle_id:
        await ctx.send('You are not in a battle!')
        return
    battle = battles[battle_id]
    attacker = ctx.author.id
    defender = [pid for pid in battle['players'] if pid != attacker][0]
    # Turn check
    if battle['players'][battle['turn'] % 2] != attacker:
        await ctx.send('It is not your turn!')
        return
    # Check if user has the skill
    user_skills = players[attacker]['skills']
    if skill_name not in user_skills:
        await ctx.send('You do not have that skill!')
        return
    # Get the skill object
    skill = SKILLS.get(skill_name)
    if not skill:
        await ctx.send('Skill not found!')
        return
    # Check for status effects (e.g., stunned)
    if players[attacker].get('status') == 'Stunned':
        players[attacker]['status'] = None  # Remove stun after missing turn
        await ctx.send(f"{ctx.author.mention} is stunned and cannot act this turn!")
        battle['turn'] += 1
        await show_status(ctx, battle_id)
        return
    # Use the skill
    result = skill.use(players[attacker], players[defender], ctx)
    battle['log'].append(f"{ctx.author.display_name} used {skill_name}!")
    await ctx.send(f"{ctx.author.mention} uses **{skill_name}**! {result}")
    # Check for win
    if players[defender]['hp'] <= 0:
        await ctx.send(f"{ctx.guild.get_member(defender).mention} has been defeated!")
        del battles[battle_id]
        return
    battle['turn'] += 1
    await show_status(ctx, battle_id)

def ask_groq_ai(prompt, api_key=None):
    """Send a prompt to Groq AI API and return the response text."""
    api_key = api_key or os.environ.get('GROQ_API_KEY')
    if not api_key:
        return 'Groq API key not set.'
    url = 'https://api.groq.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    data = {
        'model': 'llama3-70b-8192',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 256,
        'temperature': 0.7
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f'Groq API error: {e}'

@bot.command()
async def chat(ctx, *, message: str):
    """Chat with Groq AI (Llama 3). Usage: !chat <message>"""
    await ctx.trigger_typing()
    reply = ask_groq_ai(message)
    await ctx.send(reply)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # If the bot is mentioned and it's not a command, treat as chat
    if bot.user in message.mentions and not message.content.strip().startswith('!'):
        prompt = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
        if prompt:
            await message.channel.trigger_typing()
            reply = ask_groq_ai(prompt)
            await message.reply(reply)
        return
    await bot.process_commands(message)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# To run the bot, replace 'YOUR_BOT_TOKEN' with your Discord bot token
if __name__ == '__main__':
    bot.run(os.environ.get('DISCORD_BOT_TOKEN'))
