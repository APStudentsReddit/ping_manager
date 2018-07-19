# ping_manager

ping_manager.py is a helper bot for the AP Students [discord](https://discord.gg/apstudents).

This was written to allow students to easily ping the AP Helpers while also preventing spamming of Helpers.

## Commands

* !ping |alias|
    * Pings all helpers of a subject. Helper aliases can be found in the !alias command.
    * Asks for confirmation of the pinger before pinging.
* !time
    * DM's how much time is left before being able to ping a Helper.
* !remind
    * DM's after the Helper ping cooldown time is over.
* !help
    * DM's these commands and ping cooldown time.
* !alias
    * DM's all aliases for the Helper roles.

    #### Mod commands
    To use these commands, the user must have the Manage Guilds permission.
    * !blacklist |@member|
        * Bans a member from using the ping command.
    * !unblacklist |@member|
        * Unbans a member from using the ping command.
    * !getblacklist
        * Direct messages a list of all blacklisted members.
    * !setprefix |prefix|
        * Allows a mod to set the prefix to anything.
        
Note that there are no pings for Computer Science A, Calculus, or Home Economics Helpers at request of an APStudents mod (those channels are active enough).
    
This bot was written by [@ACT Inc.#2590](https://github.com/ikhaliq15) and [@jjam912#2180](https://github.com/jjam912).

Contact us for any suggestions for the bot or use GitHub's Issues page.

### Current TODO List:
1. Add to the APStudents discord.
