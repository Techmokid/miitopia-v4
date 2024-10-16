import discord,os,random,asyncio,time,uuid,aiohttp,threading

from PIL import Image
from discord.ext import commands
from moviepy.editor import ImageSequenceClip, AudioFileClipfrom concurrent.futures import ThreadPoolExecutor

# Set your bot's command prefix and the intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Multithreading
task_counter = 0
processLock = threading.lock()
executor = ThreadPoolExecutor(max_workers=10)  # Adjust max_workers as needed

# Program variables
lastImages = []
audio_folder = "./music"
temp_folder  = "./temp"




# Bot events
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@bot.event
async def on_message(message):
    global task_counter,lastImages

    if message.author == bot.user:          # If this bot wrote the message, ignore the message
        return
    if not bot.user.mentioned_in(message):  # If this bot was not mentioned, ignore the message
        return

    print()
    print("I was mentioned!")
    command = message.content.replace(f'<@{bot.user.id}>', '').replace('\n', ' ').replace('  ', ' ')
    commands = command.split(" ")

    # Were we actually needed?
    if (len(commands)==1) and (not message.attachments):
        responses = [
            "Yes, did you need me?",
            "Hey what's up?",
            "What's going on?",
            "Did you need anything?",
            "What did ya need?",
            "How can I help?"
        ]
        await message.channel.send(random.choice(responses))
    
    # Process commands first
    alertedUserToProcessing = False
    processAttachments = True
    for com in commands:
        if com.lower()=="threadcheck":
            await message.channel.send(f"Current number of active running threaded tasks: {task_counter}")
            return
        if com.lower()=="again" or com.lower()=="repeat" or com.lower()=="reprocess":
            
            return

    # Process attachments
    if not processAttachments:
        return
    if not message.attachments:
        return

    for attachment in message.attachments:
        print("Attachment found")

def create_video(image_path, unique_id):
    video_path = temp_folder + f"/output_video_{unique_id}.mp4"
    duration = 10  # Set the duration for the video (seconds)
    
    # Load the image
    image = Image.open(image_path)
    image = image.resize((640, 480))  # Resize for video, optional

    # Create a video clip from the image
    clip = ImageSequenceClip([image_path], fps=24)

    # Get a random audio file from the local folder
    audio_files = [f for f in os.listdir(audio_folder) if f.endswith('.mp3')]
    if not audio_files:
        raise FileNotFoundError("No audio files found in the specified folder.")
    
    audio_path = os.path.join(audio_folder, random.choice(audio_files))
    audio_clip = AudioFileClip(audio_path)

    clip = clip.set_audio(audio_clip) # Set the audio of the clip

      # Use unique_id in the video path
    #clip.set_duration(audio_clip.duration).write_videofile(video_path, codec='libx264')
    clip.set_duration(duration).write_videofile(video_path, codec='libx264')

    return video_path
