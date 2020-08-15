import asyncio
import discord
from discord.ext import commands
from discord.utils import escape_markdown
from discord.errors import Forbidden, HTTPException

class Bridgebot(commands.Bot):
    """
    The AO2 Discord bridge self.
    """
    def __init__(self, server, target_chanel):
        super().__init__(command_prefix='$')
        self.server = server
        self.pending_messages = []
        self.hub_id = 0
        self.area_id = 0
        self.target_channel = target_chanel

    @staticmethod
    def loop_it_forever(loop):
        loop.run_forever()

    @classmethod
    async def init(self, server, token=None, target_channel='general'):
        '''Starts the actual bot'''
        new = self(server, target_channel)
        server.bridgebot = new
        print('Trying to start the Discord Bridge bot...')
        try:
            await new.start(token)
        except Exception as e:
            print(e)
            raise
    
    def queue_message(self, name, message, charname):
        self.pending_messages.append([name, message, None])

    async def on_ready(self):
        print('Discord Bridge Successfully logged in.')
        print('Username -> ' + self.user.name)
        print('ID -> ' + str(self.user.id))
        self.guild = self.guilds[0]
        self.channel = discord.utils.get(self.guild.text_channels, name=self.target_channel)
        self.loop.create_task(self.main_thread())

    async def on_message(self, message):
        # Screw these loser bots
        if message.author.bot or message.webhook_id != None:
            return
        
        if message.channel != self.channel:
            return

        if not message.content.startswith('$'):
            self.server.send_discord_chat(message.author.name, escape_markdown(message.clean_content), self.hub_id, self.area_id)

        # await self.process_commands(message)
    
    async def send_char_message(self, name, message, avatar=None):
        webhook = None
        try:
            webhooks = await self.channel.webhooks()
            for hook in webhooks:
                if hook.user == self.user or hook.name == 'AO2_Bridgebot':
                    webhook = hook
                    break
            if webhook == None:
                webhook = await self.channel.create_webhook(name='AO2_Bridgebot')
            await webhook.send(message, username=name, avatar_url=avatar)
        except Forbidden:
            print(f'[DiscordBridge] Insufficient permissions - couldnt send char message {name}: {message}')
        except HTTPException:
            print(f'[DiscordBridge] HTTP Failure - couldnt send char message {name}: {message}')

    async def main_thread(self):
        await self.wait_until_ready()

        while 1:
            if len(self.pending_messages) > 0:
                await self.send_char_message(*self.pending_messages.pop())

            await asyncio.sleep(0.25) # Quarter of a second loop