import discord, os, random, uuid, asyncio,user_memory
from discord.ext import commands
from PIL import Image
from moviepy.editor import ImageSequenceClip, AudioFileClip
from concurrent.futures import ThreadPoolExecutor






# Set bot's command prefix and the intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix='', intents=intents)

# Multithreading and process control
task_counter = 0
processLock = asyncio.Lock()
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
        await message.channel.send(random.choice(responses))
        return

    if "ignore" in commands:
        await message.channel.send(f"Ignored all attachments and commands lol")
        return
    if "threadcheck" in commands:
        await message.channel.send(f"Current number of active running tasks: {task_counter}")
    if commands[0] == "datacheck":
        if len(commands) == 1:
            await message.channel.send(f"Username was not specified")
        else:
            await message.channel.send(f"Current data on user {commands[1]}: " + str(user_memory.getUserData(commands[1])))
            
    
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
    unique_id = str(uuid.uuid4())
    file_path = f"{temp_folder}/{unique_id}_{attachment.filename}"

    async with processLock:
        user_memory.addUserData(message.author.name,file_path)
    await attachment.save(file_path)

    # Process the image in a separate thread to avoid blocking
    loop = asyncio.get_event_loop()
    try:
        video_path = await loop.run_in_executor(executor, create_video_from_image, file_path, unique_id)
        await message.channel.send(file=discord.File(video_path))
    except Exception as e:
        await message.channel.send(f"Error processing the video: {str(e)}")
    finally:
        async with processLock:
            task_counter -= 1

# Function to create video from image (runs in executor)
def create_video_from_image(image_path, unique_id):
    video_path = os.path.join(temp_folder, f"output_video_{unique_id}.mp4")
    
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
