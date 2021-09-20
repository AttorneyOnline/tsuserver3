[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/I2I51SHXD)

# KFO-Server

KFO-Server is the official Python-based server for Attorney Online, forked from tsuserver3.

## Commands

Documentation: ["Commands"](https://github.com/Crystalwarrior/KFO-Server/blob/master/docs/commands.md). You may also use the /help documentation on the server.

## Easy setup instructions

The server will not work out of the box. **You must follow these instructions.**

### Install Python

* Install the [latest version of Python](https://www.python.org/downloads/). **Python 2 will not work**, as tsuserver3 depends on async/await, which can only be found on Python 3.7 and newer.
  - If you run Windows, make sure to check the "Add Python to PATH" and install pip checkboxes in the installer
  - If you run anything other than Windows, you should read "Advanced setup instructions" below.
  
### Download KFO-Server

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

## License

This server is licensed under the AGPLv3 license. In short, if you use a modified version of tsuserver3, you *must* distribute its source licensed under the AGPLv3 as well, and notify your users where the modified source may be found. The main difference between the AGPL and the GPL is that for the AGPL, network use counts as distribution. If you do not accept these terms, you should use [serverD](https://github.com/Attorney-Online-Engineering-Task-Force/serverD), which uses GPL rather than AGPL.

See the [LICENSE](LICENSE.md) file for more information.

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/I2I51SHXD)
