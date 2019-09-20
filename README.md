# ping_manager

ping_manager.py is a helper bot for the AP Students [discord](https://discord.gg/apstudents).

This was written to allow students to easily ping the AP Helpers while also preventing spamming of Helpers.

## Commands
These commands can be used by everyone.

* ping |alias|
    * Pings all helpers of a subject. Helper aliases can be found in the alias command.
    * Asks for confirmation of the pinger before pinging.
    * Adds the ping to the pending list, which can be removed after the problem is solved.
* pending |alias|
    * Sends all links to pings that have not been marked with a check mark (solved) in a subject.
    * Note: Anyone can react with the check mark, and once someone has reacted, it will no longer be on the pending ping list.
* time
    * Sends how much time is left before being able to ping a Helper for you.
* remind
    * Sends a reminder after the Helper ping cooldown time is over for you.
* help
    * DM's these commands and other useful information.
* alias
    * DM's all aliases for the Helper roles.


## Mod commands
To use these commands, the user must have the Manage Guilds permission.

* blacklist |@member|
    * Bans a member from using the ping command.
* unblacklist |@member|
    * Unbans a member from using the ping command.
* getblacklist
    * Direct messages a list of all blacklisted members.
* setprefix |prefix|
    * Allows a mod to set the prefix to anything.
* settimeout |time in seconds|
    * Allows a mod to change the length of the timeout.
* resetuser |@member|
    * Reset a user's timeout.
* addalias
    * Adds an alias after some selection.
* removealias
    * Removes an alias after some selection.
* stats
    * Shows ping frequencies.
        
Note that there are no pings for Computer Science A, Calculus, or Home Economics Helpers at request of an APStudents mod (those channels are active enough).
    
This bot was written by [@JJamesWWang#2180](https://github.com/JJamesWWang) and [@ACT Inc.#2590](https://github.com/ikhaliq15).

Contact us for any suggestions for the bot or use GitHub's Issues page.
