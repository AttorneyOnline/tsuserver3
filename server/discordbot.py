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
        channel = discord.utils.get(self.guild.text_channels, name='ao2-listener')
        await channel.send('Hi I exist now')

    async def on_message(self, message):
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
            channel = message.channel
            webhook = None
            try:
                webhooks = await channel.webhooks()
                for hook in webhooks:
                    if hook.user == self.user:
                        webhook = hook
                        break
                if webhook == None:
                    webhook = await channel.create_webhook(name='AO2_Bridgebot')
                await webhook.send('Hello World', username='Foo')#, avatar_url='https://cdn.discordapp.com/attachments/721774936649367644/743714648632721459/Button1_off.png')
            except Forbidden:
                await channel.send('Insufficient permissions.')
            except HTTPException:
                await channel.send('HTTP failure.')

        await self.process_commands(message)

if __name__ == '__main__':
    Bridgebot.init(None, 'LOL IMAGINE POSTING YOUR TOKEN')