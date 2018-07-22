import discord
import asyncio
from discord.ext import commands
import json
from json.decoder import JSONDecodeError


DESCRIPTION = """This bot is used to ping helpers while also preventing spamming of pings in the APStudents discord.
It was created by @jjam912#2180 and @ACT Inc.#2590
You can find our github at https://github.com/APStudentsReddit/ping_manager/
This was written using discord.py rewrite.
"""

# This bot is only meant to be run on one server, so hardcoding this id seems fine (tell me if it isn't).
GUILD_ID = 467170920155316235     # Currently set to Bot Testing
KEY_ALIASES = "aliases"
KEY_PREFIX = "prefix"
KEY_TIMEOUT = "timeout_length"

bot = commands.Bot(description=DESCRIPTION, command_prefix="!")
bot.remove_command("help")

helper_roles = {}   # See load_data()
blacklisted_users = []
users_on_timeout = {}
users_on_confirmation = []
users_to_remind = []

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
HELP_MESSAGE = """To ping helpers, use: `{0}ping <helper alias>`
Be careful when using this command! 
It will ping all helpers of that role, and you will not be able to ping again for """ \
               + str(TIMEOUT_TIME // 60) + """ minutes.

To check how much longer until you can ping a helper use: `{0}time`
To request to receive a reminder DM when you can once again ping a helper use: `{0}remind`

In order to ping a role, you must use one that role's aliases. 
To find the aliases for all the roles use: `{0}alias`

*Below are mod-only commands*:

To completely blacklist a user from pinging helpers use: `{0}blacklist <user's mention>`
To unblacklist a user from pinging helpers use: `{0}unblacklist <user's mention>`
To get all members who are blacklisted, use: `{0}getblacklist`
To change the prefix of commands on your server use: `{0}setprefix <new_prefix>`
To change the length of the timeout on your server use: `{0}settimeout <new timeout in seconds>`
To reset a user's timeout and allowing to ping a helper use: `{0}resetuser <user's mention>`
To add an alias to a helper role use: `{0}addalias`
To remove an alias from a helper role use: `{0}removealias`

**NOTE:** At the request of bork, Computer Science A, Home Economics, and Calculus Helpers will not receive any pings.
Do not try to ping these roles; it will not work.

If you wish, you may refer to the command table below.
"""

COMMAND_TABLE = \
    """```
    ________________________________________________________________________
    |   Command            |       Description         |   Access Level    |
    |----------------------+---------------------------+-------------------|
    |   ping <alias>       |   Pings a helper          |   Everyone        |
    |   time               |   Sends cooldown time     |   Everyone        |
    |   remind             |   Reminds when can ping   |   Everyone        |
    |----------------------+---------------------------+-------------------|
    |   aliases            |   Shows all aliases       |   Everyone        |
    |   help               |   Shows this              |   Everyone        |
    |----------------------+---------------------------+-------------------|
    |   blacklist <user>   |   Bans user from pinging  |   Moderator       |
    |   unblacklist <user> |   Unbans user             |   Moderator       |
    |   getblacklist       |   Lists names of banned   |   Moderator       |
    |   setprefix <prefix> |   Sets bot prefix         |   Moderator       |
    |   settimeout <time>  |   Sets bot timeout (sec)  |   Moderator       |
    |   resetuser <user>   |   Resets user's cooldown  |   Moderator       |
    |   addalias           |   Adds an alias           |   Moderator       |
    |   removealias        |   Removes an alias        |   Moderator       |
    |______________________|___________________________|___________________|
    Cooldown Time: {0} minutes
    Current prefix: {1}```"""


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


@bot.event
async def on_message(message):
    """
    Handles and interprets all messages sent by the discord and determines if they are commands.

    Only accepts messages from a specific guild id because it's meant to only run on one server.
    This is hopefully to prevent any manipulation of the blacklist from other servers.
    Also makes commands case insensitive.

    Parameters
    ----------
    message : Message
        Any message sent that the bot can read.

    Returns
    -------
    None
    """

    if message.guild:
        if message.guild.id != GUILD_ID:    # Prevent anyone from accessing the blacklist from another server.
            return

    if message.author in blacklisted_users:     # Disable blacklisted from interacting with bot
        return

    if bot.user.mention in message.content:
        await message.channel.send("My current prefix is {0}".format(bot.command_prefix))
        return

    message.content = message.content.lower()
    await bot.process_commands(message)


@bot.command()
async def help(ctx):
    """DMs bot description and help for the requester."""

    await ctx.author.send(bot.description)
    await ctx.author.send("\n\n" + HELP_MESSAGE.format(bot.command_prefix))
    await ctx.author.send("\n" + COMMAND_TABLE.format(TIMEOUT_TIME, bot.command_prefix))
    await ctx.message.delete()


@bot.command(aliases=["alias"])
async def aliases(ctx):
    """DMs helper aliases to the requester."""

    alias_message = "Alias for helpers:" + "\n"  # See alias command
    for subject in helper_roles.keys():
        alias_message += "* {0:<27}: {1}\n".format(subject, ", ".join(helper_roles[subject]))
    alias_message += "\n"
    for message in split_message(alias_message, embedded=True):
        await ctx.author.send(message)
    await ctx.message.delete()


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

    Returns
    -------
    None
    """

    # See on_message for current implementation
    # if ctx.author in blacklisted_users:
    #     await ctx.send("Sorry, but you are blacklisted from pinging helpers.", delete_after=60)
    #     for _ in range(60):
    #         await asyncio.sleep(1)
    #     await ctx.message.delete()
    #     return

    if ctx.author in users_on_confirmation:
        await ctx.send("Please confirm and cancel your current request before pinging again.", delete_after=30)
        for _ in range(30):
            await asyncio.sleep(1)
        await ctx.message.delete()
        return

    if ctx.author in users_on_timeout and not ctx.author.guild_permissions.manage_guild:
        time_left = users_on_timeout[ctx.author]    # In seconds
        await ctx.send("Sorry {0}, but you still have to wait {1} minutes and {2} seconds"
                       .format(ctx.author.name, time_left // 60, time_left % 60), delete_after=60)
        for _ in range(60):
            await asyncio.sleep(1)
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
        await ctx.send("Timed out!", delete_after=10)
        await confirm_ping.delete()
        await ctx.message.delete()
        del users_on_confirmation[users_on_confirmation.index(ctx.author)]
        return

    # if ctx.author in users_on_confirmation and users_on_confirmation[ctx.author][1] == ctx.message:

    if str(reaction.emoji) == "❌":
        await ctx.send("Canceling request...", delete_after=10)
        await confirm_ping.delete()
        await ctx.message.delete()
        del users_on_confirmation[users_on_confirmation.index(ctx.author)]
        return

    # Member answered Yes
    actual_role = discord.utils.get(ctx.guild.roles, name=helper_role)
    await actual_role.edit(mentionable=True)
    await ctx.send("Ping requested by {0} for {1}".format(ctx.author.mention, actual_role.mention))
    await actual_role.edit(mentionable=False)

    if not ctx.author.guild_permissions.manage_guild:
        users_on_timeout[ctx.author] = TIMEOUT_TIME

    del users_on_confirmation[users_on_confirmation.index(ctx.author)]

    await confirm_ping.delete()
    await ctx.message.delete()


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
    """Informs the member that they will be DMed when they are allowed to ping again."""

    try:
        _ = users_on_timeout[ctx.author]
    except KeyError:
        await ctx.send("{0}, you are currently allowed to ping a helper.".format(ctx.author.name), delete_after=60)
        return

    users_to_remind.append(ctx.author)
    await ctx.send("{0}, you will receive a DM when you are allowed to ping again.".format(ctx.author.name),
                   delete_after=60)
    await ctx.message.delete()


@bot.command()
async def blacklist(ctx, member: discord.Member):
    """Adds a member to the blacklist."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    if member not in blacklisted_users:
        blacklisted_users.append(member)
        await ctx.send("{0} has been blacklisted by {1}.".format(member.name, ctx.author.name))
    else:
        await ctx.send("{0}, {1} was already blacklisted".format(ctx.author.name, member.name))
    await ctx.message.delete()


@bot.command()
async def unblacklist(ctx, member: discord.Member):
    """Removes a member from the blacklist."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    if member in blacklisted_users:
        del blacklisted_users[blacklisted_users.index(member)]
        await ctx.send("{0} was unblacklisted by {1}.".format(member.name, ctx.author.name))
    await ctx.message.delete()


@bot.command()
async def getblacklist(ctx):
    """Sends the blacklist by converting the members to their names."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    if blacklisted_users:
        for message in split_message("{0}, blacklisted members are: " + ", ".join(
                list(map(lambda x: x.name, blacklisted_users))).format(ctx.author.name)):
            await ctx.send(message)
    else:
        await ctx.send("{0}, no members are blacklisted.".format(ctx.author.name))
    await ctx.message.delete()


@bot.command()
async def addalias(ctx):
    """Adds an alias to a helper role after some selections."""

    if not ctx.author.guild_permissions.manage_guild:
        return

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
        await ctx.send("Timed out!", delete_after=10)
        await ctx.message.delete()
        await helper_prompt.delete()
        await helper_choice.delete()
        await alias_prompt.delete()
        return

    if new_alias.content not in helper_roles[helper_name]:
        helper_roles[helper_name].append(new_alias.content)
        await ctx.send("The alias {0} has been added to the {1} Helper aliases by {2}.".format(
            new_alias.content, helper_name, ctx.author.name))
    else:
        await ctx.send("{0}, the alias {1} was already in {2} Helper aliases".format(
            ctx.author.name, new_alias.content, helper_name))

    await ctx.message.delete()
    await helper_prompt.delete()
    await helper_choice.delete()
    await alias_prompt.delete()
    await new_alias.delete()


@bot.command(aliases=["deletealias"])
async def removealias(ctx):
    """Removes an alias from the helper roles after some selections."""

    if not ctx.author.guild_permissions.manage_guild:
        return

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
        await ctx.send("Timed out!", delete_after=10)
        await ctx.message.delete()
        await helper_prompt.delete()
        await helper_choice.delete()
        await alias_prompt.delete()
        return

    try:
        alias_number = int(alias_choice.content) - 1
    except ValueError:
        await ctx.send("Canceling request...", delete_after=10)
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


@bot.command()
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


@bot.command()
async def setprefix(ctx, prefix: str):
    """Changes the prefix of the bot."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    bot.command_prefix = prefix
    await ctx.send("{0} set the bot prefix set to {1}".format(ctx.author.name, prefix))
    await ctx.message.delete()


@bot.command()
async def settimeout(ctx, seconds: int):
    """Set the length of the timeout in seconds."""

    global TIMEOUT_TIME

    if not ctx.author.guild_permissions.manage_guild:
        return
    TIMEOUT_TIME = int(seconds)
    await ctx.send("{0} set the timeout length to {1} minutes and {2} seconds.".format(
        ctx.author.name, seconds // 60, seconds % 60))
    await ctx.message.delete()


@bot.event
async def on_ready():
    """Prints important bot information and sets up background tasks. Converts ids."""

    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name='By ACT Inc. and jjam912'))
    bot.loop.create_task(update_timer())
    convert_ids()


def write_data():
    """Writes the blacklist to a JSON file using the member's ids."""

    with open("blacklist.json", mode="w") as f:
        for i in range(len(blacklisted_users)):
            blacklisted_users[i] = blacklisted_users[i].id
        f.write(json.dumps(blacklisted_users))
        print("Blacklist saved!")

    with open("aliases.json", mode="w", encoding="UTF-8") as f:
        var_dict = {KEY_PREFIX: bot.command_prefix,
                    KEY_TIMEOUT: TIMEOUT_TIME,
                    KEY_ALIASES: helper_roles}
        f.write(json.dumps(var_dict))
        print("Aliases, command prefix, and timeout length saved!")


def load_data():
    """Reads the ids from the blacklist from the JSON file"""

    global blacklisted_users
    global helper_roles
    global TIMEOUT_TIME

    with open("aliases.json", mode="r", encoding="UTF-8") as f:
        print("Loading aliases...")
        try:
            var_dict = json.loads(f.read())
            bot.command_prefix = var_dict[KEY_PREFIX]
            helper_roles = var_dict[KEY_ALIASES]
            TIMEOUT_TIME = var_dict[KEY_TIMEOUT]
        except JSONDecodeError:
            print("Aliases failed to load.")
            raise
        else:
            print("Aliases loaded successfully.")

    print("Loading data...")
    with open("blacklist.json", mode="r") as f:
        try:
            blacklisted_users = json.loads(f.read())

        except JSONDecodeError:
            print("Invalid data found.")
            print("File contents: " + f.read())
        else:
            print("Data loaded successfully.")


def convert_ids():
    """Converts all ids of the server from the blacklist by using the GUILD_ID constant."""

    global blacklisted_users
    print("Converting ids")

    for i in range(len(blacklisted_users) - 1, -1, -1):
        member = bot.get_guild(GUILD_ID).get_member(blacklisted_users[i])
        if member is None:
            del blacklisted_users[i]
        else:
            blacklisted_users[i] = member
    else:
        print("Members converted from ids successfully.")


@asyncio.coroutine
def main_task():
    """Login"""
    with open("token.txt", mode="r") as f:
        token = f.read()
    yield from bot.login(token)
    yield from bot.connect()


loop = asyncio.get_event_loop()

try:
    load_data()
    loop.run_until_complete(main_task())
except Exception as e:
    print(e)
    loop.run_until_complete(bot.logout())
finally:
    loop.close()
    write_data()
