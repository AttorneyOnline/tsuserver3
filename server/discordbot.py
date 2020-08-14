import asyncio
import discord
from discord.ext import commands
from discord.errors import Forbidden, HTTPException

class Bridgebot(commands.Bot):
    """
    The AO2 Discord bridge self.
    """
    def __init__(self, server):
        super().__init__(command_prefix='$')
        self.server = server

    @classmethod
    def init(bot, server, token=None):
        '''Starts the actual bot'''
        new = bot(server)
        try:
            new.run(token)
        except Exception as e:
            print(e)

    async def on_ready(self, ):
        print('Successfully logged in.')
        print('Username -> ' + self.user.name)
        print('ID -> ' + str(self.user.id))
        self.guild = self.guilds[0]
        self.channel = discord.utils.get(self.guild.text_channels, name='ao2-listener')
        await self.channel.send('Hi I exist now')

    async def on_message(self, message):
        # don't process our own messages
        if message.author == self:
            return

        if message.content.startswith('thumb me up scotty'):
            channel = message.channel
            await channel.send('Send me that 👍 reaction, mate')

            def check(reaction, user):
                return user == message.author and str(reaction.emoji) == '👍'

            try:
                reaction, user = await self.wait_for('reaction_add', timeout=5.0, check=check)
            except asyncio.TimeoutError:
                await channel.send('👎')
            else:
                await channel.send('👍')

        if message.content.startswith('webhook test'):
            await self.send_char_message('Foo', 'Hello World', 'https://cdn.discordapp.com/attachments/721774936649367644/743714648632721459/Button1_off.png')

        await self.process_commands(message)
    
    async def send_char_message(self, name, message, avatar=''):
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

if __name__ == '__main__':
    Bridgebot.init(None, 'NzIxNzczNDA3Njc0NTY0NzQ5.XuZZ3g.XRHqqMUYJgJWP1X1rD8Lfn_mPnU')