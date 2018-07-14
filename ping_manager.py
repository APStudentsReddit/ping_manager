import discord
import asyncio
import pickle

valid_helper_roles = {  
                        "Art History": ["ap art history", "art history"],
                        "Biology": ["biology", "ap bio", "ap biology", "bio"],
                        "Calculus": ["calculus", "ap calc", "calc ab", "calc bc", "calc", "ab calc", "bc calc"],
                        "Capstone": ["capstone", "ap capstone"],
                        "Chemistry": ["chem", "chemistry", "ap chem", "ap chemistry"],
                        "Chinese": ["ap chinese", "chinese", "中文"],
                        "Comp. Government": ["comparative government", "comp gov", "comp. gov"],
                        "Computer Science Principles": ["ap computer science principles", "ap csp", "csp", "computer principles", "computer science principles"],
                        "Environmental Science": ["apes", "environmental science", "ap es", "ap e.s"],
                        "European History": ["ap euro", "euro", "ap european history", "european history"],
                        "French": ["ap french", "french", "francais", "français"],
                        "German": ["ap german", "german"],
                        "Human Geography": ["geography", "geo", "ap geo", "human geography"],
                        "Italian": ["ap italian", "italian", "mafia"],
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
                        "Physics C Mech": ["ap physics mech", "physics mech"],
                        "Physics C E/M": ["ap physics e/m", "physics e/m"],
                        "Research": ["ap research", "research"],
                        "Seminar": ["ap seminar", "seminar"],
                        "Spanish Language": ["ap spanish language", "spanish language", "spanish culture"],
                        "Spanish Literature": ["ap spanish literature", "spanish literature", "spanish lit"],
                        "Studio Art": ["ap studio art", "studio art"],
                        "Statistics": ["ap statistics", "ap stats", "stats", "ap statistics"],
                        "U.S Government": ["ap gov", "u.s government", "us gov"],
                        "U.S History": ["apush", "united states", "us history", "u.s history", "ap u.s history"],
                        "World History": ["apwh", "ap world history", "world history", "world", "ap wh", "whap"]
                        }

ambiguous_roles = {
                    "physics": ["Physics 1", "Physics 2", "Physics C Mech", "Physics C E/M"],
                    "spanish": ["Spanish Language", "Spanish Literature"],
                    "economics": ["Macroeconomics", "Microeconomics"],
                    "econ": ["Macroeconomics", "Microeconomics"],
                    "art": ["Art History", "Studio Art"],
                    "gov": ["U.S Government", "Comp. Government"],
                    "government": ["U.S Government", "Comp. Government"],
                  }

TIMEOUT_TIME = 15

# jjam912's code
# Set up the help message
help_message = """To ping helpers, use ```!ping <helper name>```
Be careful when using this command! It will ping all helpers of that role, and you will not be able to ping again for """ + str(TIMEOUT_TIME) + """ seconds.

To check how much longer until you can ping a helper use ```!notify time```
To request to receive a reminder when you can once again ping a helper use ```!notify remind```

In order to ping a role, you must use one that role's aliases. To find the aliases for all the roles use : ```!alias```
"""

alias_message = "Alias for helpers:```"
for subject in valid_helper_roles.keys():
    alias_message += "* {0}: {1}\n".format(subject, ", ".join(valid_helper_roles[subject]))

alias_message += "\n```"

help_message += """

*Below are mod-only commands*:

To completely blacklist a user from pinging helpers use: ```!blacklist <user's mention>```
To unblacklist a user from pinging helpers use: ```!unblacklist <user's mention>```
To get all members who are blacklisted, use: ```!getblacklist```

**NOTE:** At the request of bork, Computer Science A and Home Economics Helpers will not receive any pings.
Do not try to ping these roles; it will not work."""

TOKEN = ''

client = discord.Client()


# ACT Inc.'s Code
def convertCommonNameToProperName(s):
    for item in valid_helper_roles:
        if s in valid_helper_roles[item]:
            return item + " Helper"
    if (s in ambiguous_roles):
        return "ambiguous_role"
    return ""


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def readBlacklist(obj, filename):
    with open(filename, 'rb') as input:
        blu = pickle.load(input)
        return blu


blacklisted_users = []
try:
    blacklisted_users = readBlacklist('d', 'blacklist.pkl')
except (OSError, IOError) as e:
    save_object(blacklisted_users, 'blacklist.pkl')

users_on_timeout = {}
messages_to_delete = {}
pings_needing_confirmation = {}


async def updateTimer():
    while True:
        await asyncio.sleep(1)
        names_to_remove = []
        for item in users_on_timeout:
            users_on_timeout[item][0] = users_on_timeout[item][0] - 1
            if (users_on_timeout[item][0] <= 0):
                names_to_remove.append(item)
        for item in names_to_remove:
            if (users_on_timeout[item][1]):
                await client.send_message(item, "This is your reminder that you are now allowed to ping helpers.")
            del users_on_timeout[item]


async def removeMessages():
     while True:
        await asyncio.sleep(1)
        messages_to_remove = []
        #print (messages_to_delete)
        for item in messages_to_delete:
            messages_to_delete[item] = messages_to_delete[item] - 1
            if (messages_to_delete[item] <= 0):
                messages_to_remove.append(item)
        for item in messages_to_remove:
            await client.delete_message(item)
            del messages_to_delete[item]


async def checkOnPingRequests():
     while True:
        await asyncio.sleep(1)
        requests_to_remove = []
        for item in pings_needing_confirmation:
            pings_needing_confirmation[item][0] = pings_needing_confirmation[item][0] - 1
            if (pings_needing_confirmation[item][0] <= 0):
                requests_to_remove.append(item)
        for item in requests_to_remove:
            await client.delete_message(pings_needing_confirmation[item][2])
            del pings_needing_confirmation[item]


@client.event
async def on_message(message):
    global messages_to_delete
    global help_message
    global alias_message

    if message.author == client.user:
        return
    if message.author in pings_needing_confirmation and message.content.lower()=="y":
        role = discord.utils.get(message.server.roles, name=pings_needing_confirmation[message.author][1])
        await client.edit_role(message.server, role, mentionable=True)
        await client.send_message(message.channel, "Pinging " + role.mention + " for help.")
        await client.edit_role(message.server, role, mentionable=False)
        users_on_timeout[message.author] = [TIMEOUT_TIME, False]
        messages_to_delete[message] = 1
        messages_to_delete[pings_needing_confirmation[message.author][2]] = 1
        del pings_needing_confirmation[message.author]
    elif message.content.startswith("!help"):
        await client.send_message(message.author, help_message)
        #await client.delete_message(message)
        #messages_to_delete[message] = 3
    elif message.content.startswith("!alias"):
        await client.send_message(message.author, alias_message)
    elif message.content.startswith('!notify'):
        messages_to_delete[message] = 3
        arg = " ".join(message.content.split(" ")[1:len(message.content.split(" "))]).lower()
        if (arg == "time"):
            if (message.author in users_on_timeout):
               await client.send_message(message.author, "You will be able to ping for a helper in " + str(users_on_timeout[message.author][0]) + " seconds.")
            else:
                await client.send_message(message.author, "You are currently allowed to ping helpers.")
        elif (arg == "remind"):
            if (message.author in users_on_timeout):
                if (users_on_timeout[message.author][1]):
                    await client.send_message(message.author, "You will no longer be receiving a reminder for when you can ping a helper.")
                else:
                    await client.send_message(message.author, "You will receive a reminder once you are allowed to ping a helper.")
                users_on_timeout[message.author][1] = not users_on_timeout[message.author][1]
            else:
                await client.send_message(message.author, "You are currently allowed to ping helpers.")
    elif message.content.startswith('!ping'):
        if (not message.author.mention in blacklisted_users):
            common_helper_role = " ".join(message.content.split(" ")[1:len(message.content.split(" "))]).lower()
            helper_role = convertCommonNameToProperName(common_helper_role)
            if (message.author in users_on_timeout):
                msg = await client.send_message(message.channel, message.author.mention + " Sorry, but you cannot ping a helper for " + str(users_on_timeout[message.author][0]) + " seconds.")
                messages_to_delete[msg] = 5
            else:
                if (helper_role == "ambiguous_role"):
                    ambiguous_role_response = "There are multiple helper roles that you could be referring to with \"" + common_helper_role + "\". Please specify by using one of the below roles.\n```\n"
                    for role in ambiguous_roles[common_helper_role]:
                        ambiguous_role_response += "\n* " + role + ": " + ", ".join(valid_helper_roles[role]) + "\n"
                    ambiguous_role_response += "```"
                    msg = await client.send_message(message.author, ambiguous_role_response)
                    # messages_to_delete[msg] = 15
                    messages_to_delete[message] = 15 
                elif (helper_role != ""):
                    msg = await client.send_message(message.channel, message.author.mention + " You are about to ping all the " + helper_role + "s on this server. Please make sure you have clearly elaborated your question and/or shown all work. If you have done so, type Y in the next 15 seconds. After 15 seconds, this message will be deleted and your request will be canceled.")
                    if (message.author in pings_needing_confirmation):
                        messages_to_delete[pings_needing_confirmation[message.author][2]] = 1
                    pings_needing_confirmation[message.author] = [15, helper_role, msg]
                else:
                    msg = await client.send_message(message.channel, message.author.mention + " Sorry, but there is no helper role named \"" + common_helper_role + "\".")
                    messages_to_delete[msg] = 15
                    messages_to_delete[message] = 15
        else:
            msg = await client.send_message(message.channel, message.author.mention + " Sorry, but you are blacklisted from pinging helpers.")
            messages_to_delete[message] = 5
            messages_to_delete[msg] = 5
    # Mod Only Commands
    if message.content.startswith('!blacklist'):
        role_names = [role.name for role in message.author.roles]
        #if "Mod" in role_names:
        if message.author.server_permissions.manage_server:
            user_name = message.content.split(" ")[1].lower()
            reason = " ".join(message.content.split(" ")[2:len(message.content.split(" "))]).lower()
            if (user_name.startswith("<@")):
                if (user_name not in blacklisted_users):
                    blacklisted_users.append(user_name)
                    msg = await client.send_message(message.channel, message.author.mention + (" %s is now blacklisted from pinging helpers. The reason given was: \n" % user_name) + reason)
                else:
                    msg = await client.send_message(message.channel, message.author.mention + " %s is already blacklisted from pinging helpers." % user_name)
                    messages_to_delete[msg] = 5
                    messages_to_delete[message] = 5
        else:
            msg = await client.send_message(message.channel, message.author.mention + " Sorry, but that command is for mods only.")
            messages_to_delete[msg] = 5
            messages_to_delete[message] = 5
    elif message.content.startswith('!unblacklist'):
        role_names = [role.name for role in message.author.roles]
        #if "Mod" in role_names:
        if message.author.server_permissions.manage_server:
            user_name = " ".join(message.content.split(" ")[1:len(message.content.split(" "))]).lower()
            if (user_name.startswith("<@")):
                if (user_name not in blacklisted_users):
                    msg = await client.send_message(message.channel, message.author.mention + " %s is alrady not blacklisted from pinging helpers." % user_name)
                    messages_to_delete[msg] = 5
                    messages_to_delete[message] = 5
                else:
                    blacklisted_users.remove(user_name)
                    msg = await client.send_message(message.channel, message.author.mention + " %s is no longer blacklisted from pinging helpers." % user_name)
        else:
            msg = await client.send_message(message.channel, message.author.mention + " Sorry, but that command is for mods only.")
            messages_to_delete[msg] = 5
            messages_to_delete[message] = 5
    elif message.content.startswith("!getblacklist"):
        if message.author.server_permissions.manage_server:
            users_on_blacklist = "Users that are banned from pinging helpers: \n"
            for user in blacklisted_users:
                user_info = await client.get_user_info(int(user[2:-1]))
                users_on_blacklist += "`" + user_info.name + "#" + user_info.discriminator + "`, "
            await client.send_message(message.author, users_on_blacklist[0:-2])
            messages_to_delete[message] = 1
        else:
            msg = await client.send_message(message.channel, message.author.mention + " Sorry, but that command is for mods only.")
            messages_to_delete[msg] = 5
            messages_to_delete[message] = 5


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(game=discord.Game(name='By ACT Inc and jjam912'))
    client.loop.create_task(updateTimer())
    client.loop.create_task(removeMessages())
    client.loop.create_task(checkOnPingRequests())

client.run(TOKEN)
save_object(blacklisted_users, "blacklist.pkl")
print ("Created 'blacklist.pkl'.")
