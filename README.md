# tsuserver3

tsuserver3 is the official Python-based server for Attorney Online.

## Easy setup instructions

The server will not work out of the box. **You must follow these instructions.**

### Install Python

* Install the [latest version of Python](https://www.python.org/downloads/). **Python 2 will not work**, as tsuserver3 depends on async/await, which can only be found on Python 3.7 and newer.
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

### User Commands

* **help**
    - Links to this readme.
* **g** "message" 
    - Sends a serverwide message.
* **toggleglobal** 
    - Toggles global on and off.
* **need** "message" 
    - Sends a serverwide advert.
* **toggleadverts** 
    - Toggles adverts on and off.
* **area** "area number" 
    - Displays all areas when blank, swaps to area with number.
* **getarea** 
    - Shows the current characters in your area.
* **getareas** 
    - Shows all characters in all areas.
* **afk**
    - Toggles the afk status on and off.
* **getafk** [all]
    - Displays players with the afk status in the current area when   
    blank, the [all] argument displays afkers in all areas.
* **doc** "url" 
    - Gives the doc url if blank, updates the doc url.
* **cleardoc** 
    - Clears the doc url.
* **status** "status" 
    - Shows current areas status if blank, updates the status.
    - Statuses: 'idle', 'building-open', 'building-full', 'casing-open', 'casing-full', 'recess'.
* **pm** "target" "Message" 
    - PMs the target, can either be character name or OOC name.
* **pmmute**
    - Disables all incoming PMs.
* **charselect** 
    - Puts you back to char select screen.
* **reload** 
    - Reloads your character ini.
* **switch** "character" 
    - Quick switch to a character.
* **randomchar** 
    - Randomly chooses a character.
* **pos** "position" 
    - Changes your position in the court.
    - Positions: 'def', 'pro', 'hld', 'hlp', 'jud', 'wit'.
* **bg** "background" 
    - Changes the current background.
* **notecard** "message"
    - Write a notecard that can only be revealed by a CM.
* **notecard_clear** 
    - Erase the notecard written by you.
* **roll** "max" 
    - Rolls a 1D6 if blank.
* **rolla_set** "set"
    - Changes the current ability set.
* **rolla**
    - Rolls an ability depending on the current ability set.
    - Details specified in the `dice.yaml` file.
* **coinflip**
    - Flips a coin.
* **8ball** "question"
    - Outputs a random answer to a given question.
    - Replies can be changed in the `dice.yaml` file.
* **currentmusic** 
    - Displays the current music.
* **evi_swap** <id1> <id2>
    - Swaps <id1> and <id2> evidence.
* **cm**
    - Makes you a CM of this area.
### CM Commands
* **area_lock**
    - Locks your area, preventing anyone outside of the invite list from speaking IC.
* **area_unlock**
    - Unlocks your area.
* **area_spectate**
    - Allow users to join the current area, but only as spectators.
* **invite** "ID"
    - Adds target in invite list of your area.
* **uninvite** "ID"
    - Removes target from invite list of your area.
* **forcepos** "position" "target"
    - Forcibly change target's position. Leave blank to affect everyone in area.
    - Positions: 'def', 'pro', 'hld', 'hlp', 'jud', 'wit'
* **notecard_reveal**
    - Reveal all notecards and their owners in the area.
### Mod Commands
* **login** "Password"
    - Logs you in as a moderator.
* **gm** "Message" 
    - Sends a serverwide message with mod tag.
* **lm** "Message" 
    - Sends an area OOC message with mod tag.
* **play** "song.mp3" 
    - Plays a song.
* **judgelog** 
    - Displays the last judge actions in the current area.
* **announce** "Message" 
    - Sends a serverwide announcement.
* **charselect** "ID"
    - Kicks a player back to the character select screen. If no ID was entered then target yourself.
* **kick** "IPID" 
    - Kicks the targets with this IPID.
* **area_kick** "ID" [area]
    - Kicks target and all of their multi-accs from your area to area 0 or specified [area] and removes them from invite-list should the area be locked.
* **banhdid** "IPID" "reason" "duration"
    - Bans the HDID (HDID is linked to ipid so both bans happens in a same time).
* **ban** "IPID" "reason" "duration"
    - Bans the IPID.
* **unban** "IPID" 
    - Unbans the specified IPID.
* **mute** "Target" 
    - Mutes the target from all IC actions, can be IP or Character name.
* **unmute** "Target","all" 
    - Unmutes the target, "all" will unmute all muted clients.
* **oocmute** "Target" 
    - Mutes the target from all OOC actions via OOC-name.
* **oocunmute** "Target" 
    - Unmutes the target.
* **bglock** 
    - Toggles the background lock in the current area.
* **disemvowel** "Target"
    - Removes the vowels from everything said by the target.
* **undisemvowel** "Target"
    - Lifts the disemvowel curse from the target.
* **blockdj** "target"
    - Blocks the target from changing music.
* **unblockdj** "target"
    - Unblocks the target from changing music.
* **blockwtce** "target"
    - Blocks the target from using Witness Testimony/Cross Examination signs.
* **unblockwtce** "target"
    - Unblocks the target from using Witness Testimony/Cross Examination signs.
* **evidence_mod** <MOD>
    - Changes evidence_mod in this area. Possible values: FFA, CM, HiddenCM, Mods.
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
