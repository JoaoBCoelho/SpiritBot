import discord
from discord.ext import commands
import asyncio
from itertools import cycle
import youtube_dl
import Security

# region Token
TOKEN = Security.Token.value
# endregion

# client = Bot
client = commands.Bot(command_prefix='.')

players = {}
queues = {}

# remove the default help command
client.remove_command('help')


# region Functions
def return_string_date(seconds):
    # Convert seconds to a time string "[[[DD:]HH:]MM:]SS".
    dhms = ''
    for scale in 86400, 3600, 60:
        result, seconds = divmod(seconds, scale)
        if dhms != '' or result > 0:
            dhms += '{0:02d}:'.format(result)
    dhms += '{0:02d}'.format(seconds)
    return dhms


async def announce_music(ctx, player):
    author = ctx.message.author
    channel = ctx.message.channel
    embed = discord.Embed(
        title='{}'.format(player.title),
        colour=discord.Colour.orange()
    )
    embed.set_footer(text='Duração: {}'.format(return_string_date(player.duration)))
    # embed.set_image(url="https://img.youtube.com/vi/{}/0.jpg".format(player.url.split('v=')[1]))
    embed.set_author(name='Autor: {}'.format(author.display_name),
                     icon_url=author.avatar_url)

    # await client.say(embed=embed)
    await client.send_message(channel, embed=embed)


async def change_status():
    status = ['Msg1', 'Msg2', 'Msg3']
    await client.wait_until_ready()
    msgs = cycle(status)

    while not client.is_closed:
        current_status = next(msgs)
        await client.change_presence(game=discord.Game(name=current_status))
        await asyncio.sleep(5)


async def delete_last_message(ctx):
    channel = ctx.message.channel
    messages = []
    await client.send_message(channel, 'Ok')
    async for message in client.logs_from(channel, limit=2):
        messages.append(message)
    await client.delete_messages(messages)


async def delete_last_message_and_join(ctx):
    await delete_last_message(ctx)
    channel = ctx.message.author.voice.voice_channel
    server = ctx.message.server
    voice_client = client.voice_client_in(server)
    if voice_client is not None:
        if channel != voice_client.channel:
            await client.join_voice_channel(channel)
    else:
        await client.join_voice_channel(channel)


def check_queue(id):
    if queues[id] != []:
        player = queues[id].pop(0)
        players[id] = player
        player.start()


def resume(ctx):
    id = ctx.message.server.id
    players[id].resume()

# endregion

# region Events

@client.event
async def on_ready():
    await client.change_presence(game=discord.Game(name='PUBG'))
    print("I'm Ready.")


@client.event
async def on_message(message):
    author = message.author
    content = message.content
    print("{}: {}".format(author, content))
    await client.process_commands(message)

'''
@client.event
async def on_member_join(member):
   print('joined')
   role = discord.utils.get(member.server.roles, name="Example Role")
   await client.add_roles(member, role)


@client.event
async def on_message_delete(message):
   author = message.author
   content = message.content
   channel = message.channel
   await client.send_message(channel, "{}: {}".format(author, content))
'''
# endregion

# region Commands

@client.command()
async def ping():
    await client.say("Pong!")


@client.command(pass_context=True)
async def displayEmbed(ctx):
    author = ctx.message.author
    channel = ctx.message.channel
    embed = discord.Embed(
        title='Título',
        description='Essa é uma descrição',
        colour=discord.Colour.orange()
    )

    embed.set_footer(text='Esse é um rodapé')
    embed.set_image(url='https://wallpapercave.com/wp/wp2165447.jpg')
    embed.set_thumbnail(url='https://wallpapercave.com/wp/wp2165447.jpg')
    embed.set_author(name='Autor: Sparta',
                     icon_url='https://i.pinimg.com/236x/df/0a/4d/df0a4d00b556385930e06eb130967753--spartan-helmet-tattoo-police-tattoo.jpg')
    embed.add_field(name='Nome do Campo 1', value='Valor do Campo 1', inline=False)

    # await client.say(embed=embed)
    await client.send_message(channel, embed=embed)


@client.command(pass_context=True)
async def help(ctx):
    channel = ctx.message.channel

    embed = discord.Embed(
        colour=discord.Colour.orange()
    )

    embed.set_author(name='Help')
    embed.add_field(name='ping', value='Pong xD', inline=False)
    embed.add_field(name='join', value="Join voice channel", inline=False)
    embed.add_field(name='leave', value='Leave the voice channel', inline=False)
    embed.add_field(name='play [name of the song]', value='Search the music on youtube and play it', inline=False)
    embed.add_field(name='queue [name of the song]', value='Search the music on youtube and queue up to play it', inline=False)
    embed.add_field(name='pause', value='Pause the music being played', inline=False)
    embed.add_field(name='resume', value='Resumes the paused music', inline=False)
    embed.add_field(name='stop', value='Stops the current song and deletes the music queue', inline=False)
    embed.add_field(name='playGame [name of the game]', value='Does the bot play the game that was written', inline=False)
    embed.add_field(name='purge [amount (default 10)]', value='Deletes the amount of messages', inline=False)

    await client.send_message(channel, embed=embed)
    '''
    If you want to send the message to her author
    author = ctx.message.author
    await client.send_message(author, embed=embed) 
    '''

@client.command(pass_context=True)
async def join(ctx):
    await delete_last_message_and_join(ctx)


@client.command(pass_context=True)
async def leave(ctx):
    await delete_last_message(ctx)
    server = ctx.message.server
    voice_client = client.voice_client_in(server)
    await voice_client.disconnect()


@client.command(pass_context=True)
async def play(ctx, *args):
    await delete_last_message(ctx)
    server = ctx.message.server
    voice_client = client.voice_client_in(server)

    song = ''
    for word in args:
        song += word
        song += ' '

    opts = {
        'default_search': 'auto',
        'quiet': True,
    }
    player = await voice_client.create_ytdl_player(song, ytdl_options=opts, after=lambda: check_queue(server.id))
    players[server.id] = player
    player.start()
    await announce_music(ctx, player)

# Enqueue musics
@client.command(pass_context=True)
async def queue(ctx, *args):
    await delete_last_message_and_join(ctx)
    server = ctx.message.server
    voice_client = client.voice_client_in(server)

    song = ''
    for word in args:
        song += word
        song += ' '

    opts = {
        'default_search': 'auto',
        'quiet': True,
    }
    player = await voice_client.create_ytdl_player(song, ytdl_options=opts, after=lambda: check_queue(server.id))

    if server.id in queues:
        queues[server.id].append(player)
    else:
        queues[server.id] = [player]

    await announce_music(ctx, player)


# Pause
@client.command(pass_context=True)
async def pause(ctx):
    await delete_last_message(ctx)
    id = ctx.message.server.id
    players[id].pause()


# Resume
@client.command(pass_context=True)
async def resume(ctx):
    await delete_last_message(ctx)
    resume(ctx)


@client.command(pass_context=True)
async def stop(ctx):
    await delete_last_message(ctx)
    id = ctx.message.server.id
    players[id].stop()
    queues.clear()


@client.command(pass_context=True)
async def playGame(ctx, *args):
    await delete_last_message(ctx)
    game = ''
    for word in args:
        game += word
        game += ' '
        await client.change_presence(game=discord.Game(name=game))


@client.command(pass_context=True)
async def purge(ctx, amount=10):
    amount += 1
    channel = ctx.message.channel
    messages = []
    async for message in client.logs_from(channel, limit=int(amount)):
        messages.append(message)
    await client.delete_messages(messages)
    await client.say('{} Message(s) deleted.'.format(amount - 1))


# endregion

# client.loop.create_task(change_status())
client.run(TOKEN)
