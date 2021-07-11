# Commands
\<brackets> mean "required arguments", [] mean "optional arguments". Actual commands do not need these brackets.

## Admin
* **motd**
    - Show the message of the day.
* **help**
    - Show help for a command, or show general help.
* **kick** \<ipid|*|**> [reason]
    - Kick a player.
    - Special cases:
        - "*" kicks everyone in the current area.
        - "**" kicks everyone in the server.
* **ban** \<ipid> "reason" ["\<N> \<minute|hour|day|week|month>(s)|perma"]
    - Ban a user. If a ban ID is specified instead of a reason,
    - then the IPID is added to an existing ban record.
    - Ban durations are 6 hours by default.
    - Usage 2: /ban <ipid> <ban_id>
* **banhdid**
    - Ban both a user's HDID and IPID.
* **unban** \<ban_id...>
    - Unban a list of users.
    - You need a ban ID to unban a user. Ban IDs are automatically included in ban reasons. Use `/baninfo \<ban_id>` for more information about a ban.
* **mute** \<ipid>
    - Prevent a user from speaking in-character.
* **unmute** \<ipid|"all">
    - Unmute a user.
* **login** \<password>
    - Login as a moderator.
* **refresh**
    - Reload all moderator credentials, server options, and commands without restarting the server.
* **online**
    - Show the number of players online.
* **mods**
    - Show a list of moderators online.
* **unmod**
    - Log out as a moderator.
* **ooc_mute** \<ooc-name>
    - Prevent a user from talking out-of-character.
* **ooc_unmute** \<ooc-name>
    - Allow an OOC-muted user to talk out-of-character.
* **bans**
    - Get the 5 most recent bans.
    - This can lag the server depending on the size of the database, so be judicious in its use.
* **baninfo** \<id> ['ban_id'|'ipid'|'hdid']
    - Get information about a ban.
    - By default, id identifies a ban_id.
* **time**
    - Returns the current server time.
* **whois** \<name|id|ipid|showname|character>
    - Get information about an online user.
## Area Access
* **area_lock**
    - Prevent users from joining the current area.
* **area_unlock**
    - Allow anyone to freely join the current area.
* **area_mute**
    - Makes this area impossible to speak for normal users unlesss /invite is used.
* **area_unmute**
    - Undo the effects of /area_mute.
* **lock** \<area(s)> or \<!link(s)>
    - Context-sensitive function to lock area(s) and/or area link(s).
    - Multiple targets may be passed.
    - Examples:
        - /lock - lock current area.
        - /lock 1 - lock area ID 1.
        - /lock !1 - lock a link connected to area ID 1 (if it exists).
        - /lock 1 2 3 - lock area IDs 1, 2 and 3.
* **unlock** \<area(s)> or \<!link(s)>
    - Context-sensitive function to unlock area(s) and/or area link(s).
    - Multiple targets may be passed.
    - Examples:
        - /unlock - unlock current area.
        - /unlock 1 - unlock area ID 1.
        - /unlock !1 - unlock a link connected to area ID 1 (if it exists).
        - /unlock 1 2 3 - unlock area IDs 1, 2 and 3.
* **link** \<id(s)>
    - Set up a two-way link from your current area with targeted area(s).
* **unlink** \<id(s)>
    - Remove a two-way link from your current area with targeted area(s).
* **links**
    - Display this area's information about area links.
* **onelink** \<id(s)>
    - Set up a one-way link from your current area with targeted area(s).
* **oneunlink** \<id(s)>
    - Remove a one-way link from your current area with targeted area(s).
* **link_lock** \<id(s)>
    - Lock the path leading to target area(s)
* **link_unlock** \<id(s)>
    - Unlock the path leading to target area(s).
* **link_hide**
    - Hide the path leading to target area(s).
* **link_unhide**
    - Unhide the path leading to target area(s).
* **link_pos** \<id> [pos]
    - Set the link's targeted pos when using it. Leave blank to reset.
* **link_peekable** \<id(s)>
    - Make the path(s) leading to target area(s) /peek-able.
* **link_unpeekable** \<id(s)>
    - Make the path(s) leading to target area(s) no longer /peek-able.
* **link_evidence** \<id> [evi_id(s)]
    - Make specific link only accessible from evidence ID(s).
    - Pass evidence ID's which you can see by mousing over evidence, or blank to see current evidences.
* **unlink_evidence**
    - Unlink evidence from links.
    - Pass evidence ID's which you can see by mousing over evidence.
* **pw** \<id> [password]
    - Enter a passworded area. Password is case-sensitive and must match the set password exactly, otherwise it will fail.
    - You will move into the target area as soon as the correct password is provided.
    - Leave password empty if you own the area and want to check its current password.
* **setpw** \<id> [password]
    - Context-sensitive function to set a password area(s) and/or area link(s).
    - Pass area id, or link id from current area using !, e.g. 5 vs !5.
    - Leave [password] blank to clear the password.
## Areas
* **bg** \<background>
    - Set the background of an area.
* **bgs**
    - Display the server's available backgrounds.
* **status** \<idle|rp|casing|looking-for-players|lfp|recess|gaming>
    - Show or modify the current status of an area.
* **area** [id]
    - List areas, or go to another area.
* **ooc_cmd_area_visible**
    - Display only linked and non-hidden areas. Useful to GMs.
* **getarea**
    - Show information about the current area.
* **getareas**
    - Show information about all areas.
* **getafk** [all]
    - Show currently AFK-ing players in the current area or in all areas.
* **invite** \<id>
    - Allow a particular user to join a locked or speak in spectator-only area.
    - ID can be * to invite everyone in the current area.
* **uninvite** \<id>
    - Revoke an invitation for a particular user.
    - ID can be * to uninvite everyone in the current area.
* **area_kick** \<id> [destination] [target_pos]
    - Remove a user from the current area and move them to another area.
    - If id is a * char, it will kick everyone but you and CMs from current area to destination.
    - If id is `afk`, it will only kicl all the afk people.
    - If the destination is not specified, the destination defaults to area 0.
    - target_pos is the optional position that everyone should end up in when kicked.
* **pos_lock** \<pos(s)>
    - Lock current area's available positions into a list of pos separated by space.
    - Use /pos_lock none or /pos_lock_clear to make the list empty.
    - If your pos have spaces in them, it must be a comma-separated list like /pos_lock pos one, pos two, pos X
    - If you're locking into a single pos with spaces in it, end it with a comma, like /pos_lock this is a pos,
* **pos_lock_clear**
    - Clear the current area's position lock and make all positions available.
* **knock** \<id>
    - Knock on the target area ID to call on their attention to your area.
* **peek** \<id>
    - Peek into an area to see if there's people in it.
* **max_players** [num]
    - Set a max amount of players for current area between -1 and 99.
* **desc** [desc]
    - Set an area description that appears to the user any time they enter the area.
* **edit_ambience** [tog]
    - Toggle edit mode for setting ambience. Playing music will set it as the area's ambience.
    - tog can be `on`, `off` or empty.
* **lights** [tog]
    - Toggle lights for this area. If lights are off, players will not be able to use /getarea or see evidence.
    - Players will also be unable to see area movement messages or use /chardesc.
    - You can change /bg, /desc and /pos_lock of the area when its dark and it will remember it next time you turn the lights off.
    - tog can be `on`, `off` or empty.
## Casing
* **doc** [url]
    - Show or change the link for the current case document.
* **cleardoc**
    - Clear the link for the current case document.
* **evidence_mod** \<FFA|Mods|CM|HiddenCM>
    - Change the evidence privilege mode.
    * **FFA**
        - Everyone can add, edit and remove evidence.
    * **Mods**
        - Only moderators can add, edit or remove evidence.
    * **CM**
        - Only the CM (case-maker, look at /cm for more info) or moderators can add, edit or remove evidence.
    * **HiddenCM**
        - Same as CM, but every evidence has a preset "owner's position" which can be set by a CM or moderator, such that only one side/position of the court may see the evidence. After presenting the evidence, the position of the evidence changes to "all" (visible to everyone).
* **evi_swap**  \<id> \<id>
    - Swap the positions of two evidence items on the evidence list.
    - The ID of each evidence can be displayed by mousing over it in 2.8 client, or simply its number starting from 1.
* **cm** \<id>
    - Add a case manager for the current area.
    - Leave id blank to promote yourself if there are no CMs.
* **uncm** \<id>
    - Remove a case manager from the current area.
    - Leave id blank to demote yourself.
* **setcase**
    - Set the positions you are interested in taking for a case. (This command is used internally by the 2.6 client.)
* **anncase** \<message> \<def> \<pro> \<jud> \<jur> \<steno>
    - Announce that a case is currently taking place in this area, needing a certain list of positions to be filled up.
* **blockwtce** \<id>
    - Prevent a user from using Witness Testimony/Cross Examination buttons as a judge.
* **unblockwtce** \<id>
    - Allow a user to use WT/CE again.
* **judgelog**
    - List the last 10 uses of judge controls in the current area.
* **afk**
    - Sets your player as AFK in player listings.
* **remote_listen** [option]
    - Change the remote listen logs to either NONE, IC, OOC or ALL.
    - It will send you those messages from the areas you are an owner of.
    - Leave blank to see your current option.
* **testimony** [id]
    - Display the currently recorded testimony.
    - Optionally, id can be passed to move to that statement.
* **testimony_clear**
    - Clear the current testimony.
* **testimony_remove** \<id>
    - Remove the statement at index.
* **testimony_amend** \<id> \<msg>
    - Edit the spoken message of the statement at idx.
* **testimony_swap** \<id> \<id>
    - Swap the two statements by id.
* **cs** \<id>
    - Start a one-on-one "Cross Swords" debate with targeted player!
    - Expires in 5 minutes.
    - If there's an ongoing cross-swords already, it will turn into a Scrum Debate (team vs team debate) with you joining the side *against* the \<id>.
* **pta** \<id>
    - Start a one-on-one "Panic Talk Action" debate with targeted player!
    - Unlike /cs, a Panic Talk Action (PTA) cannot evolve into a Scrum Debate.
    - Expires in 5 minutes.
* **concede** \<id>
    - Concede a trial minigame and withdraw from either team you're part of.
## Character
* **switch** \<name>
    - Switch to another character. If you are a moderator and the specified character is currently being used, the current user of that character will be automatically reassigned a character.
* **pos** \<name>
    - Set the place your character resides in the area.
* **forcepos** \<pos> \<target>
    - Set the place another character resides in the area.
* **charselect** [id] [char]
    - Enter the character select screen, or force another user to select another character.
    - Optional [char] forces them into that specific character folder/ID.
* **randomchar**
    - Select a random character.
* **charcurse** \<id> [charids...]
    - Lock a user into being able to choose only from a list of characters.
* **uncharcurse** \<id>
    - Remove the character choice restrictions from a user.
* **charids**
    - Show character IDs corresponding to each character name.
* **reload**
    - Reload a character to its default position and state.
* **blind**
    - Blind the targeted player(s) from being able to see or talk IC.
* **unblind**
    - Undo effects of the /blind command.
* **player_move_delay** \<id> [delay]
    - Set the player's move delay to a value in seconds. Can be negative.
    - Delay must be from -1800 to 1800 in seconds or empty to check.
    - If only delay is provided, you will be setting your own move_delay.
* **player_hide** \<id(s)>
    - Hide player(s) from /getarea and playercounts.
    - If <id> is *, it will hide everyone in the area excluding yourself and CMs.
* **player_unhide** \<id(s)>
    - Unhide player(s) from /getarea and playercounts.
    - If <id> is *, it will unhide everyone in the area excluding yourself and CMs.
* **hide** \<evi_name/id>
    - Try to hide in the targeted evidence name or ID.
* **unhide**
    - Stop hiding.
* **sneak**
    - Begin sneaking a.k.a. hide your area moving messages from the OOC.
* **unsneak**
    - Stop sneaking a.k.a. show your area moving messages in the OOC.
* **listen_pos** [pos(s)]
    - Start only listening to your currently occupied pos.
    - All messages outside of that pos will be reflected in the OOC.
    - Optional argument(s) is a list of positions you want to listen to.
* **unlisten_pos**
    - Undo the effects of /listen_pos command so you stop listening to the position(s).
* **save_character_data** \<path>
    - Save the move_delay, keys, etc. for characters into a file in the storage/character_data/ folder.
* **load_character_data** \<path>
    - Load the move_delay, keys, etc. for characters from a file in the storage/character_data/ folder.
* **keys_set** \<char> [key(s)]
    - Sets the keys of the target client/character folder/character id to the key(s). Keys must be a number like 5 or a link eg. 1-5.
* **keys_add** \<char> [key(s)]
    - Adds the keys of the target client/character folder/character id to the key(s). Keys must be a number like 5 or a link eg. 1-5.
* **keys_remove** \<char> [key(s)]
    - Remvove the keys of the target client/character folder/character id from the key(s). Keys must be a number like 5 or a link eg. 1-5.
* **keys** [target_id]
    - Check your own keys, or someone else's (if admin).
    - Keys allow you to /lock or /unlock specific areas, OR area links if it's formatted like 1-5
* **kms**
    - Stands for Kick MySelf - Kick other instances of the client opened by you.
    - Useful if you lose connection and the old client is ghosting.
* **chardesc** [desc/id]
    - Look at your own character description if no arugments are provided.
    - Look at another person's character description if only ID is provided.
    - Set your own character description if description is provided instead of ID.
        - Do note that the first sentence of your chardesc is displayed during area transfer messages!
    - To set someone else's char desc as an admin/GM, or look at their desc, use /chardesc_set or /chardesc_get.
* **chardesc_set** \<id> [desc]
    - Set someone else's character description to desc or clear it.
* **chardesc_get** \<id>
    - Get someone else's character description.
* **narrate** [on|off]
    - Speak as a Narrator for your next emote.
    - If using 2.9.1, when you speak IC only the chat box will be affected, making you "narrate" over the current visuals.
* **blankpost** [on|off]
    - Use a blank image for your next emote (base/misc/blank.png, will be a missingno if you don't have it)
    - tog can be `on`, `off` or empty.
* **firstperson** [on|off]
    - Speak as a Narrator for your next emote, but only to yourself. Everyone else will see the emote you used.
    - If using 2.9.1, when you speak IC only the chat box will be affected.
    - tog can be `on`, `off` or empty.
## Fun
* **disemvowel** \<id>
    - Remove all vowels from a user's IC chat.
* **undisemvowel** \<id>
    - Give back the freedom of vowels to a user.
* **shake** \<id>
    - Scramble the words in a user's IC chat.
* **unshake** \<id>
    - Give back the freedom of coherent grammar to a user.
## Hubs
* **hub** [id/name]
    - List hubs, or go to another hub.
### Saving/loading
* **save_hub** \<name>
    - Save the current Hub in the server's storage/hubs/\<name>.yaml file.
    - If blank and you're a mod, it will save to server's config/areas_new.yaml for the server owner to approve.
* **load_hub** \<name>
    - Load Hub data from the server's storage/hubs/\<name>.yaml file.
    - If blank and you're a mod, it will reload the server's config/areas.yaml.
* **list_hubs**
    - Show all the available hubs for loading in the storage/hubs/ folder.
* **clear_hub**
    - Clear the current hub and reset it to its default state.
* **rename_hub** \<name>
    - Rename the hub you are currently in to \<name>.
### Area Creation system
* **area_create** [name]
    - Create a new area.
    - Newly created area's evidence mod will be HiddenCM.
    - Optional name will rename it to that as soon as its created.
* **area_remove** \<id>
    - Remove specified area by Area ID.
* **area_rename** \<name>
    - Rename area you are currently in to \<name>.
* **area_swap** \<id> \<id>
    - Swap areas by Area IDs while correcting links to reference the right areas.
* **area_switch** \<id> \<id>
    - Switch areas by Area IDs without correcting links.
* **area_pref** [pref] [on/true/off/false]
    - Toggle a preference on/off for an area.
    - Leave pref out to see available prefs.
    - Leave on/true and off/false to toggle the pref.
    - The list of preferences is available [here](prefs.md).
* **area_move_delay** [delay]
    - Set the area's move delay to a value in seconds. Can be negative.
    - Delay must be from -1800 to 1800 in seconds or empty to check.
* **hub_move_delay** [delay]
    - Set the hub's move delay to a value in seconds. Can be negative.
    - Delay must be from -1800 to 1800 in seconds or empty to check.
* **toggle_replace_music**
    - Toggle the hub music list to replace the server's music list.
* **arup_enable**
    - Enable the ARea UPdate system for this hub.
    - ARUP system is the extra information displayed in the A/M area list, as well as being able to set /status.
* **arup_disable**
    - Disable the ARea UPdate system for this hub.
* **hide_clients**
    - Hide the playercounts for this Hub's areas.
* **unhide_clients**
    - Unhide the playercounts for this Hub's areas.
### General
* **follow**
    - Follow targeted character ID.
* **unfollow**
    - Stop following whoever you are following.
* **info** [info]
    - Check the information for the current Hub, or set it.
* **gm** \<id>
    - Add a game master for the current Hub.
    - If id is not provided, try to claim GM if none exist.
* **ungm**
    - Remove a game master from the current Hub.
    - If blank, demote yourself from being a GM.
* **broadcast** \<id(s)>
    - Start broadcasting your IC, Music and Judge buttons to specified area ID's.
    - To include all areas, use /broadcast all.
    - /clear_broadcast to stop broadcasting.
* **clear_broadcast**
    - Stop broadcasting your IC, Music and Judge buttons.
## Messaging
* **a**  \<area> \<message>
    - Send a message to an area that you are a CM in.
* **s** \<message>
    - Send a message to all areas that you are a CM in.
* **g** \<message>
    - Broadcast a server-wise message.
* **h** \<message>
    - Broadcast a message to all areas in the hub.
* **m** \<message>
    - Send a message to all online moderators.
* **lm** \<message>
    - Send a message to everyone in the current area, speaking officially.
* **announce** \<message>
    - Make a server-wide announcement.
* **toggleglobal**
    - Mute global chat.
* **need** \<message>
    - Broadcast a need for a specific role in a case.
* **toggleadverts**
    - Mute advertisements.
* **pm** \<id|ooc-name|char-name> \<message>
    - Send a private message to another online user. These messages are not logged by the server owner.
* **mutepm**
    - Mute private messages.
## Music
* **currentmusic**
    - Show the current music playing.
* **getmusic**
    - Grab the last played track in this area.
* **jukebox_toggle**
    - Toggle jukebox mode. While jukebox mode is on, all music changes become votes for the next track, rather than changing the track immediately.
* **jukebox_skip**
    - Skip the current track.
* **jukebox**
    - Show information about the jukebox's queue and votes.
* **play** \<name>
    - Play a track and loop it. See /play_once for this command without looping.
* **play_once** \<name>
    - Play a track without looping it. See /play for this command with looping.
* **blockdj** \<id>
    - Prevent a user from changing music.
* **unblockdj** \<id>
    - Unblock a user from changing music.
* **musiclists**
    - Displays all the available music lists.
* **musiclist** [path]
    - Load a client-side music list. Pass no arguments to reset. /musiclists to see available lists.
    - Note: if there is a set area/hub music list, their music lists will take priority.
* **area_musiclist** [path]
    - Load an area-wide music list. Pass no arguments to reset. /musiclists to see available lists.
    - Area list takes priority over client lists.
* **hub_musiclist** [path]
    - Load a hub-wide music list. Pass no arguments to reset. /musiclists to see available lists.
    - Hub list takes priority over client lists.
* **random_music** [category]
    - Play a random track from your current muisc list. If supplied, [category] will pick the song from that category.
    - Usage: /random_music [category]
## Roleplay
* **roll** [value/XdY] ["+5"/"-5"/"*5"/"/5"]
    - Roll a die. The result is shown publicly.
    - Example: /roll 2d6 +5 would roll two 6-sided die and add 5 to every result.
    - Rolls a 1d6 if blank
    - X is the number of dice, Y is the maximum value on the die.
* **rollp** [value/XdY] ["+5"/"-5"/"*5"/"/5"]
    - Roll a die privately. Same as /roll but the result is only shown to you and the CMs.
    - Example: /roll 2d6 +5 would roll two 6-sided die and add 5 to every result.
    - Rolls a 1d6 if blank
    - X is the number of dice, Y is the maximum value on the die.
* **notecard** \<message>
    - Write a notecard that can only be revealed by a CM.
* **notecard_clear**
    - Clear all notecards as a CM.
* **notecard_reveal**
    - Reveal all notecards and their owners.
* **notecard_check**
    - Check all notecards and their owners privately with a message telling others you've done so.
* **vote** \<id>
    - Cast a vote for a particular user that can only be revealed by a CM.
* **vote_clear** [char_folder]
    - Clear all votes as a CM.
    - Include [char_folder] (case-sensitive) to only clear a specific voter.
* **vote_reveal**
    - Reveal the number of votes, the voters and those with the highest amount of votes.
* **vote_check**
    - Check the number of votes, the voters and those with the highest amount of votes privately with a message telling others you've done so.
* **rolla_reload**
    - Reload ability dice sets from a configuration file.
    - The configuration file is located in `config/dice.yaml`.
* **rolla_set** \<name>
    - Choose the set of ability dice to roll.
* **rolla**
    - Roll a specially labeled set of dice (ability dice).
* **coinflip**
    - Flip a coin. The result is shown publicly.
* **8ball** \<question>
    - Answers a question. The result is shown publicly.
    - The answers depend on the `8ball` preset in `config/dice.yaml`.
* **timer** \<id> [+/-][time] | \<id> start | \<id> \<pause|stop> | \<id> hide
    - Manage a countdown timer in the current area. Note that timer of ID 0 is hub-wide. All other timer ID's are local to area.