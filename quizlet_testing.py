import quizlet
import discord
import asyncio
from ping_config import *

def getDefinition(set, given_term):
	set_of_terms = quizlet_client.api.sets.get(set)["terms"]
	for term in set_of_terms:
		if (term["term"].lower() == given_term.lower()):
			return term["definition"]
	return None

def convertCommonNameToProperName(s):
    for item in valid_helper_roles:
        for item2 in valid_helper_roles[item]:
        	if s.find(item2) != -1:
        		print ("Looking: " + str(s.find(item2)) + ", " + item2 + ", " + s)
        		return [item, item2]
    return None

def getTopic(t, c):
	for item in quizlets[c]:
		if item[0] == t.lower():
			return item[1]
	return None


quizlets = {
			"U.S History": [["pre-columbus", 36777989], ["columbian-exchange", 146062824], ["early-colonial", 36779226], ["pre-revolution", 36779139], ["revolution", 37369172], ["early-republic", 37370832], ["new-constituion"], [37371858], ["jefferson-jackson", 37373624], ["second-great-awakening", 37377788], ["antebellum-south", 37379659], ["antebellum", 37381043], ["civil-war", 37383850], ["reconstruction", 37384519], ["industrial-revolution", 37388512], ["world-war-one", 37384519], ["progressive-era", 36783305], ["roaring-twenties", 36808395], ["great-depression", 36809135], ["world-war-two", 192630055], ["cold-war", 38484651], ["mid-century", 38486610], ["vietnam", 38487373], ["conservative-revival", 40339649], ["21-century", 40341505]] 
			}

command_starter = "!"

valid_helper_roles = {  
                        "Art History": ["ap art history", "art history"],
                        "Biology": ["biology", "ap bio", "ap biology", "bio"],
                        "Capstone": ["capstone", "ap capstone"],
                        "Chemistry": ["chem", "chemistry", "ap chem", "ap chemistry"],
                        "Chinese": ["ap chinese", "chinese", "中文"],
                        "Comp. Government": ["comparative government", "comp gov", "comp. gov", "gov comp"],
                        "Computer Science Principles": ["ap computer science principles", "ap csp", "csp", "computer principles", "computer science principles"],
                        "Environmental Science": ["apes", "environmental science", "ap es", "ap e.s"],
                        "European History": ["ap euro", "euro", "ap european history", "european history"],
                        "French": ["ap french", "french", "francais", "français"],
                        "German": ["ap german", "german"],
                        "Human Geography": ["geography", "geo", "ap geo", "human geography"],
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

quizlet_client = quizlet.QuizletClient(client_id='P6VVs9TV2K', login='me')
client = discord.Client()

@client.event
async def on_message(message):
    message_lower_case = message.content.lower()
    if (message_lower_case.startswith(command_starter + "define ")):
    	message_reduced = message_lower_case[len(command_starter + "define "):]
    	args = message_reduced.split(" ")
    	if (len(args) >= 2):
    		class_name = convertCommonNameToProperName(message_reduced)
    		message_reduced = message_reduced.strip()[len(class_name[1]):]
    		args = message_reduced.split(" ")
    		topic = args[1]
    		if (topic.lower() == "topics"):
    			topic_list = ""
    			for t in quizlets[class_name[0]]:
    				topic_list += "`" + str(t[0]) + "`, "
    			topic_list = topic_list[:-2]
    			await client.send_message(message.channel, message.author.mention + " The class `" + class_name[0] + "` has the following topics: \n " + topic_list)
    		else:
    			term = " ".join(args[2:])
    			print (class_name[0] + ", " + topic + ", " + term)
    			definition = getDefinition(getTopic(topic, class_name[0]), term)
    			await client.send_message(message.channel, message.author.mention + " Definition of `" + term + "`:\n" + definition)
    			print (message_reduced + "\n" + definition)
    	else:
    		await client.send_message(message.channel, message.author.mention + " The define command requires three arguments: the class, the topic, and the term. For more info use `!help`.")

def run_client(client, *args, **kwargs):
    loop = asyncio.get_event_loop()
    while True:
        try:
            loop.run_until_complete(client.start(*args, **kwargs))
        except Exception as e:
            print("Error", e)  # or use proper logging
        print("Waiting until restart")
        time.sleep(600)


@client.event
async def on_ready():
    """Prints important bot information and sets up background tasks."""
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(game=discord.Game(name='By ACT Inc and jjam912'))

run_client(client, TOKEN)