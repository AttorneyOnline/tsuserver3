# tsuserver3

A Python-based server for Attorney Online.

Requires Python 3.6+ and PyYAML.

## How to use

* Install the latest version of Python. **Python 2 will not work**, as tsuserver3 depends on async/await, which can only be found on Python 3.5 and newer.
  - If your system supports it, it is recommended that you use a separate virtual environment, such as [Anaconda](https://www.continuum.io/downloads) for Windows, or [virtualenv](https://virtualenv.pypa.io/en/stable/) for everyone else (it runs itself using Python).
* Open Command Prompt or your terminal, and change to the directory where you downloaded tsuserver3 to. You can do this in two ways:
  - Go up one folder above the tsuserver3 folder, Shift + right click the tsuserver3 folder, and click `Open command window here`. This is the easiest method.
  - Copy the path of the tsuserver3 folder, open the terminal, and type in `cd "[paste here]"`, excluding the brackes, but including the quotation marks if the path contains spaces.
* To install PyYAML and dependencies, type in the following:
  ```bash
  python -m pip install --user -r requirements.txt
  ```
  If you are using Windows and have both Python 2 and 3 installed, you may do the following:
  ```batch
  py -3 -m pip install --user -r requirements.txt
  ```
  This operation should not require administrator privileges, unless you decide to remove the `--user` option.
* Rename `config_sample` to `config` and edit the values to your liking. Be sure to check your YAML file for syntax errors. *Use spaces only; do not use tabs.*
* Run by either double-clicking `start_server.py` or typing in `python start_server.py`, or `py -3 start_server.py` if you use both Python 2 and 3. It is normal to not see any output once you start the server.
  - To stop the server, press Ctrl+C multiple times.

## 

## Commands

### User Commands

* **help**
    - Links to this readme
* **g** "message" 
    - Sends a serverwide message
* **toggleglobal** 
    - Toggles global on and off
* **need** "message" 
    - Sends a serverwide advert
* **toggleadverts** 
    - Toggles adverts on and off
* **hub** "hub number" OR "hub name"
    - Displays all hubs when blank, swaps to hub with number/name
* **area** <number> OR <name>
    - Displays all areas when blank, swaps to area with number/name
* **getarea** 
    - Shows the current characters in your area
* **getareas** 
    - Shows all characters in all areas
* **doc** "url or txt" 
    - Gives the doc url/text if blank, updates the doc url/text in current hub if provided
* **cleardoc** 
    - Clears the doc url/text
* **desc** <string>
    - Display the area description if blank, set that area's description to <desc> otherwise.
* **status** "status" 
    - Shows current areas status if blank, updates the status if filled
    - Statuses: 'idle', 'building-open', 'building-full', 'casing-open', 'casing-full', 'recess'
* **pm** "target" "Message" 
    - PMs the target, can either be character name or OOC name
* **pmmute**
    - Disables all incoming PMs
* **charselect** 
    - Puts you back to char select screen
* **reload** 
    - Reloads your character ini
* **switch** "character" 
    - Quick switch to a character
* **randomchar** 
    - Randomly chooses a character
* **pos** "position" 
    - Changes your position in the court
    - Positions: 'def', 'pro', 'hld', 'hlp', 'jud', 'wit'
* **roll** "max" 
    - Rolls a 1D6 if blank
* **coinflip**
    - Flips a coin
* **currentmusic** 
    - Displays the current music
* **evi_swap** <id1> <id2>
    - Swaps <id1> and <id2> evidence.
* **evi_edit** <id: int> <name: string> <description: string> <image: string>
    - [DEPRECATED] A command emulating the in-client editing interface. Replace string with . (period) if you wish to keep original data.
* **sneak** <on/off or blank>
    - Toggles whether or not you transfering areas will be announced in local area chat, e.g. "Gym: Phoenix leaves to Hallway." "Hallway: Phoenix enters from Gym."
* **peek** <number> OR <name>
    - Peek inside the target area to see characters inside of it. Must be accessible from your current area. If the area is locked, people will be alerted of your attempt to see inside. CM's, mods and spectators are ignored.

### CM Commands
* **cm** <id1>
    - Makes you a CM of this area. As a Master CM you can also assign co-cm's with <id1>
* **cms**
    - Shows you the list of CMs in this hub.
* **uncm**
    - Removes your CM status
* **cmlogs** <on/off or blank>
    - Changes whether or not you can see CM-related logging features. Useful for alt. clients which you want to keep clean of OOC logging or if you don't need to meticulously track everyone down in the first place.
* **cleanup** <yes>
    - Cleans up the hub completely, restoring it to a pristine state. Use this to clean up after RP's. Warning: all unsaved data will be lost!
* **lock** <id1> <id2> <idx>
    - Locks your area (or list of areas if you provide <id1> <id2> <idx>), preventing anyone outside of the invite list from speaking IC.
* **unlock** <id1> <id2> <idx>
    - Unlocks your area (or list of areas if you provide <id1> <id2> <idx>).
* **forcepos** "position" [target]
    - Forcibly change [target]'s position. Leave blank to affect everyone in area.
    - Positions: 'def', 'pro', 'hld', 'hlp', 'jud', 'wit'
* **follow** <id> or blank
    - Follow specified character <id> when they move areas or display who you're following if left blank.
* **unfollow**
    - Stop following.
* **hide** <id>
    - Hide specified character <id> from /getarea
* **unhide** <id>
    - Unhide specified character <id> for /getarea
* **blind** <id>
    - Make specified character <id> unable to see or speak ICly unless receiving a /broadcast_ic message. Also disallow usage of /getarea.
* **unblind** <id>
    - Undo the /blind command for specified <id>
* **broadcast_ic** <id1> <id2> <idx> or <clear>
    - Blank to display the list of areas currently broadcasting your IC messages to. <idx> to add area(s) to the list. <clear> to reset the list.
* **iclogs** <numlines> <id>
    - Display last <numlines> of logged IC lines in area <id> in OOC. Max 50
* **savehub**
    - Save the area save data as an evidence file in area 0 of the hub.
* **loadhub**
    - Display instructions on how to load area save data using the evidence system.
* **akick** <id> <area#> (<hub#>)
    - Kicks target and all of their multi-accs from your area to area 0 or specified <area#> in same hub (or specified <hub#> if you're a mod)
* **player_move_delay** <id> (<delay>)
    - Sets the movement delay in seconds for the player. <delay> must be a value from 0 to 1800 in seconds. Leave blank to check current value.
* **area_move_delay** (<delay>)
    - Sets the movement delay in seconds for the area you're in. <delay> must be a value from 0 to 1800 in seconds. Leave blank to check current value.
* **hub_move_delay** (<delay>)
    - Sets the movement delay in seconds for the hub you're in. <delay> must be a value from 0 to 1800 in seconds. Leave blank to check current value.
* **maxplayers** (<num>)
    - Sets the amount of maximum possible player characters for the area. CM's, mods, spectators are ignored. <num> must be from -1 to 99, where -1 is infinite while 0 is allow only CM's, mods, spectators. Leave blank to check current value.
* **toggleooc**
    - Turn hub chat on/off.
   
### Area Commands
* **bg** "background" 
    - Changes the current background
* **area_add**
    - Add an area at the end of the area list
* **area_remove** <id>
    - Remove specified area while updating all existing access references to match.
* **area_swap** <id1> <id2>
    - Swaps first area ID with the second area ID while updating all existing access references to match.
* **poslock** <def> <hld> <pro> <hlp> <wit> <jud> <clear>
    - Lock the position of current area into provided pos. <clear> to unlock.
* **rename** <text>
    - Rename current area's display name to <text>
* **area_access** <id1> <id2> <idx>
    - Display area access numbers if blank, or set which areas are accessible from your area for movement. /area_access clear to clear the area access. Use area_link/area_unlink for two-way paths instead.
* **area_link** <id1> <id2> <idx>
    - Set up a two-way accessibility from and to your current area for listed ID's.
* **area_unlink** <id1> <id2> <idx>
    - Unlink specified areas from the area you're in.
* **evidence_mod** <MOD>
    - Changes evidence_mod in this area. Possible values: FFA, CM, HiddenCM, Mods
        * **FFA**
            - Everyone can add, edit and remove evidence.
        * **Mods**
            - Only moderators can add, edit or remove evidence.
        * **CM**
            - Only CM (case-maker, look at /cm for more info) or moderators can add, edit or remove evidence.
        * **HiddenCM**
            - Same as CM, but every evidence has a preset "owner's position" which can be set by a CM or moderator, such that only one side/position of the court may see the evidence.
            Possible positions include def (defense), hld (defense help), pro (prosecution), hlp (prosecution help), wit (witness), jud (judge), sea (seance), jur (jury), as well as
            pos (hidden from everyone), and all (everyone can see the evidence).
            There are also shorthands - defense (will display to def and hld), prosecution (will display to pro and hlp), benches (includes defense and prosecution), witness (includes wit and sea), and judge (includes jud and jur).
* **allow_iniswap**
    - Toggle allow_iniswap var in this area. 
    - Even if iniswap at all is forbidden you can configure all-time allowed iniswaps in *iniswaps.yaml*
* **akick** <id> <area#> (<hub#>)
    - Kicks target and all of their multi-accs from your area to area 0 or specified <area#> in same hub (or specified <hub#> if you're a mod)

### Mod Commands
* **login** "Password"
* **gm** "Message" 
    - Sends a serverwide message with mod tag
* **lm** "Message" 
    - Sends an area OOC message with mod tag
* **play** "song.mp3" 
    - Plays a song
* **judgelog** 
    - Displays the last judge actions in the current area
* **announce** "Message" 
    - Sends a serverwide announcement
* **charselect** "ID"
    - Kicks a player back to the character select screen. If no ID was entered then target yourself.
* **kick** "IPID" 
    - Kicks the targets with this IPID.
* **ban** "IPID" 
    - Bans the IPID (hdid is linked to ipid so all bans happens in a same time).
* **unban** "IPID" 
    - Unbans the specified IPID .
* **mute** "Target" 
    - Mutes the target from all IC actions, can be IP or Character name
* **unmute** "Target","all" 
    - Unmutes the target, "all" will unmute all muted clients
* **oocmute** "Target" 
    - Mutes the target from all OOC actions via OOC-name.
* **oocunmute** "Target" 
    - Unmutes the target.
* **bglock** 
    - Toggles the background lock in the current area
* **disemvowel** "Target"
    - Removes the vowels from everything said by the target
* **undisemvowel** "Target"
    - Lifts the disemvowel curse from the target
* **blockdj** "target"
    - Mutes the target from changing music. 
* **unblockdj** "target"
    - Undo previous command.

## License

This server is licensed under the AGPLv3 license. In short, if you use a modified version of tsuserver3, you *must* distribute its source licensed under the AGPLv3 as well, and notify your users where the modified source may be found. The main difference between the AGPL and the GPL is that for the AGPL, network use counts as distribution. If you do not accept these terms, you should use [serverD](https://github.com/Attorney-Online-Engineering-Task-Force/serverD), which uses GPL rather than AGPL.

See the [LICENSE](LICENSE.md) file for more information.
