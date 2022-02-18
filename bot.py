import discord
import youtube_dl
from discord.voice_client import VoiceClient
from discord.ext import commands , tasks
from discord.ext.commands import has_permissions, MissingPermissions


youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

client = commands.Bot(command_prefix = '?')

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle,activity=discord.Game('Let the Music Speak!'))
    print(' Bot is Ready ')

@client.command(help=' This command shows bot ping!')
async def ping(ctx):
    await ctx.send(f'ping! {round(client.latency * 1000)}ms')


@client.command(help=' This command clear last 5 messages! ')
@has_permissions(manage_roles=True, manage_messages=True)
async def clear(ctx, amount=5):
    await ctx.channel.purge( limit=amount )

@clear.error
async def clear_error(error, ctx):
    if isinstance(error, MissingPermissions):
        text = "`you` do not have permissions to do that (NOOB)!".format(ctx.message.author)
        await bot.send_message(ctx.message.channel, text)

@client.command(pass_context = True , help=' This command would let the bot join the voice!')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send('`YOU` are not connected to voice channel ')
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@client.command(pass_context = True , help=' This command plays the song!')
async def play(ctx , url):
    if not ctx.message.author.voice:
        await ctx.send('`YOU` are not Connected to voice channel ')
        return

    channel = ctx.message.author.voice.channel
    bot_channel =  ctx.guild.voice_client
    if not bot_channel:
        await channel.connect()
    
    server = ctx.message.guild
    voice_channel = server.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send('**Now playing:** {}'.format(player.title))


@client.command(name='pause', help=' This command pauses the song!')
async def pause(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.pause()

@client.command(name='resume', help=' This command resumes the song!')
async def resume(ctx):
    server = ctx.message.guild
    voice_channel = server.voice_client

    voice_channel.resume()


@client.command(pass_context = True, help=' This command would let the bot leave the server!' )
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    await voice_client.disconnect()



client.run('your token')
