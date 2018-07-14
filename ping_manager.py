import discord
import asyncio
import pickle #as pickle

valid_helper_roles = {"Chemistry": ["chem", "chemistry", "ap chem", "chemistry helper"], "U.S History": ["apush", "united states", "us", "us history", "u.s history", "u.s history helper", "apush helper"],
                        "Calculus": ["calculus", "calculus helper", "ap calc", "calc ab", "calc bc", "calc"],
                        "Literature": ["lit", "lit helper", "literature", "literature helper", "ap lit", "ap lit helper"],
                        "Psychology": ["psych", "psych helper", "ap psych", "ap psychology", "psychology helper"],
                        "Computer Science Principles": ["ap computer science principles", "ap csp", "csp", "computer principles", "computer science principles helper", "computer science principles"],
                        "Computer Science": ["ap computer science", "ap computer science helper", "ap csa", "computer science", "computer scienceh helper"],
                        "Biology": ["biology", "biology helper", "ap bio", "ap biology", "ap biology helper", "ap bio helper"],
                        "U.S Government": ["ap gov", "u.s government helper", "u.s government", "us gov", "gov", "gov helper"],
                        "Comp. Government": ["comparative government", "comp gov", "comp. gov", "comparatove government helper", "comp gov helper", "comp. gov helper"],
                        "Macroeconomics": ["ap macro", "macro", "ap macroeconomics", "macroeconomics", "macro helper"],
                        "Microeconomics": ["ap micro", "micro", "ap microeconomics", "microeconomics", "micro helper"],
                        }

TIMEOUT_TIME = 15

# jjam912's code
# Set up the help message
help = """To ping helpers, use ```!ping <helper name>```
Be careful when using this command! It will ping all helpers of that role, and you will not be able to ping again for """ + str(TIMEOUT_TIME) + """ seconds.\n\nTo check how much longer until you can ping a helper use ```!notify time```\nTo request to receive a reminder when you can once again ping a helper use ```!notify remind```\n\nAliases for each role are as follows: ```
"""

for subject in valid_helper_roles.keys():
    help += "\n* {0}: {1}\n".format(subject, ", ".join(valid_helper_roles[subject]))

help += "\n```"

help += "\n\n*Below are mod-only commands*:\n\nTo completely blacklist a user from pinging helpers use: ```!blacklist <user's mention>```\nTo unblacklist a user from pinging helpers use: ```!unblacklist <user's mention>```"

TOKEN = 'NDY3MTcxNTg0MTcyNDkwNzUz.Dim1LQ.hBC0IjvBboKHF1B2HqxUU3Z_5IU'

client = discord.Client()

# ACT Inc.'s Code

def convertCommonNameToProperName(s):
    for item in valid_helper_roles:
        if s in valid_helper_roles[item]:
            return item + " Helper"
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

@client.event
async def on_message(message):
    global messages_to_delete
    if message.author == client.user:
        return
    if message.content.startswith("!help"):
        await client.send_message(message.author, help)
        #await client.delete_message(message)
        messages_to_delete[message] = 3
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
                if (helper_role != ""):
                    role = discord.utils.get(message.server.roles, name=helper_role)
                    await client.edit_role(message.server, role, mentionable=True)
                    await client.send_message(message.channel, "Pinging " + role.mention + " for help.")
                    await client.edit_role(message.server, role, mentionable=False)
                    users_on_timeout[message.author] = [TIMEOUT_TIME, False]
                else:
                    await client.send_message(message.channel, message.author.mention + " Sorry, but there is no helper role \"" + common_helper_role + "\".")
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
        else:
            msg = await client.send_message(message.channel, message.author.mention + " Sorry, but that command is mods only.")
            messages_to_delete[msg] = 5
    elif message.content.startswith('!unblacklist'):
        role_names = [role.name for role in message.author.roles]
        #if "Mod" in role_names:
        if message.author.server_permissions.manage_server:
            user_name = " ".join(message.content.split(" ")[1:len(message.content.split(" "))]).lower()
            if (user_name.startswith("<@")):
                if (user_name not in blacklisted_users):
                    msg = await client.send_message(message.channel, message.author.mention + " %s is alrady not blacklisted from pinging helpers." % user_name)
                    messages_to_delete[msg] = 5
                else:
                    blacklisted_users.remove(user_name)
                    msg = await client.send_message(message.channel, message.author.mention + " %s is no longer blacklisted from pinging helpers." % user_name)
        else:
            msg = await client.send_message(message.channel, message.author.mention + " Sorry, but that command is mods only.")
            messages_to_delete[msg] = 5

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(game=discord.Game(name='By ACT Inc and jjam912'))
    client.loop.create_task(updateTimer())
    client.loop.create_task(removeMessages())

client.run(TOKEN)
save_object(blacklisted_users, "blacklist.pkl")
print ("Created 'blacklist.pkl'.")
