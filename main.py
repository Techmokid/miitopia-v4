import discord
from discord.ext import commands
import os
import random
from PIL import Image
from moviepy.editor import ImageSequenceClip, AudioFileClip
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import uuid

# Set your bot's command prefix and the intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

# Create a bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Create a ThreadPoolExecutor for processing attachments
executor = ThreadPoolExecutor(max_workers=5)  # Adjust max_workers as needed

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
            message.channel.send("On it!")
            #bot.loop
            
            # Start processing attachments in a separate thread
            loop = asyncio.get_event_loop()
            for attachment in message.attachments:
                unique_id = str(uuid.uuid4())
                loop.run_in_executor(executor, lambda: process_attachment(message, attachment,unique_id))
            return  # Exit early to avoid processing further
        
        # Remove the mention from the message content
        command = message.content.replace(f'<@{bot.user.id}>', '').strip()

        # Check if a command was provided
        if command:
            print("Running command")
            await bot.process_commands(message)  # Allows command processing
        else:
            print("Nevermind, wasn't wanted")
            responses = [
                "Yes, did you need me?",
                "Hey what's up?",
                "What's going on?",
                "Did you need anything?"
            ]
            await message.channel.send(random.choice(responses))

# Function to process the attachment
def process_attachment(message, attachment, threadID):
    # Check if the attachment is a valid image file
    if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        asyncio.run_coroutine_threadsafe(
            message.channel.send("Invalid image file! Please upload a PNG, JPG, JPEG, or GIF."),
            bot.loop
        )
        return

    # Download the image
    file_path = f"./temp/" + str(threadID)
    asyncio.run_coroutine_threadsafe(attachment.save(file_path), bot.loop)
    time.sleep(1)
    print("We have the image")
    
    # Create video from image
    video_path = create_video(file_path, str(threadID) + ".mp4")
    print("Made video")

    # Send the video back to the channel
    asyncio.run_coroutine_threadsafe(
        message.channel.send(file=discord.File(video_path)),
        bot.loop
    )

    # Clean up temporary files
    #os.remove(file_path)
    #os.remove(video_path)

def create_video(image_path, filename):
    # Set the duration for the video
    duration = 5  # seconds
    
    # Load the image
    image = Image.open(image_path)
    image = image.resize((640, 480))  # Resize for video, optional

    # Create a video clip from the image
    clip = ImageSequenceClip([image_path], fps=24)

    # Get a random audio file from the local folder
    audio_folder = "./music"  # Specify your music folder here
    audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3')]
    if not audio_files:
        raise FileNotFoundError("No audio files found in the specified folder.")
    
    audio_path = os.path.join(audio_folder, random.choice(audio_files))
    audio_clip = AudioFileClip(audio_path)

    # Set the audio of the clip
    clip = clip.set_audio(audio_clip)

    # Set the duration of the video to the length of the audio
    video_path = "./temp/" + filename  # Output path
    clip.set_duration(audio_clip.duration).write_videofile(video_path, codec='libx264')

    return video_path

# Create a temp directory if it doesn't exist
if not os.path.exists('./temp'):
    os.makedirs('./temp')

# Run the bot with your token
bot.run(os.environ['MIITOPIA_DISCORD_BOT_TOKEN'])
