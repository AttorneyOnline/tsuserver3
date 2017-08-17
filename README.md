# tsuserver3

A Python based server for Attorney Online.

Requires Python 3.6.2 and the latest version of PyYAML  
Install PyYAML by doing
```python -m pip install --user pyyaml```

## How to use

* Rename `config_sample` to `config` and edit the values to your liking.  
* Run by using `start_server.py`. It's recommended that you use a separate virtual environment.

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
    - Locks your area.
* **area_unlock**
    - Unlocks your area.
* **invite** "ID"
    - Adds target in invite list of your area.
* **area_kick** "ID"
    - Kicks target and all his(same for all genders) multi-accs from your area and remove him from invite-list.
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
* **evidence_mod** <MOD>
    - Changes evidence_mod in this area. Possible values: FFA, CM, HiddenCM, Mods
        * **FFA**
            - Everyone can add, edit and remove evidence.
        * **Mods**
            - Only moderators can add, edit or remove evidence.
        * **CM**
            - Only CM (case-maker, look at /cm for more info) or moderators can add, edit or remove evidence.
        * **HiddenCM**
            - Same as CM, but every evidence have his "owner's position" that can be changed by CM or moderator, what means that only one side can see it (except for 'all'). After presenting evidence once his position changing to 'all'. Possible positions: 'def', 'pro', 'wit', 'jud', 'pos' (means that no one can see this evidence), 'all' (means that everyone can see this evidence).
* **allow_iniswap**
    - Toggle allow_iniswap var in this area. 
    - Even if iniswap at all is forbidden you can configure all-time allowed iniswaps in *iniswaps.yaml*

## License

This server is licensed under the GPLv3 license. See the
[LICENSE](LICENSE.md) file for more information.
