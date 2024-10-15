import discord
from discord.ext import commands
import os

# Set your bot's command prefix and the intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

# Create a bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Event to indicate the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

# This event triggers when the bot is mentioned
@bot.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return

    # Check if the bot is mentioned in the message
    if bot.user.mentioned_in(message):
        print("I was mentioned?")
        
        # Check if there are any attachments
        if message.attachments:
            print("Attachment detected!")
            await attachment_detected(message)
            return  # Exit early to avoid processing further
        
        # Remove the mention from the message content
        command = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        # Check if a command was provided
        if command:
            await bot.process_commands(message)  # Allows command processing
        else:
            print("Yes, did you need me?")
            await message.channel.send("Yes, did you need me?")

# Function to handle attachment detection
async def attachment_detected(message):
    # Handle the attachment as needed, for now, just notify in chat
    await message.channel.send("I noticed an attachment! How can I assist you with it?")

# Example command: repairImage
@bot.command(name='repairImage')
async def repair_image(ctx):
    print("Repairing image!")
    await ctx.send("Repairing the image...")

# Run the bot with your token
bot.run(os.environ['MIITOPIA_DISCORD_BOT_TOKEN'])
