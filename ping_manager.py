import discord
import asyncio
from discord.ext import commands
import json
from json.decoder import JSONDecodeError


DESCRIPTION = """This bot is used to ping helpers while also preventing spamming of pings in the APStudents discord.
It was created by @jjam912#2180 and @ACT Inc.#2590
You can find our github at https://github.com/APStudentsReddit/ping_manager/tree/rewrite
This was written using discord.py rewrite.
"""

# This bot is only meant to be run on one server, so hardcoding this id seems fine (tell me if it isn't).
GUILD_ID = 420053499707916288     # Currently set to JJam912's Bot Army
KEY_BLACKLIST = "blacklist"
KEY_PREFIX = "prefix"

bot = commands.Bot(description=DESCRIPTION, command_prefix="!")
bot.remove_command("help")

blacklisted_users = []
users_on_timeout = {}
users_to_remind = []

AMBIGUOUS = "Ambiguous role"
HELPER_SUFFIX = " Helper"

TIMEOUT_TIME = 60

HELPER_ROLES = \
    {
        "Art History": ["ap art history", "art history"],
        "Biology": ["biology", "ap bio", "ap biology", "bio"],
        "Capstone": ["capstone", "ap capstone"],
        "Chemistry": ["chem", "chemistry", "ap chem", "ap chemistry"],
        "Chinese": ["ap chinese", "chinese", "中文"],
        "Comp. Government": ["comparative government", "comp gov", "comp. gov", "gov comp"],
        "Computer Science Principles": ["ap computer science principles", "ap csp", "csp", "computer principles",
                                        "computer science principles"],
        "Environmental Science": ["apes", "environmental science", "ap es", "ap e.s"],
        "European History": ["ap euro", "euro", "ap european history", "european history"],
        "French": ["ap french", "french", "francais", "français"],
        "German": ["ap german", "german"],
        "Human Geography": ["geography", "geo", "ap geo", "human geography", "hug"],
        "Italian": ["ap italian", "italian"],
        "Japanese": ["ap japanese", "japanese"],
        "Language Arts": ["ap language", "ap lang", "lang"],
        "Latin": ["ap latin", "latin"],
        "Literature": ["lit", "literature", "ap lit", "ap literature"],
        "Macroeconomics": ["ap macro", "macro", "ap macroeconomics", "macroeconomics"],
        "Microeconomics": ["ap micro", "micro", "ap microeconomics", "microeconomics"],
        "Music Theory": ["ap music theory", "music", "music theory", "ap music"],
        "Psychology": ["psych", "ap psych", "ap psychology"],
        "Physics 1": ["ap physics 1", "physics 1"],
        "Physics 2": ["ap physics 2", "physics 2"],
        "Physics C Mech": ["ap physics mech", "physics mech", "mech"],
        "Physics C E/M": ["ap physics e/m", "physics e/m", "e/m"],
        "Research": ["ap research", "research"],
        "Seminar": ["ap seminar", "seminar"],
        "Spanish Language": ["ap spanish language", "spanish language", "spanish culture", "spanish"],
        "Spanish Literature": ["ap spanish literature", "spanish literature", "spanish lit"],
        "Studio Art": ["ap studio art", "studio art"],
        "Statistics": ["ap statistics", "ap stats", "stats", "ap statistics"],
        "U.S Government": ["ap gov", "u.s government", "us gov"],
        "U.S History": ["apush", "united states", "us history", "u.s history", "ap u.s history"],
        "World History": ["apwh", "ap world history", "world history", "world", "ap wh", "whap"]
    }

AMBIGUOUS_ROLES = {
                    "physics": ["Physics 1", "Physics 2", "Physics C Mech", "Physics C E/M"],
                    # "spanish": ["Spanish Language", "Spanish Literature"],
                    "economics": ["Macroeconomics", "Microeconomics"],
                    "econ": ["Macroeconomics", "Microeconomics"],
                    "art": ["Art History", "Studio Art"],
                    "gov": ["U.S Government", "Comp. Government"],
                    "government": ["U.S Government", "Comp. Government"],
                  }

HELP_MESSAGE = """To ping helpers, use ```{0}ping <helper alias>```
Be careful when using this command! 
It will ping all helpers of that role, and you will not be able to ping again for """ + str(TIMEOUT_TIME) + """ seconds.

To check how much longer until you can ping a helper use ```{0}time```
To request to receive a reminder DM when you can once again ping a helper use ```{0}remind```

In order to ping a role, you must use one that role's aliases. 
To find the aliases for all the roles use : ```{0}alias```

*Below are mod-only commands*:

To completely blacklist a user from pinging helpers use: ```{0}blacklist <user's mention>```
To unblacklist a user from pinging helpers use: ```{0}unblacklist <user's mention>```
To get all members who are blacklisted, use: ```{0}getblacklist```
To change the prefix of commands on your server use: ```{0}setprefix <new_prefix>```

**NOTE:** At the request of bork, Computer Science A, Home Economics, and Calculus Helpers will not receive any pings.
Do not try to ping these roles; it will not work."""


ALIAS_MESSAGE = "Alias for helpers:```"
for subject in HELPER_ROLES.keys():
    ALIAS_MESSAGE += "* {0}: {1}\n".format(subject, ", ".join(HELPER_ROLES[subject]))
ALIAS_MESSAGE += "\n```"


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
        The helper name, "ambiguous role", or "" (if none are found).
    """

    for role in HELPER_ROLES:
        if alias in HELPER_ROLES[role]:
            return role + HELPER_SUFFIX
    if alias in AMBIGUOUS_ROLES:
        return AMBIGUOUS
    return None


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

    Parameters
    ----------
    message : Message
        Any message sent that the bot can read.

    Returns
    -------
    None
    """

    if message.guild.id != GUILD_ID:    # Prevent anyone from accessing the blacklist from another server.
        return

    message.content = message.content.lower()
    await bot.process_commands(message)


@bot.command()
async def help(ctx):
    """DMs bot description and help for the requester."""

    await ctx.author.send(bot.description)
    await ctx.author.send(HELP_MESSAGE.format(bot.command_prefix))
    await ctx.message.delete()


@bot.command()
async def alias(ctx):
    """DMs helper aliases to the requester."""

    await ctx.author.send(ALIAS_MESSAGE)
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

    if ctx.author in blacklisted_users:
        await ctx.send("Sorry, but you are blacklisted from pinging helpers.", delete_after=60)
        return

    if ctx.author in users_on_timeout and not ctx.author.guild_permissions.manage_guild:
        time_left = users_on_timeout[ctx.author]    # In seconds
        await ctx.send("Sorry {0}, but you still have to wait {1} minutes and {2} seconds"
                       .format(ctx.author.name, time_left // 60, time_left - time_left // 60), delete_after=60)
        return

    helper_role = convert_alias(alias)

    if helper_role is None:
        await ctx.send("Sorry {0}, invalid alias.".format(ctx.author.name), delete_after=60)
        return

    if helper_role == AMBIGUOUS:
        ambiguous_role_response = "There are multiple helper roles that you could be referring to with." \
                                  "  Please specify by using one of the below roles and try again.\n```\n"
        for r in AMBIGUOUS_ROLES[alias]:
            ambiguous_role_response += "\n* " + r + ": " + ", ".join(HELPER_ROLES[r]) + "\n"
        ambiguous_role_response += "```"

        await ctx.send(ctx.author.name + ", " + ambiguous_role_response, delete_after=60)
        return

    # We may now assume helper_role is verified.
    YES = ["y", "yes"]
    NO = ["n", "no", "stop", "cancel", "exit", "quit"]

    confirm_ping = await ctx.send("{0}, You are about to ping all the {1}s on this server. " 
                                  "Please make sure you have clearly elaborated your question and/or shown all work. \n""If you have done so, type Y or Yes in the next 30 seconds. \n"
                                  "To cancel, type N, No, Stop, Cancel, Exit, or Quit.\n"
                                  "After 30 seconds, this message will be deleted and your request will be canceled."
                                  .format(ctx.author.name, helper_role))

    def ping_check(message):
        """Determines if the confirmation is a valid response."""
        if message.author == ctx.author and message.guild == ctx.guild:
            if message.content.lower() in YES or message.content.lower() in NO:
                return True
        return False

    try:
        user_confirm = await bot.wait_for('message', timeout=30, check=ping_check)
    except asyncio.TimeoutError:
        await ctx.send("Timed out!", delete_after=10)
        await confirm_ping.delete()
        await ctx.message.delete()
        return
    if user_confirm.content in NO:
        await ctx.send("Canceling request...", delete_after=10)
        await confirm_ping.delete()
        await user_confirm.delete()
        await ctx.message.delete()
        return

    # Member answered Yes
    actual_role = discord.utils.get(ctx.guild.roles, name=helper_role)
    await actual_role.edit(mentionable=True)
    await ctx.send("Ping requested by {0} for {1}".format(ctx.author.mention, actual_role.mention))
    await actual_role.edit(mentionable=False)

    users_on_timeout[ctx.author] = TIMEOUT_TIME

    await confirm_ping.delete()
    await user_confirm.delete()
    await ctx.message.delete()


@bot.command()
async def time(ctx):
    """Tells the member how much time they have left before being able to ping again."""

    try:
        time_left = users_on_timeout[ctx.author]  # In seconds
        await ctx.send("{0}, you still have to wait {1} minutes and {2} seconds"
                   .format(ctx.author.name, time_left // 60, time_left - time_left // 60), delete_after=60)
    except KeyError:
        await ctx.send("{0}, you are currently allowed to ping a helper.".format(ctx.author.name), delete_after=60)


@bot.command()
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


@bot.command()
async def blacklist(ctx, member: discord.Member):
    """Adds a member to the blacklist."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    if member not in blacklisted_users:
        blacklisted_users.append(member)
        await ctx.send("{0} has been blacklisted by {1}.".format(member.name, ctx.author.name))
    else:
        await ctx.send("{0} was already blacklisted".format(member.name))


@bot.command()
async def unblacklist(ctx, member: discord.Member):
    """Removes a member from the blacklist."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    if member in blacklisted_users:
        del blacklisted_users[blacklisted_users.index(member)]
        await ctx.send("{0} was unblacklisted by {1}.".format(member.name, ctx.author.name))


@bot.command()
async def getblacklist(ctx):
    """Sends the blacklist by converting the members to their names."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    if blacklisted_users:
        await ctx.send("Blacklisted members are: " + ", ".join(list(map(lambda x: x.name, blacklisted_users))))
    else:
        await ctx.send("No members are blacklisted.")


@bot.command()
async def setprefix(ctx, prefix: str):
    """Changes the prefix of the bot."""

    if not ctx.author.guild_permissions.manage_guild:
        return
    bot.command_prefix = prefix
    await ctx.send("Bot prefix set to " + prefix)


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
        var_dict = {KEY_BLACKLIST: blacklisted_users, KEY_PREFIX: bot.command_prefix}
        f.write(json.dumps(var_dict))
        print("Data written!")


def load_data():
    """Reads the ids from the blacklist from the JSON file"""

    global blacklisted_users
    print("Loading data...")
    with open("blacklist.json", mode="r") as f:
        try:
            var_dict = json.loads(f.read())
            blacklisted_users = var_dict[KEY_BLACKLIST]
            bot.command_prefix = var_dict[KEY_PREFIX]

        except JSONDecodeError:
            print("Invalid data found.")
            print("File contents: " + f.read())
        else:
            print("Data loaded successfully.")


def convert_ids():
    """Converts all ids of the server from the blacklist by using the GUILD_ID constant."""

    global blacklisted_users
    print("Converting ids")
    for i in range(len(blacklisted_users)):
        blacklisted_users[i] = bot.get_guild(GUILD_ID).get_member(blacklisted_users[i])
    else:
        print("Members converted from ids successfully.")


@asyncio.coroutine
def main_task():
    with open("token.txt", mode="r") as f:
        token = f.read()
    yield from bot.login(token)
    yield from bot.connect()


loop = asyncio.get_event_loop()

try:
    load_data()
    loop.run_until_complete(main_task())
except:
    loop.run_until_complete(bot.logout())
finally:
    loop.close()
    write_data()
