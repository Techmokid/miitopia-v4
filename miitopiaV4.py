import discord
import os
import random
import uuid
import asyncio
import user_memory
from discord.ext import commands
from PIL import Image
from moviepy.editor import ImageSequenceClip, AudioFileClip
from concurrent.futures import ThreadPoolExecutor
import threading

# Set bot's command prefix and the intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix='', intents=intents)

# Multithreading and process control
task_counter = 0
processLock = asyncio.Lock()  # Async lock for async functions
threadLock = threading.Lock()  # Thread lock for thread-safe operations
executor = ThreadPoolExecutor(max_workers=10)  # Adjust max_workers as needed

# Program variables
audio_folder = "./music"
temp_folder = "./temp"
if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)
if not os.path.exists(audio_folder):
    os.makedirs(audio_folder)

# Bot events
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    global task_counter

    if message.author == bot.user:
        return
    if not bot.user.mentioned_in(message):
        return

    command = message.content.replace(f'<@{bot.user.id}>', '').strip()
    commands = command.split(" ")

    # Simple response if no valid command or attachment is given
    if len(commands) == 1 and commands[0] == '' and not message.attachments:
        responses = [
            "Yes, did you need me?",
            "Hey what's up?",
            "What's going on?",
            "Did you need anything?",
            "How can I help?",
            "Sup?",
            "What's up?"
        ]

        await message.channel.send(random.choice(responses) + (task_counter != 0) * (f" I'm currently a tad busy processing {task_counter} data request" + (task_counter != 1) * "s" + " at the moment"))

    # Process commands
    if "ignore" in commands:
        await message.channel.send(f"Ignored all attachments and commands lol")
        return
    if ("help" in commands) or ("?" in commands):
        msg = "I am the Miitopia Version 4 discord bot programmed by Andrey || translated from the original MiitopiaV1 Javascript version from a long time ago||\n"
        msg += "Basically, if you ping me in discord and attach images, I will put music from the Wii Nintendo game \"Miitopia\" over them\n\n"
        msg += "Optional commands that I will listen to are as follows:\n```\n"
        msg += " - Ignore:      Nomatter what other commands or attachments, do nothing\n"
        msg += " - Help:        Displays this help menu\n"
        msg += " - ?:           Same as help (Alias)\n"
        msg += " - Threadcheck: I will tell you how many processes I'm currently processing\n"
        msg += " - Dataclear:   If given a username, I will clear the stored 'again' data for repeating a command\n"
        msg += " - Again:       I will reprocess the last files you gave me to process\n"
        msg += " - Reprocess:   Same as 'Again' (Alias)\n"
        msg += " - Repeat:      Same as 'Again' (Alias)\n"
        msg += "```"
        await message.channel.send(msg)
    if "threadcheck" in commands:
        await message.channel.send(f"Current number of active running tasks: {task_counter}")
    if commands[0] == "datacheck":
        if len(commands) == 1:
            await message.channel.send(f"Username was not specified")
        else:
            await message.channel.send(f"Current data on user {commands[1]}: " + str(user_memory.getUserData(commands[1])))
    if commands[0] == "dataclear":
        if len(commands) == 1:
            await message.channel.send(f"Username was not specified")
        else:
            user_memory.clearUserData(commands[1])
            await message.channel.send(f"Cleared data for user {commands[1]}")
    if ("again" in commands) or ("repeat" in commands) or ("reprocess" in commands):
        await message.channel.send(f"Let me try those files again!")
        user_data = user_memory.getUserData(message.author.name)
        if user_data:
            tasks = [asyncio.get_event_loop().run_in_executor(executor, create_video_from_image_and_handle_thread_counter, path) for path in user_data]
            video_paths = await asyncio.gather(*tasks)  # Await all tasks and gather the results
            for video_path in video_paths:
                await message.channel.send(file=discord.File(video_path))
        else:
            await message.channel.send("No previous attachments found to reprocess.")
    
    # Process attachments
    if not message.attachments:
        return

    user_memory.clearUserData(message.author.name)
    tasks = [download_and_create_video(message, attachment) for attachment in message.attachments]
    await asyncio.gather(*tasks)

# Coroutine for processing image attachment
async def download_and_create_video(message, attachment):
    global task_counter
    if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        await message.channel.send("Invalid image file! Please upload a PNG, JPG, JPEG, or GIF.")
        return

    async with processLock:
        task_counter += 1

    # Download and process the image asynchronously
    file_path = f"{temp_folder}/{str(uuid.uuid4())}_{attachment.filename}"

    async with processLock:
        user_memory.addUserData(message.author.name, file_path)
    await attachment.save(file_path)

    # Process the image in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        video_path = await loop.run_in_executor(executor, create_video_from_image, file_path)
        await message.channel.send(file=discord.File(video_path))
    except Exception as e:
        await message.channel.send(f"Error processing the video: {str(e)}")
    finally:
        async with processLock:
            task_counter -= 1

# Function to create video from image (runs in executor)
def create_video_from_image_and_handle_thread_counter(image_path):
    global task_counter

    with threadLock:
        task_counter += 1
    
    video_path = create_video_from_image(image_path)  # Get video path
    
    with threadLock:
        task_counter -= 1
    
    return video_path

def create_video_from_image(image_path):
    video_path = os.path.join(temp_folder, f"output_video_{str(uuid.uuid4())}.mp4")
    
    # Load the image
    image = Image.open(image_path)
    image = image.resize((640, 480))  # Resize for video, optional

    # Create a video clip from the image
    clip = ImageSequenceClip([image_path], fps=24)

    # Pick a random audio file
    audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3')]
    if not audio_files:
        raise FileNotFoundError("No audio files found in the specified folder.")
    
    audio_path = os.path.join(audio_folder, random.choice(audio_files))
    audio_clip = AudioFileClip(audio_path)

    # Set the audio of the clip and write to file
    clip = clip.set_audio(audio_clip)
    clip.set_duration(audio_clip.duration).write_videofile(video_path, codec='libx264')

    return video_path


# Run the bot using your token
bot.run(os.environ['MIITOPIA_DISCORD_BOT_TOKEN'])
