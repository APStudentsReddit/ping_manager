import discord
import asyncio
from discord.ext import commands
import json
from json.decoder import JSONDecodeError
import sys
import traceback


DESCRIPTION = """This bot is used to ping helpers while also preventing spamming of pings in the APStudents discord.
It was created by @jjam912#2180 and @ACT Inc.#2590
https://github.com/APStudentsReddit/ping_manager/
This was written using discord.py rewrite.
"""

# This bot is only meant to be run on one server, so hardcoding this id seems fine
GUILD_ID = 420053499707916288     # Currently set to JJam912's Bot Army

# For the settings file
KEY_PREFIX = "prefix"
KEY_TIMEOUT = "timeout_length"

bot = commands.Bot(description=DESCRIPTION, command_prefix="!")
bot.remove_command("help")      # We implement our own

helper_roles = {}       # Drawn from aliases.json

blacklisted_users = []

users_on_confirmation = []
pending_pings = {}

users_on_timeout = {}
users_to_remind = []

ping_frequency = {}     # Keeps track of stats

AMBIGUOUS = "Ambiguous role"
DISABLED = "Disabled role"
HELPER_SUFFIX = " Helper"

TIMEOUT_TIME = 3600

DISABLED_ROLES = {
                    "Calculus": ["calculus", "ap calc", "calc ab", "calc bc", "calc", "ab calc",
                                 "bc calc", "calculus bc", "calculus ab"],
                    "Computer Science": ["ap computer science", "ap computer science helper",
                                         "ap csa", "computer science a", "comp sci a", "csa"],
                    "Home Economics": ["home econ", "home economics", "ap home econ", "ap home economics"]
                 }

AMBIGUOUS_ROLES = {
                    "physics": ["Physics 1", "Physics 2", "Physics C Mech", "Physics C E/M"],
                    # "spanish": ["Spanish Language", "Spanish Literature"],
                    # "comp sci": ["Computer Science", "Computer Science Principles"]
                    "economics": ["Macroeconomics", "Microeconomics"],
                    "econ": ["Macroeconomics", "Microeconomics"],
                    "art": ["Art History", "Studio Art"],
                    "gov": ["U.S Government", "Comp. Government"],
                    "government": ["U.S Government", "Comp. Government"],
                  }

# See alias command for alias message
HELP_MESSAGE = """
{0}

**NOTE:** At the request of bork, Computer Science A, Home Economics, and Calculus Helpers will not receive any pings.
```
_________________________________________________________________________
|   Command            |        Description         |   Access Level    |
|----------------------+----------------------------+-------------------|
|   ping <alias>       |    Pings a helper          |   Everyone        |
|   pending <alias>    |    Links to active pings   |   Everyone        |
|   time               |    Sends cooldown time     |   Everyone        |
|   remind             |    DM's when can ping      |   Everyone        |
|----------------------+----------------------------+-------------------|
|   help               |    Shows this              |   Everyone        |
|   aliases            |    Shows all aliases       |   Everyone        |
|----------------------+----------------------------+-------------------|
|   blacklist <@user>  |    Bans user from pinging  |   Moderator       |
|   unblacklist <@user>|    Unbans user             |   Moderator       |
|   getblacklist       |    Lists names of banned   |   Moderator       |
|   setprefix <prefix> |    Sets bot prefix         |   Moderator       |
|   settimeout <time>  |    Sets bot timeout (sec)  |   Moderator       |
|   resetuser <@user>  |    Resets user's cooldown  |   Moderator       |
|   addalias           |    Adds an alias           |   Moderator       |
|   removealias        |    Removes an alias        |   Moderator       |
|   stats              |    DM's ping frequencies   |   Moderator       |
|______________________|____________________________|___________________|
Cooldown Time: {1} minutes and {2} seconds
Current prefix: {3}```"""


def convert_alias(alias):
    """
    Converts an alias name to the proper Helper name.

    Parameters
    ----------
    alias : str
        An alias for the wanted helper name.

    Returns
    -------
    str
        The helper name, "ambiguous role", "disabled role", or "" (if none are found).
    """

    for role in helper_roles:
        if alias in helper_roles[role]:
            return role + HELPER_SUFFIX
    if alias in AMBIGUOUS_ROLES:
        return AMBIGUOUS
    for role in DISABLED_ROLES:
        if alias in DISABLED_ROLES[role]:
            return DISABLED
    return None


def split_message(message, embedded=False, language: str=""):
    """
    Splits a message into more messages of size less than 2000 characters.

    This is to bypass the Discord 2000 character limit.

    Parameters
    ----------
    message : str
        A long message to split up.
    embedded : bool
        Whether to embed the message in code format (surrounded by ```)
    language : str
        Name of the language of the code.

    Returns
    -------
    list of str
        All messages to send.
    """

    lines = message.split("\n")
    curr_message = ""
    messages = []

    if embedded:
        curr_message += "```" + language + "\n"
        for line in lines:
            if len(line) + len(curr_message) + 5 > 2000:
                messages.append(curr_message + "```")
                curr_message = "```" + language + line + "\n"
            else:
                curr_message += line + "\n"
        messages.append(curr_message + "```")

    else:
        for line in lines:
            if len(line) + len(curr_message) + 2 > 2000:
                messages.append(curr_message)
                curr_message = line + "\n"
            else:
                curr_message += line + "\n"
        messages.append(curr_message)
    return messages


@bot.event
async def on_message(message):
    """
    Handles and interprets all messages sent by the discord and determines if they are commands.

    Only accepts messages from a specific guild id because it's meant to only run on one server.
    This is hopefully to prevent any manipulation of the blacklist from other servers.
    Also makes commands case insensitive.
    """

    if message.guild:
        if message.guild.id != GUILD_ID:    # Prevent anyone from using the bot in another server
            return

    if message.author in blacklisted_users or message.author.id in blacklisted_users:
        # Disable blacklisted from interacting with bot
        return

    if bot.user.mention in message.content:
        await message.channel.send("My current prefix is {0}".format(bot.command_prefix), delete_after=60)
        return

    message.content = message.content.lower()
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    """The event triggered when an error is raised while invoking a command.
    ctx   : Context
    error : Exception"""

    if hasattr(ctx.command, 'on_error'):
        return

    ignored = (commands.CommandNotFound, commands.UserInputError)
    error = getattr(error, 'original', error)

    if isinstance(error, ignored):
        return

    elif isinstance(error, commands.NoPrivateMessage):
        try:
            return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
        except:
            pass

    elif isinstance(error, commands.BadArgument):
        if ctx.command.qualified_name == "settimeout":
            return await ctx.send("Please enter a time in seconds.")
        elif ctx.command.qualified_name in ["blacklist", "unblacklist", "resetuser"]:
            return await ctx.send("Please enter a valid member.")

    print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
    traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


@bot.command()
async def help(ctx):
    """DM's bot description and help for the requester."""

    await ctx.author.send(HELP_MESSAGE.format(DESCRIPTION, TIMEOUT_TIME//60, TIMEOUT_TIME % 60, bot.command_prefix))
    await ctx.message.delete()


@bot.command(aliases=["alias"])
async def aliases(ctx):
    """DM's helper aliases to the requester."""

    alias_message = "Alias for helpers:" + "\n"  # See alias command
    for subject in helper_roles.keys():
        alias_message += "* {0:<27}: {1}\n".format(subject, ", ".join(helper_roles[subject]))
    alias_message += "\n"
    for message in split_message(alias_message, embedded=True):
        await ctx.author.send(message)
    await ctx.message.delete()


@commands.guild_only()
@bot.command()
async def ping(ctx, *, alias: str):
    """
    Pings a helper role after some confirmation and puts the user on cooldown.

    In order for a member to ping, they must:
        1. Not be on the blacklist.
        2. Not be on timeout.
        3. Refer clearly to an alias.
        4. Confirm that they are going to ping all helpers.
    Also, the bot will delete several messages if the ping is confirmed to reduce channel spam.

    Parameters
    ----------
    ctx : Context
        Context of the message.
    alias : str
        An alias for a helper role.
    """

    if ctx.author in users_on_confirmation:
        await ctx.send("{0}, please confirm or cancel your current request before pinging again.".format(
            ctx.author.name), delete_after=30)
        await ctx.message.delete()
        return

    if ctx.author in users_on_timeout and not ctx.author.guild_permissions.manage_guild:
        time_left = users_on_timeout[ctx.author]    # In seconds
        await ctx.send("Sorry {0}, but you still have to wait {1} minutes and {2} seconds"
                       .format(ctx.author.name, time_left // 60, time_left % 60), delete_after=60)
        await ctx.message.delete()
        return

    helper_role = convert_alias(alias)

    if helper_role is None:
        await ctx.send("Sorry {0}, invalid alias.".format(ctx.author.name), delete_after=60)
        for _ in range(60):
            await asyncio.sleep(1)
        await ctx.message.delete()
        return

    if helper_role == AMBIGUOUS:
        ambiguous_role_response = "There are multiple helper roles that you could be referring to with." \
                                  "  Please specify by using one of the below roles and try again.\n```\n"
        for r in AMBIGUOUS_ROLES[alias]:
            ambiguous_role_response += "\n* " + r + ": " + ", ".join(helper_roles[r]) + "\n"
        ambiguous_role_response += "```"

        await ctx.send(ctx.author.name + ", " + ambiguous_role_response, delete_after=60)
        for _ in range(60):
            await asyncio.sleep(1)
        await ctx.message.delete()
        return

    if helper_role == DISABLED:
        disabled_role_response = "Sorry, but that helper role has been disabled at the request of the moderators."
        await ctx.send(ctx.author.name + ", " + disabled_role_response, delete_after=60)
        for _ in range(60):
            await asyncio.sleep(1)
        await ctx.message.delete()
        return

    # We may now assume helper_role is verified.
    confirm_ping = await ctx.send("{0}, You are about to ping all the {1}s on this server. " 
                                  "Please make sure you have clearly elaborated your question and/or shown all work. \n"
                                  "If you have done so, react with ✅ in the next 30 seconds. \n"
                                  "To cancel, react with ❌.\n"
                                  "After 30 seconds, this message will be deleted and your request will be canceled."
                                  .format(ctx.author.name, helper_role))
    
    # Add the new request to the list of requests.
    users_on_confirmation.append(ctx.author)

    # Add the two options for reacts to make it easier for the user to click their choice.
    await confirm_ping.add_reaction("✅")
    await confirm_ping.add_reaction("❌")

    def ping_check(react, member):
        """Determines if the confirmation is a valid response."""
        if member == ctx.author:
            if str(react.emoji) == "✅" or str(react.emoji) == "❌":
                return True
        return False

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30, check=ping_check)
    except asyncio.TimeoutError:
        await ctx.send("Timed out!", delete_after=5)
        await confirm_ping.delete()
        await ctx.message.delete()
        del users_on_confirmation[users_on_confirmation.index(ctx.author)]
        return

    if str(reaction.emoji) == "❌":
        await ctx.send("Canceling request...", delete_after=5)
        await confirm_ping.delete()
        await ctx.message.delete()
        del users_on_confirmation[users_on_confirmation.index(ctx.author)]
        return

    del users_on_confirmation[users_on_confirmation.index(ctx.author)]
    # Member answered Yes
    actual_role = discord.utils.get(ctx.guild.roles, name=helper_role)
    await actual_role.edit(mentionable=True)
    actual_ping = await ctx.send("Ping requested by {0} for {1}\nReact with ✅ when the problem is solved.\n"
                                 "Note: Anyone can react with ✅ and it cannot be revoked.".format(
                                  ctx.author.mention, actual_role.mention))
    await actual_role.edit(mentionable=False)

    if not ctx.author.guild_permissions.manage_guild:
        users_on_timeout[ctx.author] = TIMEOUT_TIME

    await confirm_ping.delete()
    await ctx.message.delete()

    pending_pings[helper_role].append(actual_ping)
    await actual_ping.add_reaction("✅")

    try:
        ping_frequency[helper_role] += 1
    except KeyError:
        ping_frequency[helper_role] = 1

    def done_check(react, ruser):
        """Determines if someone says the problem is solved."""

        if ruser == bot.user:
            return False

        if str(react.emoji) == "✅":
            return True
        return False

    # We do not delete the actual ping message since that gives people safety of deleting their ping.
    await bot.wait_for("reaction_add", check=done_check)
    del pending_pings[helper_role][pending_pings[helper_role].index(actual_ping)]


@bot.command()
async def time(ctx):
    """Tells the member how much time they have left before being able to ping again."""

    try:
        time_left = users_on_timeout[ctx.author]  # In seconds
        await ctx.send("{0}, you still have to wait {1} minutes and {2} seconds"
                       .format(ctx.author.name, time_left // 60, time_left % 60), delete_after=60)
    except KeyError:
        await ctx.send("{0}, you are currently allowed to ping a helper.".format(ctx.author.name), delete_after=60)
    await ctx.message.delete()


@bot.command(aliases=["notify"])
async def remind(ctx):
    """Informs the member that they will be DM'ed when they are allowed to ping again."""

    try:
        _ = users_on_timeout[ctx.author]
    except KeyError:
        await ctx.send("{0}, you are currently allowed to ping a helper.".format(ctx.author.name), delete_after=60)
        return

    users_to_remind.append(ctx.author)
    await ctx.send("{0}, you will receive a DM's when you are allowed to ping again.".format(ctx.author.name),
                   delete_after=60)
    await ctx.message.delete()


@commands.guild_only()
@bot.command(alieses=["pings"])
async def pending(ctx, *, alias: str):
    """Prints all links to pending pings."""

    helper_role = convert_alias(alias)

    if helper_role is None:
        await ctx.send("Sorry {0}, invalid alias.".format(ctx.author.name), delete_after=60)
        for _ in range(60):
            await asyncio.sleep(1)
        await ctx.message.delete()
        return

    if helper_role == AMBIGUOUS:
        ambiguous_role_response = "There are multiple helper roles that you could be referring to with." \
                                  "  Please specify by using one of the below roles and try again.\n```\n"
        for r in AMBIGUOUS_ROLES[alias]:
            ambiguous_role_response += "\n* " + r + ": " + ", ".join(helper_roles[r]) + "\n"
        ambiguous_role_response += "```"

        await ctx.send(ctx.author.name + ", " + ambiguous_role_response, delete_after=60)
        for _ in range(60):
            await asyncio.sleep(1)
        await ctx.message.delete()
        return

    if helper_role == DISABLED:
        disabled_role_response = "Sorry, but that helper role has been disabled at the request of the moderators."
        await ctx.send(ctx.author.name + ", " + disabled_role_response, delete_after=60)
        for _ in range(60):
            await asyncio.sleep(1)
        await ctx.message.delete()
        return

    if pending_pings[helper_role]:
        await ctx.send("{0}, active pings for {1}s are:\n {2}".
                       format(ctx.author.name, helper_role,
                              "\n".join(list(map(lambda x: x.jump_url, pending_pings[helper_role])))), delete_after=300)
    else:
        await ctx.send("{0}, there are no active pings for {1}s.".format(ctx.author.name, helper_role), delete_after=30)
    await ctx.message.delete()


@commands.has_permissions(manage_guild=True)
@bot.command()
async def blacklist(ctx, member: discord.Member):
    """Adds a member to the blacklist."""

    if member not in blacklisted_users and member.id not in blacklisted_users:
        blacklisted_users.append(member)
        await ctx.send("{0} has been blacklisted by {1}.".format(member.mention, ctx.author.name))
    else:
        await ctx.send("{0}, {1} was already blacklisted".format(ctx.author.name, member.name))
    await ctx.message.delete()


@commands.has_permissions(manage_guild=True)
@bot.command()
async def unblacklist(ctx, member: discord.Member):
    """Removes a member from the blacklist."""

    if member in blacklisted_users or member.id in blacklisted_users:
        try:
            del blacklisted_users[blacklisted_users.index(member)]
        except ValueError:
            pass
        try:
            del blacklisted_users[blacklisted_users.index(member.id)]
        except ValueError:
            pass

        await ctx.send("{0} was unblacklisted by {1}.".format(member.mention, ctx.author.name))
    else:
        await ctx.send("{0}, {1} was already unblacklisted.".format(ctx.author.name, member.name))
    await ctx.message.delete()


@commands.has_permissions(manage_guild=True)
@bot.command()
async def getblacklist(ctx):
    """Sends the blacklist by converting the members to their names."""

    if blacklisted_users:
        for message in split_message(ctx.author.name + ", blacklisted members are: " + ", ".join(
                list(map(lambda x: x.name if not isinstance(x, int) else str(ctx.guild.get_member(x)),
                         blacklisted_users)))):
            await ctx.send(message)
    else:
        await ctx.send("{0}, no members are blacklisted.".format(ctx.author.name))
    await ctx.message.delete()


@commands.has_permissions(manage_guild=True)
@bot.command()
async def addalias(ctx):
    """Adds an alias to a helper role after some selections."""

    helper_message = "Please choose the number of the helper role you want to add to:\n" \
                     "To cancel, type 'cancel'\n\n"
    for i, alias in enumerate(helper_roles.keys()):
        helper_message += "{0}: {1}\n".format(i+1, alias)

    helper_prompt = await ctx.send(helper_message)
    cancels = ["exit", "cancel", "quit", "stop"]

    def helper_check(message):
        """Checks whether the user quit or selected a valid number in the helper role index."""
        if message.author == ctx.author and message.channel == ctx.channel:
            if message.content in cancels:
                return True
            try:
                select = int(message.content)
            except ValueError:
                return False
            if select in range(1, len(helper_roles.keys()) + 1):
                return True
        return False

    try:
        helper_choice = await bot.wait_for("message", check=helper_check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.send("Timed out!", delete_after=10)
        await ctx.message.delete()
        await helper_prompt.delete()
        return

    try:
        helper_number = int(helper_choice.content) - 1
    except ValueError:
        await ctx.send("Canceling request...", delete_after=10)
        await ctx.message.delete()
        await helper_prompt.delete()
        await helper_choice.delete()
        return

    helper_name = list(helper_roles.keys())[helper_number]
    alias_prompt = await ctx.send("Now enter your alias name:\n"
                                  "To cancel, type 'cancel'")

    def author_check(message):
        """Checks whether the message is by the original requester."""
        if message.author == ctx.author and message.channel == ctx.channel:
            return True
        return False

    try:
        new_alias = await bot.wait_for('message', check=author_check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.send("Timed out!", delete_after=5)
        await ctx.message.delete()
        await helper_prompt.delete()
        await helper_choice.delete()
        await alias_prompt.delete()
        return

    if new_alias.content in cancels:
        await ctx.send("Canceling request...", delete_after=5)
        await ctx.message.delete()
        await helper_prompt.delete()
        await helper_choice.delete()
        await alias_prompt.delete()
        await new_alias.delete()
        return

    if new_alias.content.lower() not in helper_roles[helper_name]:
        helper_roles[helper_name].append(new_alias.content.lower())
        await ctx.send("The alias {0} has been added to the {1} Helper aliases by {2}.".format(
            new_alias.content.lower(), helper_name, ctx.author.name))
    else:
        await ctx.send("{0}, the alias {1} was already in {2} Helper aliases".format(
            ctx.author.name, new_alias.content.lower(), helper_name))

    await ctx.message.delete()
    await helper_prompt.delete()
    await helper_choice.delete()
    await alias_prompt.delete()
    await new_alias.delete()


@commands.has_permissions(manage_guild=True)
@bot.command(aliases=["deletealias"])
async def removealias(ctx):
    """Removes an alias from the helper roles after some selections."""

    helper_message = "Please choose the number of the helper role you want to remove from:\n" \
                     "To cancel, type 'cancel'\n\n"
    for i, alias in enumerate(helper_roles.keys()):
        helper_message += "{0}: {1}\n".format(i + 1, alias)

    helper_prompt = await ctx.send(helper_message)
    cancels = ["exit", "cancel", "quit", "stop"]

    def helper_check(message):
        """Checks whether the user quit or selected a valid number in the helper role index."""
        if message.author == ctx.author and message.channel == ctx.channel:
            if message.content in cancels:
                return True
            try:
                select = int(message.content)
            except ValueError:
                return False
            if select in range(1, len(helper_roles.keys()) + 1):
                return True
        return False

    try:
        helper_choice = await bot.wait_for("message", check=helper_check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.send("Timed out!", delete_after=5)
        await ctx.message.delete()
        await helper_prompt.delete()
        return

    try:
        helper_number = int(helper_choice.content) - 1
    except ValueError:
        await ctx.send("Canceling request...", delete_after=5)
        await ctx.message.delete()
        await helper_prompt.delete()
        await helper_choice.delete()
        return

    helper_name = list(helper_roles.keys())[helper_number]

    alias_message = "Now select the number of the alias you want to remove:\n" \
                    "To cancel, type 'cancel'\n\n"
    for i, alias in enumerate(helper_roles[helper_name]):
        alias_message += "{0}: {1}\n".format(i + 1, alias)

    alias_prompt = await ctx.send(alias_message)

    def alias_check(message):
        """Checks whether the author quit or selected a valid number in the helper alias index."""
        if message.author == ctx.author and message.channel == ctx.channel:
            if message.content in cancels:
                return True
            try:
                select = int(message.content)
            except ValueError:
                return False
            if select in range(1, len(helper_roles[helper_name]) + 1):
                return True
        return False

    try:
        alias_choice = await bot.wait_for('message', check=alias_check, timeout=60)
    except asyncio.TimeoutError:
        await ctx.send("Timed out!", delete_after=5)
        await ctx.message.delete()
        await helper_prompt.delete()
        await helper_choice.delete()
        await alias_prompt.delete()
        return

    try:
        alias_number = int(alias_choice.content) - 1
    except ValueError:
        await ctx.send("Canceling request...", delete_after=5)
        await ctx.message.delete()
        await helper_prompt.delete()
        await helper_choice.delete()
        await alias_prompt.delete()
        await alias_choice.delete()
        return

    alias_name = helper_roles[helper_name][alias_number]

    if alias_name in helper_roles[helper_name]:
        del helper_roles[helper_name][alias_number]
        await ctx.send("The alias {0} has been removed from the {1} Helper aliases by {2}.".format(
            alias_name, helper_name, ctx.author.name))
    else:
        await ctx.send("{0}, the alias {1} was not in the {2} Helper aliases.".format(
            ctx.author.name, alias_name, helper_name))

    await ctx.message.delete()
    await helper_prompt.delete()
    await helper_choice.delete()
    await alias_prompt.delete()
    await alias_choice.delete()


@commands.has_permissions(manage_guild=True)
@bot.command(aliases=["reset"])
async def resetuser(ctx, member: discord.Member):
    """Reset a user's current timeout, allowing them to ping a helper."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    if member in users_on_timeout:
        del users_on_timeout[member]
        await ctx.send("{0} can now ping a helper (reset by {1}).".format(member.name, ctx.author.name))
    else:
        await ctx.send("{0} can already ping helpers (reset by {1}).".format(member.name, ctx.author.name))
    await ctx.message.delete()


@commands.has_permissions(manage_guild=True)
@bot.command(aliases=["prefix"])
async def setprefix(ctx, prefix: str):
    """Changes the prefix of the bot."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    bot.command_prefix = prefix
    await ctx.send("{0} set the bot prefix set to {1}".format(ctx.author.name, prefix))
    await bot.change_presence(activity=discord.Game(name="{0}help for commands!".format(bot.command_prefix)))
    await ctx.message.delete()


@commands.has_permissions(manage_guild=True)
@bot.command(aliases=["settime"])
async def settimeout(ctx, seconds: int):
    """Set the length of the timeout in seconds."""

    global TIMEOUT_TIME

    if not ctx.author.guild_permissions.manage_guild:
        return
    TIMEOUT_TIME = int(seconds)
    await ctx.send("{0} set the timeout length to {1} minutes and {2} seconds.".format(
        ctx.author.name, seconds // 60, seconds % 60))
    await ctx.message.delete()


@commands.has_permissions(manage_guild=True)
@bot.command()
async def stats(ctx):
    """Prints ping frequency of all helper roles that have been pinged"""

    if not ctx.author.guild_permissions.manage_guild:
        return

    roles = sorted(ping_frequency, key=lambda x: x)

    total_pings = sum([ping_frequency[k] for k in roles])

    stats_message = "Percentages of pings out of {0} pings\n\n".format(total_pings)
    for role in roles:
        stats_message += "{0:<34}: ".format(role)
        stats_message += ("{:04." + str(len(str(total_pings)) + 1) + "f}\n").format(ping_frequency[role] / total_pings)

    stats_message += "\nTotal number of pings out of {0} pings\n\n".format(total_pings)
    for role in roles:
        stats_message += "{0:<34}: ".format(role)
        stats_message += "{0}\n".format(ping_frequency[role])

    for message in split_message(stats_message, embedded=True):
        await ctx.author.send(message)
    await ctx.message.delete()


@commands.is_owner()
@bot.command()
async def logout(ctx):
    await ctx.send("Logging out.")
    print("Logging out")
    print("------")
    await bot.logout()


@bot.event
async def on_ready():
    """Prints important bot information and sets up background tasks. Converts ids."""

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name="{0}help for commands!".format(bot.command_prefix)))
    convert_ids()


async def update_timer():
    """Updates all students' cooldown periods every second."""

    while True:
        await asyncio.sleep(1)
        names_to_remove = []
        for member in users_on_timeout:
            users_on_timeout[member] -= 1
            if users_on_timeout[member] <= 0:
                names_to_remove.append(member)
        for member in names_to_remove:
            if member in users_to_remind:
                await member.send("This is your reminder that you are now allowed to ping helpers.")
            del users_on_timeout[member]


def write_data():
    """Writes the blacklist to a JSON file using the member's ids."""

    with open("aliases.json", mode="w", encoding="UTF-8") as f:
        f.write(json.dumps(helper_roles))
        print("Aliases saved!")

    with open("blacklist.json", mode="w") as f:
        for i in range(len(blacklisted_users)):
            try:
                blacklisted_users[i] = blacklisted_users[i].id
            except AttributeError:
                pass
        f.write(json.dumps(blacklisted_users))
        print("Blacklist saved!")

    with open("settings.json", mode="w") as f:
        var_dict = dict()
        var_dict[KEY_PREFIX] = bot.command_prefix
        var_dict[KEY_TIMEOUT] = TIMEOUT_TIME
        f.write(json.dumps(var_dict))
        print("Settings saved!")

    with open("stats.json", mode="w") as f:
        f.write(json.dumps(ping_frequency))
        print("Ping frequency saved!")


def load_data():
    """Reads the ids from the blacklist from the JSON file"""

    global blacklisted_users
    global helper_roles
    global TIMEOUT_TIME
    global ping_frequency
    global pending_pings

    with open("aliases.json", mode="r", encoding="UTF-8") as f:
        try:
            helper_roles = json.loads(f.read())
        except JSONDecodeError:
            print("Aliases failed to load.")
            raise
        else:
            print("Aliases loaded successfully.")

    for alias_list in helper_roles.values():
        alias_list.sort(key=len)

    for role in helper_roles:
        pending_pings[role + HELPER_SUFFIX] = []

    with open("blacklist.json", mode="r") as f:
        try:
            blacklisted_users = json.loads(f.read())

        except JSONDecodeError:
            print("Invalid blacklist found.")
            print("File contents: " + f.read())
        else:
            print("Blacklist loaded successfully.")

    with open("settings.json", mode="r") as f:
        try:
            settings = json.loads(f.read())
            bot.command_prefix = settings[KEY_PREFIX]
            TIMEOUT_TIME = settings[KEY_TIMEOUT]
        except JSONDecodeError:
            print("No settings found.")
            print("File contents: " + f.read())
        else:
            print("Settings loaded successfully.")

    with open("stats.json", mode="r") as f:
        try:
            ping_frequency = json.loads(f.read())

        except JSONDecodeError:
            print("Invalid statistics found.")
            print("File contents: " + f.read())
        else:
            print("Statistics loaded successfully.")


def convert_ids():
    """Converts all ids of the server from the blacklist by using the GUILD_ID constant."""

    global blacklisted_users
    print("Converting ids")

    for i in range(len(blacklisted_users) - 1, -1, -1):
        member = bot.get_guild(GUILD_ID).get_member(blacklisted_users[i])       # Can be None
        if member:
            blacklisted_users[i] = member
        # If it is None, we can just keep the id.
    else:
        print("Members converted from ids successfully.")


@asyncio.coroutine
def main_task():
    """Login and start timer."""

    bot.loop.create_task(update_timer())
    with open("token.txt", mode="r") as f:
        token = f.read()
    yield from bot.login(token)
    yield from bot.connect()


loop = asyncio.get_event_loop()

try:
    load_data()
    loop.run_until_complete(main_task())
except Exception as e:
    print("")
    print(e)
    print("")
    loop.run_until_complete(bot.logout())
finally:
    loop.close()
    write_data()
