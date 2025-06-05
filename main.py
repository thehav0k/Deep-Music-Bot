import discord
import os
from dotenv import load_dotenv
import asyncio
import logging
import queue
from logging.handlers import QueueHandler, QueueListener

# Setup asynchronous, non-blocking logging using a queue
log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)
formatter = logging.Formatter('%(asctime)s %(levelname)s:%(name)s: %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
listener = QueueListener(log_queue, stream_handler)
listener.start()

# Root logger configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(queue_handler)

# Ensure Opus is loaded for voice features
if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus('/opt/homebrew/lib/libopus.dylib')
    except Exception as e:
        logger.error("Could not load Opus library: %s", e)

from discord.ext import commands
from deepseek_cli import send_message
import yt_dlp as youtube_dl

# Bot setup
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# send_message imported from deepseek_cli handles API key internally

# Music playback setup
queues = {}         # {guild_id: [song_dict, ...]}
current_song = {}   # {guild_id: song_dict}
looping = {}        # {guild_id: bool}
playlists = {}      # {guild_id: {playlist_name: [song_dict, ...]}}
timers = {}         # {guild_id: asyncio.Task}

ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
}

async def search_song(query):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            if query.startswith('http'):
                info = ydl.extract_info(query, download=False)
            else:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            return {'title': info['title'], 'url': info['url']}
        except Exception:
            return None

async def get_fresh_song_url(webpage_url):
    ydl_opts_stream = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': False
    }
    with youtube_dl.YoutubeDL(ydl_opts_stream) as ydl:
        try:
            info = ydl.extract_info(webpage_url, download=False)
            # direct audio url
            return info.get('url')
        except Exception as e:
            logger.error("Stream URL fetch error: %s", e)
            return None

async def check_voice_channel(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client is None:
        await ctx.send("The bot is not in a voice channel. Use /gaanshonao to start playing.")
        return False
    if ctx.author.voice is None or ctx.author.voice.channel != voice_client.channel:
        await ctx.send("You need to be in the same voice channel as the bot to use this command.")
        return False
    return True

async def inactivity_timer(guild_id):
    await asyncio.sleep(120)
    vc = bot.get_guild(guild_id).voice_client
    if vc and isinstance(vc.channel, discord.VoiceChannel) and len(vc.channel.members) == 1:
        await vc.disconnect(force=True)
        timers.pop(guild_id, None)

@bot.event
async def on_ready():
    logger.info("Logged in as %s", bot.user)

@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        return
    vc = member.guild.voice_client
    if vc is None:
        return
    ch = vc.channel
    if before.channel == ch and after.channel != ch and len(ch.members) == 1:
        timers[member.guild.id] = asyncio.create_task(inactivity_timer(member.guild.id))
    if before.channel != ch and after.channel == ch:
        task = timers.pop(member.guild.id, None)
        if task:
            task.cancel()

@bot.command()
async def play(ctx, *, query):
    song = await search_song(query)
    if song is None:
        await ctx.send("Music not found!")
        return
    stream_url = await get_fresh_song_url(song['url'])
    if stream_url is None:
        await ctx.send("Could not fetch stream URL.")
        return
    vc = ctx.guild.voice_client
    if ctx.author.voice is None:
        await ctx.send("Join a voice channel first.")
        return
    if vc is None:
        vc = await ctx.author.voice.channel.connect()
    elif vc.channel != ctx.author.voice.channel:
        await ctx.send("Bot already in another channel.")
        return
    if vc.is_playing(): vc.stop()
    current_song[ctx.guild.id] = song

    def play_next(error):
        if error:
            logger.error("Playback error: %s", error)
        asyncio.run_coroutine_threadsafe(_play_next(ctx), bot.loop)

    async def _play_next(ctx):
        if looping.get(ctx.guild.id):
            vc.play(discord.FFmpegPCMAudio(current_song[ctx.guild.id]['url']))
        elif queues.get(ctx.guild.id):
            nxt = queues[ctx.guild.id].pop(0)
            current_song[ctx.guild.id] = nxt
            vc.play(discord.FFmpegPCMAudio(nxt['url']), after=play_next)
            await ctx.send(f"Now playing: {nxt['title']}")
        else:
            current_song[ctx.guild.id] = None

    vc.play(discord.FFmpegPCMAudio(stream_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn -b:a 128k"), after=play_next)
    await ctx.send(f"Now playing: {song['title']}")

@bot.command(name='next')
async def Next(ctx, *, query):
    song = await search_song(query)
    if song is None:
        await ctx.send("Music not found!")
        return
    queues.setdefault(ctx.guild.id, []).append(song)
    await ctx.send(f"Added to queue: {song['title']}")

@bot.command()
async def stop(ctx):
    if not await check_voice_channel(ctx): return
    vc = ctx.guild.voice_client
    if vc.is_playing():
        vc.pause()
        await ctx.send("Paused")
    else:
        await ctx.send("Nothing playing")

@bot.command()
async def resume(ctx):
    """Resume paused music playback."""
    if not await check_voice_channel(ctx): return
    vc = ctx.guild.voice_client
    if vc.is_paused():
        vc.resume()
        await ctx.send("Resumed")
    else:
        await ctx.send("Nothing paused")

@bot.command()
async def Exit(ctx):
    if not await check_voice_channel(ctx): return
    vc = ctx.guild.voice_client
    if vc.is_playing(): vc.stop()
    queues.pop(ctx.guild.id, None)
    current_song.pop(ctx.guild.id, None)
    await vc.disconnect(force=True)
    timers.pop(ctx.guild.id, None)
    await ctx.send("Stopped and disconnected")

@bot.command()
async def list(ctx, name, *, query):
    song = await search_song(query)
    if song is None:
        await ctx.send("Music not found!")
        return
    pls = playlists.setdefault(ctx.guild.id, {})
    pls.setdefault(name, []).append(song)
    await ctx.send(f"Added {song['title']} to {name}")

@bot.command()
async def loop(ctx):
    if not await check_voice_channel(ctx): return
    looping[ctx.guild.id] = not looping.get(ctx.guild.id, False)
    await ctx.send(f"Looping {'on' if looping[ctx.guild.id] else 'off'}")

# Chat memory for AI context
chat_histories = {}  # {channel_id: [message_dict, ...]}
chat_sessions = {}   # {channel_id: bool, active session flag}

@bot.command()
async def ask(ctx, *, question):
    """Ask DeepSeek AI a question with memory across this channel and support play/recommend intents"""
    # start a persistent chat session in this channel
    chat_sessions[ctx.channel.id] = True
    ql = question.lower().strip()
    # handle pause intent
    if ql in ('pause', 'stop'):
        return await ctx.invoke(bot.get_command('stop'))
    # handle resume intent
    if ql == 'resume':
        return await ctx.invoke(bot.get_command('resume'))
    # handle direct play intent
    if ql.startswith('play '):
        song_query = question[5:].strip()
        return await ctx.invoke(bot.get_command('play'), query=song_query)
    # handle recommendation intent
    if 'recommend' in ql:
        async with ctx.typing():
            rec = await bot.loop.run_in_executor(None, send_message, [{"role": "user", "content": question}])
        if rec:
            return await ctx.invoke(bot.get_command('play'), query=rec)
        else:
            return await ctx.send("Sorry, I couldn't get a recommendation.")
    # default: AI chat with memory
    history = chat_histories.setdefault(ctx.channel.id, [])
    history.append({"role": "user", "content": question})
    async with ctx.typing():
        reply = await bot.loop.run_in_executor(None, send_message, history)
    if reply:
        history.append({"role": "assistant", "content": reply})
        for chunk in (reply[i:i+2000] for i in range(0, len(reply), 2000)):
            await ctx.send(chunk)
    else:
        await ctx.send("Sorry, I couldn't process your question.")

@bot.command()
async def forget(ctx):
    """Clear AI chat memory for this channel"""
    chat_histories.pop(ctx.channel.id, None)
    await ctx.send("Chat memory cleared for this channel.")

@bot.command()
async def over(ctx):
    """End the persistent chat session"""
    chat_sessions.pop(ctx.channel.id, None)
    chat_histories.pop(ctx.channel.id, None)
    await ctx.send("Chat session ended.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    ctx = await bot.get_context(message)
    content = message.content.strip()
    lower = content.lower()
    # handle natural language commands when no slash prefix
    if not content.startswith(bot.command_prefix):
        if lower.startswith('play '):
            return await ctx.invoke(bot.get_command('play'), query=content[5:].strip())  # type: ignore
        if lower in ('pause', 'stop'):
            return await ctx.invoke(bot.get_command('stop'))  # type: ignore
        if lower == 'resume':
            return await ctx.invoke(bot.get_command('resume'))  # type: ignore
        if lower.startswith('next '):
            return await ctx.invoke(bot.get_command('next'), query=content[5:].strip())  # type: ignore
        # AI chat fallback
        if chat_sessions.get(message.channel.id):
            history = chat_histories.setdefault(message.channel.id, [])
            history.append({"role": "user", "content": content})
            async with message.channel.typing():
                reply = await bot.loop.run_in_executor(None, send_message, history)
            if reply:
                history.append({"role": "assistant", "content": reply})
                for chunk in (reply[i:i+2000] for i in range(0, len(reply), 2000)):
                    await message.channel.send(chunk)
            else:
                await message.channel.send("Sorry, I couldn't process your message.")
            return
    # process slash commands and others
    await bot.process_commands(message)

@bot.command()
async def lyrics(ctx, *, song_name):
    """Get lyrics for a song using DeepSeek AI."""
    question = f"Please provide only the lyrics for the song '{song_name}', without any additional commentary or explanation."
    history = [{"role": "user", "content": question}]
    async with ctx.typing():
        reply = await bot.loop.run_in_executor(None, send_message, history)
    if reply:
        for chunk in (reply[i:i+2000] for i in range(0, len(reply), 2000)):
            await ctx.send(chunk)
    else:
        await ctx.send("Sorry, I couldn't fetch the lyrics.")

# Run the bot
load_dotenv()
bot.run(os.getenv('BOT_TOKEN'))

