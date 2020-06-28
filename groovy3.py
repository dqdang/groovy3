import asyncio
import dbhandler as db
from datetime import datetime
import discord
from discord.ext import commands
import os
import pytz
import time

# SERVER = os.getenv("DISCORD_SERVER")
CHANNEL_NAME = os.getenv("CHANNEL_NAME")
TOKEN = os.getenv("DISCORD_TOKEN")
P_ROLE = os.getenv("P_ROLE")
W_ROLE = os.getenv("W_ROLE")

server_channels = {}  # Server channel cache
p_on = False
p_seen = {"before": None, "after": None, "switched": None}
client = discord.Client()


def get_p():
    """
    Return my boy's last seen location with a timestamp
    """
    # if state == "before":
    #     return p_seen["before"]
    # if state == "after":
    #     return p_seen["after"]
    # if state == "switched":
    #     return p_seen["switched"]

    return p_seen["after"]


def set_p(timestamp):
    """
    Set my boy's last seen location with a timestamp

    :param timestamp: The time and message to save
    """
    if "joined" in timestamp:
        p_seen["before"] = timestamp
    elif "switched" in timestamp:
        p_seen["switched"] = timestamp
    # elif "left" in timestamp:
    #     p_seen["after"] = timestamp
    else:
        p_seen["after"] = timestamp

    return


def find_channel(server, refresh=False):
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


def find_role(member, key):
    """
    Find and return the role to pass the message to.

    :param server: The server to find the role for.
    :param key: The role to select
    """
    if not member:
        return None

    for role in member.roles:
        if role.name == key:
            return role

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
    global p_on
    tz_CE = pytz.timezone('Canada/Eastern')
    state = ""
    delay = 5

    w_member_role = find_role(member, W_ROLE)
    p_member_role = find_role(member, P_ROLE)

    if w_member_role or p_member_role or member.display_name == "Groovy Bot 3" or member.display_name == "JoyJenerator":
        try:
            server = after.channel.guild
        except:
            server = before.channel.guild
        channel = find_channel(server)

        voice_channel_before = before.channel
        voice_channel_after = after.channel

        if voice_channel_before == voice_channel_after:
            # No change
            return

        datetime_CE = datetime.now(tz_CE).strftime("%H:%M:%S %p %Z")
        if voice_channel_before == None:
            if p_member_role:
                p_on = True
            # The member was not on a voice channel before the change
            msg = "%s joined voice channel _%s_ at %s" % (
                member.display_name, voice_channel_after.name, datetime_CE)
            state = "before"
        else:
            # The member was on a voice channel before the change
            if voice_channel_after == None:
                if p_member_role:
                    p_on = False
                # The member is no longer on a voice channel after the change
                msg = "%s left voice channel _%s_ at %s" % (
                    member.display_name, voice_channel_before.name, datetime_CE)
                state = "after"
            else:
                # The member is still on a voice channel after the change
                msg = "%s switched from voice channel _%s_ to _%s_ at %s" % (
                    member.display_name, voice_channel_before.name, voice_channel_after.name, datetime_CE)
                state = "switched"

        if p_member_role or member.display_name == "JoyJenerator":
            print("Logged {} for {}".format(msg, p_member_role))
            set_p(msg)

        if (w_member_role or member.display_name == "Groovy Bot 3") and state == "before" and not p_on:
            # Try to log the voice event to the channel
            try:
                msg = get_p()
                if not msg:
                    msg = db.get_timestamp(2)
                    set_p(msg)
                await channel.send(msg, delete_after=0)
                time.sleep(delay)
                await channel.send(msg, tts=True)
                # for i in range(15):
                #     await channel.send(w_member_role.mention)
            except:
                # No message could be sent to the channel; force refresh the channel cache and try again
                channel = find_channel(server, refresh=True)
                if channel == None:
                    # The channel could not be found
                    print("Error: channel #%s does not exist on server %s." %
                          (CHANNEL_NAME, server))
                else:
                    # Try sending a message again
                    try:
                        msg = get_p()
                        if not msg:
                            msg = db.get_timestamp(2)
                            set_p(msg)
                        await channel.send(msg, delete_after=0)
                        time.sleep(delay)
                        await channel.send(msg, tts=True)
                        # for i in range(15):
                        #     await channel.send(w_member_role.mention)
                    except discord.DiscordException as exception:
                        print("Error: no message could be sent to channel #%s on server %s. Exception: %s" % (
                            CHANNEL_NAME, server, exception))


def main():
    try:
        client.run(TOKEN)
    finally:
        if not db.user_exists(2):
            db.insert_user(2, get_p())
        else:
            db.change_timestamp(2, get_p())


if __name__ == "__main__":
    main()
