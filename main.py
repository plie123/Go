import os
import discord
from discord.ext import commands
from discord import app_commands

from youtube_dl import YoutubeDL

from myserver import server_on

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.is_paused = False

        
        self.music_queue= []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'nonplaylist': 'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.TDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, donload=False)['entries'][0]
            except Exception:
                return False
        return {'source': info['formats'[0]['url']], 'title': info['title']}
        
    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True    

            m_url = self.music_queue[0][0]['source']

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]['source']

            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                if self.vc ==None:
                    await ctx.send("Could not connect to the voice channel")
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())

        else:
            self.is_playing = False

        @commands.command(name="play", aliases=["p", "playing"], help="Played the selected song from youtube")
        async def play(self, ctx, *args):
            query = " ".join(args)

            voice_channel = ctx.author.voice.channel
            if voice_channel is None:
                await ctx.send("Connect to a voice channel!")
            elif self.is_paused:
                self.vc.resume()
            else:
                song = self.search_yt(query)
                if type(song) == type(True):
                    await ctx.send("Could not download the song. Incorrect format, try different one")
                else:
                    await ctx.send("Song add to queue")
                    self.music_queue.append([song, voice_channel])

                    if self.is_playing == False:
                        await self.play_music(ctx)
    @commands.command(name="pause", help="Pauses the current song being played")
    async def pause(self,ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    @commands.command(name="resume", aliases=["r"], help="Resumes playing the current song")
    async def resume(self,ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    @commands.command(name="skip", aliases=["s"], help="Skipped the currently played song")
    async def skip(self,ctx, *args):
        if self.vc != None and self.vc:
            self.vc.stop()
            await self.play_music(ctx)

    @commands.command(name="queue", aliases=["q"], help="Displayed all the song currently in queue")
    async def queue(self, ctx):
        retval = ""

        for i in range(0, len(self.music_queue)):
            if i > 4: break
            retval += self.music_queue[i][0]['title'] + '\n'

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("No music in the queue")

    @commands.command(name="clear", aliases=["c", "bin"], help="Stop the current song and clear the queue")
    async def clear(self,ctx, *args):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Music queue is cleared")   

    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Resumes playing the current song")
    async def leave(self, ctx):
            self.is_playing = False
            self.is_paused = False
            await self.vc.disconnect()

# //////////////////// Bot Event /////////////////////////
# คำสั่ง bot พร้อมใช้งานแล้ว
@bot.event
async def on_ready():
    print("Bot Online!")
    print("555")
    synced = await bot.tree.sync()
    print(f"{len(synced)} command(s)")




# แจ้งคนเข้า -ออกเซิฟเวอร์

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(1140633489520205934) # IDห้อง
    text = f"Welcome to the server, {member.mention}!"

    emmbed = discord.Embed(title = 'Welcome to the server!',
                           description = text,
                           color = 0x66FFFF)

    await channel.send(text) # ส่งข้อความไปที่ห้องนี้
    await channel.send(embed = emmbed)  # ส่ง Embed ไปที่ห้องนี้
    await member.send(text) # ส่งข้อความไปที่แชทส่วนตัวของ member


@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(1140633489520205934)  # IDห้อง
    text = f"{member.name} has left the server!"
    await channel.send(text)  # ส่งข้อความไปที่ห้องนี้



# คำสั่ง chatbot
@bot.event
async def on_message(message):
    mes = message.content # ดึงข้อความที่ถูกส่งมา
    if mes == 'hello':
        await message.channel.send("Hello It's me") # ส่งกลับไปที่ห้องนั่น

    elif mes == 'hi bot':
        await message.channel.send("Hello, " + str(message.author.name))

    await bot.process_commands(message)
    # ทำคำสั่ง event แล้วไปทำคำสั่ง bot command ต่อ




# ///////////////////// Commands /////////////////////
# กำหนดคำสั่งให้บอท

class help_cog(commands.Cog):
    def init(self, bot):
        self.bot = bot

        self.help_message = """
General command:
!help - displays all the aviable commands
!p <keywords> - finds the song on youtube and plays it in your current channel Will resume!
!q - displayes the current music queue
!skip - skips the current song being played
!clear - Stops the music and clears the queue
!leave - Disconnected the bot from the vice channel
!pause - pauses the current song being played or resumes if already paused
!resume - resume playing the current song

"""
        self.text_channel_text = []

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                  self.text_channel_text.append(channel)

        await self.send_to_all(self.help_message)

    async def send_to_all(self, msg):
      for text_channel in self.rext_channel_text:
           await text_channel.send(msg)

    @commands.command(name="help", help="Displays all the avaiable commands")
    async def help(self, ctx):
      await ctx.send(self.help_message)


@bot.command()
async def hello(ctx):
    await ctx.send(f"hello {ctx.author.name}!")


@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)


# Slash Commands
@bot.tree.command(name='hellobot', description='Replies with Hello')
async def hellocommand(interaction):
    await interaction.response.send_message("Hello It's me BOT DISCORD")


@bot.tree.command(name='name')
@app_commands.describe(name = "What's your name?")
async def namecommand(interaction, name : str):
    await interaction.response.send_message(f"Hello {name}")


# Embeds

@bot.tree.command(name='help', description='Bot Commands')
async def helpcommand(interaction):
    emmbed = discord.Embed(title='Help Me! - Bot Commands',
                           description='Bot Commands',
                           color=0x66FFFF,
                           timestamp= discord.utils.utcnow())
    



    # ใส่ข้อมูล
    emmbed.add_field(name='/hello1', value='Hello Commmand', inline=True)
    emmbed.add_field(name='/hello2', value='Hello Commmand', inline=True)
    emmbed.add_field(name='/hello3', value='Hello Commmand', inline=False)

    emmbed.set_author(name='Author', url='https://www.youtube.com/@maoloop01/channels', icon_url='https://yt3.googleusercontent.com/0qFq3tGT6LVyfLtZc-WCXcV9YyEFQ0M9U5W8qDe36j2xBTN34CJ20dZYQHmBz6aXASmttHI=s900-c-k-c0x00ffffff-no-rj')

    # ใส่รูปเล็ก-ใหญ่
    emmbed.set_thumbnail(url='https://yt3.googleusercontent.com/0qFq3tGT6LVyfLtZc-WCXcV9YyEFQ0M9U5W8qDe36j2xBTN34CJ20dZYQHmBz6aXASmttHI=s900-c-k-c0x00ffffff-no-rj')
    emmbed.set_image(url='https://i.ytimg.com/vi/KZRa9DQzUpQ/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLCfWDgiBYjFJtrUasd5yxmQZJG_cg')

    # Footer เนื้อหาส่วนท้าย
    emmbed.set_footer(text='Footer', icon_url='https://yt3.googleusercontent.com/0qFq3tGT6LVyfLtZc-WCXcV9YyEFQ0M9U5W8qDe36j2xBTN34CJ20dZYQHmBz6aXASmttHI=s900-c-k-c0x00ffffff-no-rj')

    await interaction.response.send_message(embed = emmbed)


server_on()

bot.run(os.getenv('TOKEN'))


