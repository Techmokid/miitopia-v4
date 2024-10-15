import discord
from discord.ext import commands
import os
import random
from PIL import Image
from moviepy.editor import ImageSequenceClip, AudioFileClip
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import aiohttp

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
            await message.channel.send("On it!")

            # Start processing attachments in a separate thread
            loop = asyncio.get_event_loop()
            for attachment in message.attachments:
                # Generate a unique thread ID for file naming
                unique_id = str(uuid.uuid4())  # Generate a unique ID
                loop.run_in_executor(executor, lambda a=attachment, uid=unique_id: process_attachment(message, a, uid))

        # Remove the mention from the message content
        command = message.content.replace(f'<@{bot.user.id}>', '').replace('\n', ' ').replace('  ', ' ').strip()

        # Check if a command was provided
        if command:
            print("Running command")
            for cmd in command.split(" "):
                # Call the coroutine directly
                await process_command(cmd, message)

            # It's good to call process_commands to handle any command defined in your bot
            await bot.process_commands(message)
        else:
            print("Nevermind, wasn't wanted")
            responses = [
                "Yes, did you need me?",
                "Hey what's up?",
                "What's going on?",
                "Did you need anything?"
            ]
            await message.channel.send(random.choice(responses))


async def process_command(command, message):
    if command.startswith("http"):
        print("Processing HTTP image file")
        async with aiohttp.ClientSession() as session:
            async with session.get(command) as response:
                if response.status == 200:
                    # Get the content of the response as bytes
                    image_data = await response.read()
                    
                    # Save the image to a temporary file
                    unique_id = str(uuid.uuid4())
                    file_path = f"./temp/{unique_id}.png"  # Save as PNG or choose based on URL

                    # Use run_in_executor for blocking file I/O
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(executor, save_image_to_file, file_path, image_data)

                    print("Downloaded image from URL")

                    # Create video from the downloaded image
                    video_path = await loop.run_in_executor(executor, create_video, file_path, unique_id)
                    print("Made video from URL")

                    # Send the video back to the channel
                    await message.channel.send(file=discord.File(video_path))

                    # Clean up temporary files
                    os.remove(file_path)
                    os.remove(video_path)
                else:
                    await message.channel.send("Failed to download the image. Please check the URL.")

def save_image_to_file(file_path, image_data):
    with open(file_path, 'wb') as f:
        f.write(image_data)

# Function to process the attachment
def process_attachment(message, attachment, unique_id):
    # Check if the attachment is a valid image file
    if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        asyncio.run_coroutine_threadsafe(
            message.channel.send("Invalid image file! Please upload a PNG, JPG, JPEG, or GIF."),
            bot.loop
        )
        return

    # Generate unique file paths
    file_path = f"./temp/{unique_id}_{attachment.filename}"
    asyncio.run_coroutine_threadsafe(attachment.save(file_path), bot.loop)
    print("We have the image")
    
    # Create video from image
    video_path = create_video(file_path, unique_id)
    print("Made video")

    # Send the video back to the channel
    asyncio.run_coroutine_threadsafe(
        message.channel.send(file=discord.File(video_path)),
        bot.loop
    )

def create_video(image_path, unique_id):
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
    video_path = f"./temp/output_video_{unique_id}.mp4"  # Use unique_id in the video path
    clip.set_duration(audio_clip.duration).write_videofile(video_path, codec='libx264')

    return video_path

# Create a temp directory if it doesn't exist
if not os.path.exists('./temp'):
    os.makedirs('./temp')

# Run the bot with your token
bot.run(os.environ['MIITOPIA_DISCORD_BOT_TOKEN'])
