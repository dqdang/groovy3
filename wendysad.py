import asyncio
import discord
from discord.ext import commands
import os
from datetime import datetime

CHANNEL_NAME = os.getenv("CHANNEL_NAME")
# SERVER = os.getenv("DISCORD_SERVER")
TOKEN = os.getenv('DISCORD_TOKEN')

server_channels = {} # Server channel cache
client = discord.Client()

def find_channel(server, refresh = False):
    """
    Find and return the channel to log the voice events to.

    :param server: The server to find the channel for.
    :param refresh: Whether to refresh the channel cache for this server.
    """
    if not refresh and server in server_channels:
        return server_channels[server]

    for channel in client.get_all_channels():
        if channel.guild == server and channel.name == CHANNEL_NAME:
            print("%s: refreshed destination log channel" % server)
            server_channels[server] = channel
            return channel

    return None

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_voice_state_update(member, before, after):
    """
    Called when the voice state of a member on a server changes.

    :param before: The state of the member before the change.
    :param after: The state of the member after the change.
    """
    if member.display_name == "Dango Kuhaku" or member.display_name == "wendysad":
        server = after.channel.guild
        channel = find_channel(server)

        voice_channel_before = before.channel
        voice_channel_after = after.channel

        if voice_channel_before == voice_channel_after:
            # No change
            return

        if voice_channel_before == None:
            # The member was not on a voice channel before the change
            now = datetime.now().time()
            msg = "%s joined voice channel _%s_ at %s" % (member.display_name, voice_channel_after.name, now)
        else:
            # The member was on a voice channel before the change
            if voice_channel_after == None:
                # The member is no longer on a voice channel after the change
                now = datetime.now().time()
                msg = "%s left voice channel _%s_ at %s" % (member.display_name, voice_channel_before.name, now)
            else:
                # The member is still on a voice channel after the change
                now = datetime.now().time()
                msg = "%s switched from voice channel _%s_ to _%s_ at %s" % (member.display_name, voice_channel_before.name, voice_channel_after.name, now)

        # Try to log the voice event to the channel
        try:
            await channel.send(msg)
        except:
            # No message could be sent to the channel; force refresh the channel cache and try again
            channel = find_channel(server, refresh = True)
            if channel == None:
                # The channel could not be found
                print("Error: channel #%s does not exist on server %s." % (CHANNEL_NAME, server))
            else:
                # Try sending a message again
                try:
                    # await client.send_message(channel, msg)
                    await channel.send(msg)
                except discord.DiscordException as exception:
                    print("Error: no message could be sent to channel #%s on server %s. Exception: %s" % (CHANNEL_NAME, server, exception))

client.run(TOKEN)
