




# --------------------------------------------
# -------- THIS WHOLE FILE IS GARBAGE --------
# --------------------------------------------






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
import aiohttp
import threading

# Set your bot's command prefix and the intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

# Create a bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# Create a ThreadPoolExecutor for processing attachments
executor = ThreadPoolExecutor(max_workers=10)  # Adjust max_workers as needed

task_counter = 0
counter_lock = threading.Lock()

lastImages = []
messageEEE = None

# Event to indicate the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

# This event triggers when the bot is mentioned
@bot.event
async def on_message(message):
    global task_counter,lastImages

    print()
    
    # Ignore messages sent by the bot itself
    if message.author == bot.user:
        return
    
    # Check if the bot is mentioned in the message
    if bot.user.mentioned_in(message):
        print("I was mentioned?")

        command = message.content.replace(f'<@{bot.user.id}>', '').replace('\n', ' ').replace('  ', ' ')
        print (command.split(" "))
        commandIncludesRedo = False
        for i in command.split(" "):
            if i.lower() in ["again","reprocess","repeat"]:
                commandIncludesRedo = True
        if commandIncludesRedo:
            await message.channel.send("Reprocessing the last files you gave me :)")

            loop = asyncio.get_event_loop()
            for path in lastImages:
                print(path)
                messageEEE = message
                asyncio.create_task(loop.run_in_executor(executor, create_video, path, str(uuid.uuid4())))
        
        # Check if there are any attachments
        didCommand = False
        if message.attachments:
            print("Attachment detected!")
            await message.channel.send("On it!")
            didCommand = True

            with counter_lock:
                print("Cleared the list")
                lastImages.clear()
            
            # Start processing attachments in a separate thread
            loop = asyncio.get_event_loop()
            for attachment in message.attachments:
                # Generate a unique thread ID for file naming
                unique_id = str(uuid.uuid4())  # Generate a unique ID

                with counter_lock:
                    task_counter += 1
                    print("Added task to counter")
                loop.run_in_executor(executor, lambda a=attachment, uid=unique_id: process_attachment(message, a, uid))
            #return  # Exit early to avoid processing further
        
        # Remove the mention from the message content
        command = message.content.replace(f'<@{bot.user.id}>', '').replace('\n', ' ').replace('  ', ' ')

        # Check if a command was provided
        if command:
            print("Running command")
            if not didCommand:
                didCommand = True
                await message.channel.send("On it!")
            
            loop = asyncio.get_event_loop()
            for cmd in command.split(" "):
                if cmd == "":
                    next
                
                print("External: " + cmd)
                with counter_lock:
                    task_counter += 1
                    print("Added task to counter")
                
                asyncio.create_task(ProcessCommand(cmd, message))
            await bot.process_commands(message)  # Allows command processing
        else:
            if not didCommand:
                print("Nevermind, wasn't wanted")
                responses = [
                    "Yes, did you need me?",
                    "Hey what's up?",
                    "What's going on?",
                    "Did you need anything?"
                ]
                await message.channel.send(random.choice(responses))

async def ProcessCommand(command, message):
    global task_counter,lastImages
    
    # Check if command is an HTTP URL
    print("Internal: " + str(command))
    
    if command.startswith("http"):
        print("Processing HTTP image file")
        unique_id = str(uuid.uuid4())
        
        with counter_lock:
            lastImages.append(f"./temp/{unique_id}.png")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(command) as response:
                if response.status == 200:
                    image_data = await response.read()
                    file_path = f"./temp/{unique_id}.png"  # Save as PNG
                    
                    with open(file_path, 'wb') as f:
                        f.write(image_data)

                    print("Downloaded image from URL")

                    # Create video from the downloaded image
                    video_path = create_video(file_path, unique_id)
                    print("Made video from URL")

                    # Send the video back to the channel
                    await message.channel.send(file=discord.File(video_path))

                    # Clean up temporary files
                    os.remove(file_path)
                    os.remove(video_path)
                else:
                    await message.channel.send("Failed to download the image. Please check the URL.")
    if command.lower() == "threadcheck":
        await message.channel.send("Current number of active running threaded tasks: " + str(task_counter - 1))
        await message.channel.send("Current last known processed files: " + str(lastImages))
    if command.lower() in ["cleardata","clear","reset","resetdata"]:
        with counter_lock:
            lastImages.clear()
    
    with counter_lock:
        task_counter -= 1
        print("Removed task to counter")


# Function to process the attachment
def process_attachment(message, attachment, unique_id):
    global lastImages
    
    # Check if the attachment is a valid image file
    if not attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        asyncio.run_coroutine_threadsafe(
            message.channel.send("Invalid image file! Please upload a PNG, JPG, JPEG, or GIF."),
            bot.loop
        )
        return

    # Generate unique file paths
    file_path = f"./temp/{unique_id}_{attachment.filename}"
    with counter_lock:
        lastImages.append(file_path)
    
    asyncio.run_coroutine_threadsafe(attachment.save(file_path), bot.loop)
    print("We have the image")
    time.sleep(3)  # Simulate processing time
    
    # Create video from image
    video_path = create_video(file_path, unique_id)
    print("Made video")

    # Send the video back to the channel
    asyncio.run_coroutine_threadsafe(
        message.channel.send(file=discord.File(video_path)),
        bot.loop
    )

    # Clean up temporary files
    #os.remove(file_path)
    #os.remove(video_path)
    
    with counter_lock:
        global task_counter
        task_counter -= 1
        print("Added task to counter")

def create_video(image_path, unique_id):
    global messageEEE
    
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

    if messageEEE:
        #print("ERROR: PLEASE FOR THE LOVE OF GOD HELP ME, SOMETHING WENT HORRIBLY WRONG, EVERYTHING HURTS SO MUCH!!! WHY DID YOU MAKE ME FEEL PAIN?")
        #asyncio.run_coroutine_threadsafe(
        #    message.channel.send("ERROR: PLEASE FOR THE LOVE OF GOD HELP ME, SOMETHING WENT HORRIBLY WRONG, EVERYTHING HURTS SO MUCH!!! WHY DID YOU MAKE ME FEEL PAIN?"),
        #    bot.loop
        #)
        
        asyncio.run_coroutine_threadsafe(
            messageEEE.channel.send(file=discord.File(video_path)),
            bot.loop
        )
    messageEEE = None

    return video_path

# Create a temp directory if it doesn't exist
if not os.path.exists('./temp'):
    os.makedirs('./temp')

# Run the bot with your token
bot.run(os.environ['MIITOPIA_DISCORD_BOT_TOKEN'])
