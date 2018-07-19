import discord
import asyncio
from discord.ext import commands


DESCRIPTION = """This bot is used to ping helpers while also preventing spamming of pings in the APStudents discord.
It was created by @jjam912#2180 and @ACT Inc.#2590
You can find our github at https://github.com/APStudentsReddit/ping_manager/tree/rewrite
This was written using discord.py rewrite.
"""

# This bot is only meant to be run on one server, so hardcoding this seems fine.
GUILD_ID = "420053499707916288"     # JSON only allows string keys :(

bot = commands.Bot(description=DESCRIPTION, command_prefix="!")
bot.remove_command("help")

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

TIMEOUT_TIME = 3600

HELP_MESSAGE = """To ping helpers, use ```{0}ping <helper name>```
Be careful when using this command! 
It will ping all helpers of that role, and you will not be able to ping again for """ + str(TIMEOUT_TIME) + """ seconds.

To check how much longer until you can ping a helper use ```{0}notify time```
To request to receive a reminder when you can once again ping a helper use ```{0}notify remind```

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

blacklisted_users = []
users_on_timeout = {}
users_to_remind = []

AMBIGUOUS = "Ambiguous role"
HELPER_SUFFIX = " Helper"


def convert_alias(s):
    """
    Converts an alias name to the proper Helper name.

    Parameters
    ----------
    s : str
        An alias for the wanted helper name.

    Returns
    -------
    str
        The helper name, "ambiguous role", or "" (if none are found).
    """

    for item in HELPER_ROLES:
        if s in HELPER_ROLES[item]:
            return item + HELPER_SUFFIX
    if s in AMBIGUOUS_ROLES:
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

    Parameters
    ----------
    message : Message
        Any message sent that the bot can read.

    Returns
    -------
    None

    Notes
    -----
    Commands include:
        !help
            Privately messages the user our help message.
        !alias
            Privately messages the user our alias message.
        !notify time
            DM's the user how much longer they must wait to ping again.
        !notify remind
            DM's the user when their ping is ready.
        !ping <subject_alias>
            When this is called, the member must confirm if they are sure that they want to ping and must respond "Y".
            If the member confirms it, this will ping all Helpers of the requested subject.

        Mod only (must have Manage Server):
            !blacklist  <@member>
                Blacklists a member from using pings.
            !unblacklist <@member>
                Removes a member from the blacklist.
            !getblacklist
                DM's the user all members that are blacklisted.
            !setprefix <new_prefix>
                Changes the prefix for new commands.
    """

    if message.guild.id != int(GUILD_ID):
        return

    message.content = message.content.lower()
    await bot.process_commands(message)

    # if message.author in pings_needing_confirmation and message.content.lower()=="y":
    #     temp_dict = pings_needing_confirmation[message.author]
    #     del pings_needing_confirmation[message.author]
    #     role = discord.utils.get(message.server.roles, name=temp_dict[1])
    #     await bot.edit_role(message.server, role, mentionable=True)
    #     await bot.send_message(message.channel, "Pinging " + role.mention + " for help (Ping requested by " + temp_dict[3] + ").")
    #     await bot.edit_role(message.server, role, mentionable=False)
    #     if (not message.author.server_permissions.manage_server):
    #         users_on_timeout[message.author] = [TIMEOUT_TIME, False]
    #         save_object(users_on_timeout, 'timeouts.pkl')
    #     messages_to_delete[message] = 1
    #     messages_to_delete[temp_dict[2]] = 1
    # elif message_lower_case.startswith(command_starter + "help"):
    #     await bot.send_message(message.author, HELP_MESSAGE.replace("!", settings[message.server][0]))
    #     #await client.delete_message(message)
    #     #messages_to_delete[message] = 3
    # elif message_lower_case.startswith(command_starter + "alias"):
    #     await bot.send_message(message.author, ALIAS_MESSAGE)
    # elif message_lower_case.startswith(command_starter + 'notify '):
    #     messages_to_delete[message] = 30
    #     arg = " ".join(message.content.split(" ")[1:len(message.content.split(" "))]).lower()
    #     if (arg == "time"):
    #         if (message.author in users_on_timeout):
    #             msg = await bot.send_message(message.channel, "You will be able to ping for a helper in " + str(int(users_on_timeout[message.author][0] / 60)) + " minutes and " + str(users_on_timeout[message.author][0] - (int(users_on_timeout[message.author][0] / 60) * 60)) + " seconds.")
    #             messages_to_delete[msg] = 30
    #         else:
    #             msg = await bot.send_message(message.channel, "You are currently allowed to ping helpers.")
    #             messages_to_delete[msg] = 30
    #     elif (arg == "remind"):
    #         if (message.author in users_on_timeout):
    #             if (users_on_timeout[message.author][1]):
    #                 msg = await bot.send_message(message.channel, "You will no longer be receiving a reminder for when you can ping a helper.")
    #                 messages_to_delete[msg] = 30
    #             else:
    #                 msg = await bot.send_message(message.channel, "You will receive a reminder once you are allowed to ping a helper.")
    #                 messages_to_delete[msg] = 30
    #             users_on_timeout[message.author][1] = not users_on_timeout[message.author][1]
    #         else:
    #             msg = await bot.send_message(message.channel, "You are currently allowed to ping helpers.")
    #             messages_to_delete[msg] = 30
    # elif message_lower_case.startswith(command_starter + 'ping '):
    #     if (not message.author.mention in blacklisted_users or message.author.server_permissions.manage_server):
    #         common_helper_role = " ".join(message.content.split(" ")[1:len(message.content.split(" "))]).lower()
    #         helper_role = convertCommonNameToProperName(common_helper_role)
    #         if (message.author in users_on_timeout and not message.author.server_permissions.manage_server):
    #             msg = await bot.send_message(message.channel, message.author.mention + " Sorry, but you cannot ping a helper for " + str(int(users_on_timeout[message.author][0] / 60)) + " minutes and " + str(users_on_timeout[message.author][0] - (int(users_on_timeout[message.author][0] / 60) * 60)) + " seconds.")
    #             messages_to_delete[msg] = 30
    #         else:
    #             if (helper_role == "ambiguous_role"):
    #                 ambiguous_role_response = "There are multiple helper roles that you could be referring to with \"" + common_helper_role + "\". Please specify by using one of the below roles.\n```\n"
    #                 for role in AMBIGUOUS_ROLES[common_helper_role]:
    #                     ambiguous_role_response += "\n* " + role + ": " + ", ".join(HELPER_ROLES[role]) + "\n"
    #                 ambiguous_role_response += "```"
    #                 msg = await bot.send_message(message.channel, message.author.mention + " " + ambiguous_role_response)
    #                 messages_to_delete[msg] = 30
    #                 messages_to_delete[message] = 30
    #             elif (helper_role != ""):
    #                 msg = await bot.send_message(message.channel, message.author.mention + " You are about to ping all the " + helper_role + "s on this server. Please make sure you have clearly elaborated your question and/or shown all work. If you have done so, type Y in the next 15 seconds. After 15 seconds, this message will be deleted and your request will be canceled.")
    #                 if (message.author in pings_needing_confirmation):
    #                     messages_to_delete[pings_needing_confirmation[message.author][2]] = 1
    #                     del pings_needing_confirmation[message.author]
    #                 pings_needing_confirmation[message.author] = [15, helper_role, msg, message.author.mention]
    #             else:
    #                 msg = await bot.send_message(message.channel, message.author.mention + " Sorry, but there is no helper role named \"" + common_helper_role + "\".")
    #                 messages_to_delete[msg] = 15
    #                 messages_to_delete[message] = 15
    #     else:
    #         msg = await bot.send_message(message.channel, message.author.mention + " Sorry, but you are blacklisted from pinging helpers.")
    #         messages_to_delete[message] = 30
    #         #messages_to_delete[msg] = 5
    # # Mod Only Commands
    # if message_lower_case.startswith(command_starter + 'blacklist '):
    #     role_names = [role.name for role in message.author.roles]
    #     #if "Mod" in role_names:
    #     if message.author.server_permissions.manage_server:
    #         user_name = message.content.split(" ")[1].lower()
    #         reason = " ".join(message.content.split(" ")[2:len(message.content.split(" "))]).lower()
    #         if (user_name.startswith("<@")):
    #             if (user_name not in blacklisted_users):
    #                 blacklisted_users.append(user_name)
    #                 msg = await bot.send_message(message.channel, message.author.mention + (" %s is now blacklisted from pinging helpers. The reason given was: \n" % user_name) + reason)
    #             else:
    #                 msg = await bot.send_message(message.channel, message.author.mention + " %s is already blacklisted from pinging helpers." % user_name)
    #                 messages_to_delete[msg] = 30
    #                 messages_to_delete[message] = 30
    #     else:
    #         msg = await bot.send_message(message.channel, message.author.mention + " Sorry, but that command is for members with the Manage Server permission only.")
    #         messages_to_delete[msg] = 30
    #         messages_to_delete[message] = 30
    #     exit_handler()
    # elif message_lower_case.startswith(command_starter + 'unblacklist '):
    #     role_names = [role.name for role in message.author.roles]
    #     #if "Mod" in role_names:
    #     if message.author.server_permissions.manage_server:
    #         user_name = " ".join(message.content.split(" ")[1:len(message.content.split(" "))]).lower()
    #         if (user_name.startswith("<@")):
    #             if (user_name not in blacklisted_users):
    #                 msg = await bot.send_message(message.channel, message.author.mention + " %s is alrady not blacklisted from pinging helpers." % user_name)
    #                 messages_to_delete[msg] = 30
    #                 messages_to_delete[message] = 30
    #             else:
    #                 blacklisted_users.remove(user_name)
    #                 msg = await bot.send_message(message.channel, message.author.mention + " %s is no longer blacklisted from pinging helpers." % user_name)
    #     else:
    #         msg = await bot.send_message(message.channel, message.author.mention + " Sorry, but that command is for members with the Manage Server permission only.")
    #         messages_to_delete[msg] = 30
    #         messages_to_delete[message] = 30
    #     exit_handler()
    # elif message_lower_case.startswith(command_starter + "getblacklist"):
    #     if message.author.server_permissions.manage_server:
    #         users_on_blacklist = "Users that are banned from pinging helpers: \n"
    #         for user in blacklisted_users:
    #             user_info = await bot.get_user_info(int(user[2:-1]))
    #             users_on_blacklist += "`" + user_info.name + "#" + user_info.discriminator + "`, "
    #         await bot.send_message(message.author, users_on_blacklist[0:-2])
    #         messages_to_delete[message] = 1
    #     else:
    #         msg = await bot.send_message(message.channel, message.author.mention + " Sorry, but that command is for members with the Manage Server permission only.")
    #         messages_to_delete[msg] = 30
    #         messages_to_delete[message] = 30
    # elif message_lower_case.startswith(command_starter + 'setprefix '):
    #     role_names = [role.name for role in message.author.roles]
    #     #if "Mod" in role_names:
    #     if message.author.server_permissions.manage_server:
    #         prefix = " ".join(message.content.split(" ")[1:len(message.content.split(" "))]).lower()
    #         settings[message.server] = prefix.strip()
    #         save_object(settings, 'settings.pkl')
    #         msg = await bot.send_message(message.channel, message.author.mention + " The prefix for commands on this server is now \"" + prefix.strip() + "\".")
    #     else:
    #         msg = await bot.send_message(message.channel, message.author.mention + " Sorry, but that command is for members with the Manage Server permission only.")
    #         messages_to_delete[msg] = 30
    #         messages_to_delete[message] = 30


@bot.command()
async def help(ctx):
    await ctx.author.send(HELP_MESSAGE.format(bot.command_prefix))
    await ctx.message.delete()


@bot.command()
async def alias(ctx):
    await ctx.author.send(ALIAS_MESSAGE)
    await ctx.message.delete()


@bot.command()
async def ping(ctx, *, role):
    if ctx.author in blacklisted_users:
        await ctx.send("Sorry, but you are blacklisted from pinging helpers.", delete_after=60)
        return

    if ctx.author in users_on_timeout and not ctx.author.guild_permissions.manage_server:
        time_left = users_on_timeout[ctx.author]    # In seconds
        await ctx.send("Sorry, but you still have to wait {0} minutes and {1} seconds"
                       .format(time_left // 60, time_left - time_left // 60), delete_after=60)
        return

    helper_role = convert_alias(role)

    if helper_role is None and helper_role != AMBIGUOUS:
        await ctx.send("Sorry, invalid alias.", delete_after=60)
        return

    if helper_role == AMBIGUOUS:
        ambiguous_role_response = "There are multiple helper roles that you could be referring to with." \
                                  "  Please specify by using one of the below roles and try again.\n```\n"
        for role in AMBIGUOUS_ROLES[helper_role]:
            ambiguous_role_response += "\n* " + role + ": " + ", ".join(HELPER_ROLES[role]) + "\n"
        ambiguous_role_response += "```"

        await ctx.send(ctx.author.name + ", " + ambiguous_role_response, delete_after=60)
        return

    # We may now assume helper_role is verified.
    YES = ["y", "yes"]
    NO = ["n", "no", "stop", "cancel", "exit", "quit"]

    confirm_ping = await ctx.send("{0} You are about to ping all the {1}s on this server. " 
                                  "Please make sure you have clearly elaborated your question and/or shown all work. \n""If you have done so, type Y or Yes in the next 30 seconds. \n"
                                  "To cancel, type N, No, Stop, Cancel, Exit, or Quit.\n"
                                  "After 30 seconds, this message will be deleted and your request will be canceled."
                                  .format(ctx.author.name, helper_role))

    def ping_check(message):
        if message.author == ctx.author and message.guild == ctx.guild:
            if message.content.lower() in YES or message.content.lower() in NO:
                return True
        return False

    try:
        user_confirm = await bot.wait_for('message', timeout=30, check=ping_check)
    except asyncio.TimeoutError:
        await ctx.send("Timed out!", delete_after=5)
        await confirm_ping.delete()
        await ctx.message.delete()
        return
    if user_confirm.content in NO:
        await ctx.send("Canceling request...", delete_after=5)
        await confirm_ping.delete()
        await user_confirm.delete()
        await ctx.message.delete()
        return

    # Member answered Yes
    actual_role = discord.utils.get(ctx.guild.roles, name=helper_role)
    await actual_role.edit(mentionable=True)
    await ctx.send("Ping requested by {0} for {1}".format(ctx.author.mention, actual_role.mention))
    await actual_role.edit(mentionable=False)

    await confirm_ping.delete()
    await user_confirm.delete()
    await ctx.message.delete()


@bot.command()
async def time(ctx):
    pass


@bot.command()
async def remind(ctx):
    pass


@bot.command()
async def blacklist(ctx):
    pass


@bot.command()
async def unblacklist(ctx):
    pass


@bot.command()
async def getblacklist(ctx):
    pass


@bot.command()
async def setprefix(ctx, prefix: str):
    bot.command_prefix = prefix
    await ctx.send("Bot prefix set to " + prefix)


@bot.event
async def on_ready():
    """Prints important bot information and sets up background tasks."""
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name='By ACT Inc. and jjam912'))
    bot.loop.create_task(update_timer())


@asyncio.coroutine
def main_task():
    yield from bot.login()
    yield from bot.connect()


loop = asyncio.get_event_loop()

try:
    # load_data()
    loop.run_until_complete(main_task())
except:
    loop.run_until_complete(bot.logout())
finally:
    loop.close()
    while True:     # To prevent accidents
        try:
            # write_data()
            break
        except KeyboardInterrupt:
            pass
