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
