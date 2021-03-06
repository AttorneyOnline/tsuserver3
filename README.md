# tsuserver3

tsuserver3 is the official Python-based server for Attorney Online.

## Easy setup instructions

The server will not work out of the box. **You must follow these instructions.**

### Install Python

* Install the [latest version of Python](https://www.python.org/downloads/). **Python 2 will not work**, as tsuserver3 depends on async/await, which can only be found on Python 3.7 and newer.
  - If you run Windows, make sure to check the "Add Python to PATH" and install pip checkboxes in the installer
  - If you run anything other than Windows, you should read "Advanced setup instructions" below.
  
### Download tsuserver3

We recommend [Git](https://git-scm.com/downloads/guis) - it makes it very easy to update tsuserver. But we are power users and therefore inherently biased. You can instead download the latest zip of tsuserver with [this link](https://github.com/AttorneyOnline/tsuserver3/archive/master.zip). Extract it and put it wherever you want.

### Install dependencies

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
  
### Configure tsuserver

* **Rename `config_sample` to `config`**.
* Edit the values in the `.yaml` files to your liking. If you downloaded tsuserver from a zip and try to edit it from Notepad, the line breaks will be missing. That's because Notepad is stupid. Use [Notepad++](https://notepad-plus-plus.org/) instead like the pro you are.
* Be sure to check your YAML file for syntax errors. Use this website: http://www.yamllint.com/
  - *Use spaces only; do not use tabs.* That's another reason we recommend anything that isn't Notepad.
* You don't need to copy characters into the `characters` folder *unless* you specifically chose to disable iniswapping in an area (in `areas.yaml`). In this case, all tsuserver needs to know is the `char.ini` of each character. It doesn't need sprites.
* Don't forget to forward ports on your router. You will need to forward both the regular port and the webAO port.

### Run

* Run by either double-clicking `start_server.py` or typing in `py -3 start_server.py` if you use both Python 2 and 3. It is normal to not see any output once you start the server.
  - To stop the server, press Ctrl+C multiple times.

## Advanced setup instructions

For servers that are intended to run for an extended period of time, Linux is recommended. Linux distros have a significantly more consistent and sane environment compared to Windows and macOS. These days, Microsoft is trying to cater the operating system it happened to prepackage with Candy Crush to power users by sticking a successful kernel inside its failed Win32 kernel, so you can try [that abomination](https://docs.microsoft.com/en-us/windows/wsl/install-win10) ([or its successor](https://docs.microsoft.com/en-us/windows/wsl/wsl2-install)) if you want. Or you can just use [a darn virtual machine](https://www.virtualbox.org/) instead.

I will just assume from now on that you have managed to produce an object that runs Linux.

### Using Docker

The easiest way to set up and start tsuserver is with the Dockerfile. You just [install Docker](https://get.docker.com/) and [install Docker Compose](https://docs.docker.com/compose/install/).

Once you have everything configured, do `sudo docker-compose up`. It will build the image and start tsuserver up for you. If you accidentally restart the server, the container will automatically start back up. If you're not understanding why it's starting, try starting it up manually:

```sh
sudo docker run -it -d -v `pwd`/storage:/app/storage -v `pwd`/logs:/app/logs  -v `pwd`/config:/app/config -p 27018:27018 -p 27017:27017 --restart=unless-stopped tsuserver
```

Here is a breakdown of the command:
 * `-it` puts an *interactive* *terminal* so that the output of the command line can be reaped later with `docker logs`. Without these options, the output is closed and printing things to the log will then break Python.
 * `-d` starts the container in the background (`detached`).
 * `-v SOURCE:TARGET` mounts the SOURCE directory on the host filesystem into the container's virtual filesystem at the TARGET location, so that we can modify server files without having to rebuild the entire image. However, SOURCE can't be a relative path, so we make an absolute path with `pwd`.
 * `-p SOURCE:TARGET` exposes port SOURCE inside the container as port TARGET in the whole machine. This way, a port can be connected to by anyone, not just the machine which Docker is being run in.
 * `--restart=unless-stopped` sets the restart policy to always restart, even after reboot, unless the container is explicitly stopped with `docker stop`.
 * `tsuserver` is the name of the image to start a container from.

Docker is a nifty tool, although I admit that setting it up and understanding how to use it can be tedious.

### Alternative: Using `venv`

`venv` is a tool built into Python to create a virtual Python environment to install packages in. It reduces the risk of mixing up Python versions and package versions. Sometimes, it's even necessary if `pip` installs require sudo privileges. (`sudo pip install` is highly frowned upon as it regularly causes conflicts with the system's own package manager. Don't do it, use `venv` instead!)

Suppose you installed tsuserver in `/home/me/tsuserver` (protip: this path is the same as `~me/tsuserver`).

You can create a venv with the following command:

```sh
python3 -m venv /home/me/tsuserver/.venv
```

Then activate the venv:

```sh
source /home/me/tsuserver/.venv/bin/activate
```

Install requirements:

```sh
cd /home/me/tsuserver
pip install -r requirements.txt
```

Start the server:

```sh
python start_server.py
```

You will always need to activate the venv before starting the server.

Refer to ["Creating Virtual Environments"](https://docs.python.org/3/library/venv.html#creating-virtual-environments) in the Python documentation for more information.

To keep the server running even after closing the terminal:
 * Use a multiplexer, such as screen or tmux. These programs let you have multiple terminals open in a single window, and detach/reattach with them freely. They are extremely convenient.
 * Create a systemd service. Not for the faint of heart.
 * Use Docker instead.

## Commands

Good-to-know commands are marked with a :star:.

### Administration

* **motd**
    - Show the message of the day.
* :star: **help** [command]
    - Show help for a command, or show general help.
* :star: **kick** <ipid|*|**> [reason]
    - Kick a player.
    - Special cases:
        - "*" kicks everyone in the current area.
        - "**" kicks everyone in the server.
* :star: **ban**
    - Ban a user. If a ban ID is specified instead of a reason, then the IPID is added to an existing ban record.
    - Ban durations are 6 hours by default.
    - Usage 1: `/ban <ipid> "reason" ["<N> <minute|hour|day|week|month>(s)|perma"]`
    - Usage 2: `/ban <ipid> <ban_id>`
* **banhdid**
    - Ban both a user's HDID and IPID.
* **unban** <ban_id...>
    - Unban a list of users.
    - You need a ban ID to unban a user. Ban IDs are automatically included in ban reasons. Use `/baninfo <ban_id>` for more information about a ban.
* **mute** <ipid>
    - Prevent a user from speaking in-character.
* **unmute** <ipid|"all">
    - Unmute a user.
* :star: **login** <password>
    - Login as a moderator.
* :star: **refresh**
    - Reload all moderator credentials, server options, and commands without restarting the server.
* **online**
    - Show the number of players online.
* **mods**
    - Show a list of moderators online.
* **unmod**
    - Log out as a moderator.
* **ooc_mute** <ooc-name>
    - Prevent a user from talking out-of-character.
* **ooc_unmute** <ooc-name>
    - Allow an OOC-muted user to talk out-of-character.
* **bans**
    - Get the 5 most recent bans.
    - This can lag the server depending on the size of the database, so be judicious in its use.
* :star: **baninfo** <id> ['ban_id'|'ipid'|'hdid']
    - Get information about a ban.
    - By default, id identifies a ban_id.

### Area

* **bg** <background>
    - Set the background of a room.
* **bglock**
    - Toggle whether or not non-moderators are allowed to change the background of a room.
* **allow_iniswap**
    - Toggle whether or not users are allowed to swap INI files in character folders to allow playing as a character other than the one chosen in the character list.
    - To enforce that no custom emotes at all are used, copy the character's char.ini file to the `characters` folder.
    - Even if iniswap is forbidden, you can use `iniswaps.yaml` to configure iniswaps that are always allowed.
* **allow_blankposting**
    - Toggle whether or not in-character messages purely consisting of spaces are allowed.
* **force_nonint_pres**
    - Toggle whether or not all pre-animations lack a delay before a character begins speaking.
* :star: **status** <idle|rp|casing|looking-for-players|lfp|recess|gaming>
    - Show or modify the current status of a room.
* **area** [id]
    - List areas, or go to another area/room.
* **getarea**
    - Show information about the current area.
* :star: **getareas**
    - Show information about all areas.
* **area_lock**
    - Prevent users from joining the current area.
* **area_spectate**
    - Allow users to join the current area, but only as spectators.
* **area_unlock**
    - Allow anyone to freely join the current area.
* **invite** <id>
    - Allow a particular user to join a locked or spectator-only area.
* **uninvite** <id>
    - Revoke an invitation for a particular user.
* **area_kick** <id> [destination]
    - Remove a user from the current area and move them to another area.
    - If the area is locked, this also removes the user from the invite list.
    - If the user is using multiple clients, then this targets all of the clients in the current area.
    - If the destination is not specified, the destination defaults to area 0.
* **getafk** [all]
    - Show currently AFK-ing players in the current area or in all areas.

### Casing

* **doc** [url]
    - Show or change the link for the current case document.
* **cleardoc**
    - Clear the link for the current case document.
* **evidence_mod** <FFA|Mods|CM|HiddenCM>
    - Change the evidence privilege mode.
    * **FFA**
        - Everyone can add, edit and remove evidence.
    * **Mods**
        - Only moderators can add, edit or remove evidence.
    * **CM**
        - Only the CM (case-maker, look at /cm for more info) or moderators can add, edit or remove evidence.
    * **HiddenCM**
        - Same as CM, but every evidence has a preset "owner's position" which can be set by a CM or moderator, such that only one side/position of the court may see the evidence. After presenting the evidence, the position of the evidence changes to "all." Possible positions include def (defense), pro (prosecutor), wit (witness), jud (judge), pos (hidden from everyone), and all (everyone can see the evidence).
* **evi_swap**  <id> <id>
    - Swap the positions of two evidence items on the evidence list.
    - The ID of each evidence is simply its ordinal number starting from 0.
* :star: **cm** <id>
    - Add a case manager for the current room.
* **uncm** <id>
    - Remove a case manager from the current area.
* **setcase**
    - Set the positions you are interested in taking for a case. (This command is used internally by the 2.6 client.)
* **anncase** <message> <def> <pro> <jud> <jur> <steno>
    - Announce that a case is currently taking place in this area,
needing a certain list of positions to be filled up.
* **blockwtce** <id>
    - Prevent a user from using Witness Testimony/Cross Examination buttons as a judge.
* **unblockwtce** <id>
    - Allow a user to use WT/CE again.
* **judgelog**
    - List the last 10 uses of judge controls in the current area.
* **afk**
    - Sets your player as AFK in player listings.

### Character

* **switch** <name>
    - Switch to another character. If you are a moderator and the specified character is currently being used, the current user of that character will be automatically reassigned a character.
* **pos** <name>
    - Set the place your character resides in the room.
* **forcepos** <pos> <target>
    - Set the place another character resides in the room.
* **charselect** [id]
    - Enter the character select screen, or force another user to select another character.
* **randomchar**
    - Select a random character.
* **charcurse** <id> [charids...]
    - Lock a user into being able to choose only from a list of characters.
* **uncharcurse** <id>
    - Remove the character choice restrictions from a user.
* **charids**
    - Show character IDs corresponding to each character name.
* **reload**
    - Reload a character to its default position and state.

### Fun

* **disemvowel** <id>
    - Remove all vowels from a user's IC chat.
* **undisemvowel** <id>
    - Give back the freedom of vowels to a user.
* **shake** <id>
    - Scramble the words in a user's IC chat.
* **unshake** <id>
    - Give back the freedom of coherent grammar to a user.

### Messaging

* **a**  <area> <message>
    - Send a message to an area that you are a CM in.
* **s** <message>
    - Send a message to all areas that you are a CM in.
* **g** <message>
    - Broadcast a message to all areas.
* :star: **gm** <message>
    - Broadcast a message to all areas, speaking officially.
* **m** <message>
    - Send a message to all online moderators.
* :star: **lm** <message>
    - Send a message to everyone in the current area, speaking officially.
* :star: **announce** <message>
    - Make a server-wide announcement.
* **toggleglobal**
    - Mute global chat.
* **need** <message>
    - Broadcast a need for a specific role in a case.
* **toggleadverts**
    - Mute advertisements.
* **pm** <id|ooc-name|char-name> <message>
    - Send a private message to another online user. These messages are not logged by the server owner.
* **mutepm**
    - Mute private messages.

### Music

* **currentmusic**
    - Show the current music playing.
* **jukebox_toggle**
    - Toggle jukebox mode. While jukebox mode is on, all music changes become votes for the next track, rather than changing the track immediately.
* **jukebox_skip**
    - Skip the current track.
* **jukebox**
    - Show information about the jukebox's queue and votes.
* **play** <name>
    - Play a track.
* **blockdj** <id>
    - Prevent a user from changing music.
* **unblockdj** <id>
    - Unblock a user from changing music.

### Roleplay

* :star: **roll** [max value] [rolls]
    - Roll a die. The result is shown publicly.
* **rollp** [max value] [rolls]
    - Roll a die privately.
* **notecard** <message>
    - Write a notecard that can only be revealed by a CM.
* **notecard_clear**
    - Erase a notecard.
* **notecard_reveal**
    - Reveal all notecards and their owners.
* **rolla_reload**
    - Reload ability dice sets from a configuration file.
    - The configuration file is located in `config/dice.yaml`.
* **rolla_set** <name>
    - Choose the set of ability dice to roll.
* **rolla**
    - Roll a specially labeled set of dice (ability dice).
* **coinflip**
    - Flip a coin. The result is shown publicly.
* **8ball** <question>
    - Answers a question. The result is shown publicly.
    - The answers depend on the `8ball` preset in `config/dice.yaml`.
* **timer** \<id> [+/-][time] | \<id> start | \<id> \<pause|stop> | \<id> hide
    - Manage a countdown timer in the current area. Note that timer of ID 0 is global. All other timer IDs are local to the area.

## License

This server is licensed under the AGPLv3 license. In short, if you use a modified version of tsuserver3, you *must* distribute its source licensed under the AGPLv3 as well, and notify your users where the modified source may be found. The main difference between the AGPL and the GPL is that for the AGPL, network use counts as distribution. If you do not accept these terms, you should use [serverD](https://github.com/Attorney-Online-Engineering-Task-Force/serverD), which uses GPL rather than AGPL.

See the [LICENSE](LICENSE.md) file for more information.
