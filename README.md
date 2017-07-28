# tsuserver3

A Python based server for Attorney Online.

Requires Python 3.6.2 and the latest version of PyYAML
Install PyYAML by doing
```python -m pip install --user pyyaml```

## How to use

* Rename `config_sample` to `config` and edit the values to your liking.  
* Run by using `start_server.py`. It's recommended that you use a separate virtual environment.

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
* **getip**
    - Gets the IPs of everyone in the current area
* **getips**
    - Gets the IPs of everyone in every area
* **charselect** "Target"
    - Kicks a player back to the character select screen
* **kick** "Target" 
    - Kicks the target, can be IP or character name
* **ban** "IP" 
    - Bans the IP
* **banhdid** "HDID"
    - Bans the HDID
* **unban** "IP" 
    - Unbans the specified IP
* **unbanhdid** "HDID"
    - Unbans the specified HDID
* **mute** "Target" 
    - Mutes the target from all IC actions, can be IP or Character name
* **unmute** "Target","all" 
    - Unmutes the target, "all" will unmute all muted clients
* **oocmute** "Target" 
    - Mutes the target from all OOC actions, can be OOC, IP or Character name
* **oocunmute** "Target" 
    - Unmutes the target, "all" will unmute all muted clients
* **bglock** 
    - Toggles the background lock in the current area

## License

This server is licensed under the GPLv3 license. See the
[LICENSE](LICENSE.md) file for more information.
