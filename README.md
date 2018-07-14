# helper_ping_bot

helper_ping_bot.py is a helper bot for the AP Students [discord](https://discord.gg/apstudents).

This was written to allow students to easily ping the AP Helpers while also preventing spamming of Helpers.

## Commands

* !ping |alias|
    * Pings all helpers of a subject. Helper aliases can be found in the !help command.
    * Asks for confirmation of the pinger before pinging.
* !notify time
    * DM's how much time is left before being able to ping a Helper.
* !notify remind
    * DM's after the Helper ping cooldown time is over.
* !help
    * Displays these commands, Helper aliases, and ping cooldown time.

    #### Mod commands
    To use these commands, the user must have the manage channels permission.
    * !blacklist |@member|
        * Bans a member from using the ping command.
    * !unblacklist |@member|
        * Unbans a member from using the ping command.
    
This bot was written by [@ACT Inc.#2590](https://github.com/ikhaliq15) and [@jjam912#2180](https://github.com/jjam912).

Contact us for any suggestions for the bot or use GitHub's Issues page.

### Current TODO List:
1. ~~Implement a confirmation of the ping asking if the member has elaborated his or her question.~~
1. ~~Delete confirmation messages after the member has either confirmed or changed their mind.~~
1. ~~Add a command that will list all of the members that are currently blacklisted.~~
1. ~~Complete all aliases for all ap helper roles.~~
1. ~~Ask user to specify if there are multiple possible helpers (ex. ap computer science a and ap computer science principles)~~
