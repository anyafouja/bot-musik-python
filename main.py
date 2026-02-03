import discord
from discord.ext import commands
from dotenv import load_dotenv
import yt_dlp
import os

load_dotenv()

TOKEN = os.getenv("TOKEN")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Konfigurasi YT-DLP yang optimal
ytdl_opts = {
    'format': 'bestaudio[abr<=96]/bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'libopus',
    }]
}

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing: {e}")

@bot.tree.command(name="play", description="Putar lagu YouTube")
async def play(interaction: discord.Interaction, search: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("Kamu harus di VC!", ephemeral=True)

    voice_client = interaction.guild.voice_client

    # Cek Kondisi Voice Client
    if voice_client:
        if voice_client.is_connected() and voice_client.channel != interaction.user.voice.channel:
            # Jika ada di VC lain, pindah
            await voice_client.move_to(interaction.user.voice.channel)
        elif not voice_client.is_connected():
            # Jika error/hang, buat baru
            voice_client = await interaction.user.voice.channel.connect()
    else:
        # Jika belum ada sama sekali, connect baru
        try:
            voice_client = await interaction.user.voice.channel.connect()
        except Exception as e:
            print(f"Error connecting: {e}")
            return await interaction.response.send_message("❌ Gagal masuk VC.", ephemeral=True)

    # Defer response
    await interaction.response.defer()

    try:
        with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{search}", download=False)['entries'][0]
            url = info['url']
            title = info.get('title', 'Unknown')

        # Setup Audio Source
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        source = discord.FFmpegOpusAudio(url, **ffmpeg_options)

        # Cek apakah sedang playing
        if voice_client.is_playing():
            voice_client.stop()

        voice_client.play(source, after=lambda e: print(f'Finished: {title}'))

        # Pakai followup_message untuk reply yang aman
        await interaction.followup.send(f"Memutar: **{title}**")

    except Exception as e:
        print(f"Playback Error: {e}")
        await interaction.followup.send(f"❌ Error: {e}")

@bot.tree.command(name="stop", description="Stop musik")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Stopped!")
    else:
        await interaction.response.send_message("Tidak memutar apa-apa.", ephemeral=True)

@bot.tree.command(name="skip", description="Skip lagu")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped!")
    else:
        await interaction.response.send_message("Tidak memutar apa-apa.", ephemeral=True)

bot.run(TOKEN)
