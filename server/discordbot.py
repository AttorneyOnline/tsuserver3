import asyncio
import discord
from discord.ext import commands
from discord.utils import escape_markdown
from discord.errors import Forbidden, HTTPException

class Bridgebot(commands.Bot):
    """
    The AO2 Discord bridge self.
    """
    def __init__(self, server):
        super().__init__(command_prefix='$')
        self.server = server
        self.pending_messages = []
        self.hub_id = 0
        self.area_id = 0

    @classmethod
    def init(bot, server, token=None):
        '''Starts the actual bot'''
        new = bot(server)
        print('Trying to start the Discord Bridge bot...')
        try:
            new.run(token)
            return new
        except Exception as e:
            print(e)
            raise
    
    def queue_message(self, name, message, charname):
        self.pending_messages.append([name, message, None])

    async def on_ready(self, ):
        print('Discord Bridge Successfully logged in.')
        print('Username -> ' + self.user.name)
        print('ID -> ' + str(self.user.id))
        self.guild = self.guilds[0]
        self.channel = discord.utils.get(self.guild.text_channels, name='ao2-listener')
        self.loop.create_task(self.main_thread())
        await self.channel.send('Hi I exist now')

    async def on_message(self, message):
        # don't process our own messages
        if message.author == self:
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
                if hook.user == self.user:
                    webhook = hook
                    break
            if webhook == None:
                webhook = await self.channel.create_webhook(name='AO2_Bridgebot')
            await webhook.send(message, username=name, avatar_url=avatar)
        except Forbidden:
            await self.channel.send('Insufficient permissions.')
        except HTTPException:
            await self.channel.send('HTTP failure.')

    async def main_thread(self):
        await self.wait_until_ready()

        while 1:
            if len(self.pending_messages) > 0:
                self.send_char_message(*self.pending_messages.pop())

            await asyncio.sleep(1) # Wait for one second