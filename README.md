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
* **area** "area number" 
    - Displays all areas when blank, swaps to area with number
* **getarea** 
    - Shows the current characters in your area
* **getareas** 
    - Shows all characters in all areas
* **doc** "url" 
    - Gives the doc url if blank, updates the doc url
* **cleardoc** 
    - Clears the doc url
* **status** "status" 
    - Shows current areas status if blank, updates the status
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
* **bg** "background" 
    - Changes the current background
* **roll** "max" 
    - Rolls a 1D6 if blank
* **coinflip**
    - Flips a coin
* **currentmusic** 
    - Displays the current music
* **evi_swap** <id1> <id2>
    - Swaps <id1> and <id2> evidence.
* **cm**
    - Makes you a CM of this area.
### CM Commands
* **area_lock**
    - Locks your area, preventing anyone outside of the invite list from speaking IC.
* **area_unlock**
    - Unlocks your area.
* **invite** "ID"
    - Adds target in invite list of your area.
* **uninvite** "ID"
    - Removes target from invite list of your area.
* **forcepos** "position" [target]
    - Forcibly change [target]'s position. Leave blank to affect everyone in area.
    - Positions: 'def', 'pro', 'hld', 'hlp', 'jud', 'wit'
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
* **area_kick** "ID" [area]
    - Kicks target and all of their multi-accs from your area to area 0 or specified [area] and removes them from invite-list should the area be locked.
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
* **blockwtce** "target"
    - Blocks the target from using Witness Testimony/Cross Examination signs.
* **unblockwtce** "target"
    - Undo previous command.
* **evidence_mod** <MOD>
    - Changes evidence_mod in this area. Possible values: FFA, CM, HiddenCM, Mods
        * **FFA**
            - Everyone can add, edit and remove evidence.
        * **Mods**
            - Only moderators can add, edit or remove evidence.
        * **CM**
            - Only CM (case-maker, look at /cm for more info) or moderators can add, edit or remove evidence.
        * **HiddenCM**
            - Same as CM, but every evidence has a preset "owner's position" which can be set by a CM or moderator, such that only one side/position of the court may see the evidence. After presenting the evidence, the position of the evidence changes to "all." Possible positions include def (defense), pro (prosecutor), wit (witness), jud (judge), pos (hidden from everyone), and all (everyone can see the evidence).
* **allow_iniswap**
    - Toggle allow_iniswap var in this area. 
    - Even if iniswap at all is forbidden you can configure all-time allowed iniswaps in *iniswaps.yaml*

## License

This server is licensed under the AGPLv3 license. In short, if you use a modified version of tsuserver3, you *must* distribute its source licensed under the AGPLv3 as well, and notify your users where the modified source may be found. The main difference between the AGPL and the GPL is that for the AGPL, network use counts as distribution. If you do not accept these terms, you should use [serverD](https://github.com/Attorney-Online-Engineering-Task-Force/serverD), which uses GPL rather than AGPL.

See the [LICENSE](LICENSE.md) file for more information.
