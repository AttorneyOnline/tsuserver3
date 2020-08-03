"""
Extracts songs from the AO2 music folder into a yaml file for tsuserver3.
This script will look through the music files present in the given music folder
and add/update the respective song lengths in the music.yaml. It will preserve
the category and positioning of existing tracks, while new tracks are added
to the "Uncategorized" category.
You can also create a fresh music.yaml with this script.
You need ffmpeg/ffprobe installed for this to work.
"""

# ISC License
# 
# Copyright (c) 2018, oldmud0 (https://github.com/oldmud0)
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


import argparse
import os
import re
import subprocess
import sys
import yaml

from collections import OrderedDict


class NoAliasDumper(yaml.dumper.SafeDumper):
    """
    Makes sure a little annoyance of the super-complicated
    YAML format doesn't sneak into our innocent YAML files.
    """
    def ignore_aliases(self, _data):
        return True

# This lazy hack allows the ordering of items in the YAML to be preserved.
# Special thanks to https://stackoverflow.com/a/21912744/2958458

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    # Remember, we're inside a def right now
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))

    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)

    return yaml.load(stream, OrderedLoader)

def ordered_dump(data, stream=None, Dumper=NoAliasDumper, **kwds):
    class OrderedDumper(Dumper):
        pass

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    return yaml.dump(data, stream, OrderedDumper, **kwds)



# Parse arguments
yaml_path = "music.yaml"
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("yaml_path", metavar="yaml_path", type=str, help="path to music.yaml")
parser.add_argument("-n", "--no-new", action="store_true", help="do not add new songs to the music.yaml")
parser.add_argument("-s", "--new-only", action="store_true", help="only scan for new songs")

try:
    args = parser.parse_args()
except:
    parser.print_help()
    sys.exit(1)

yaml_path = args.yaml_path
no_new = args.no_new
new_only = args.new_only

if no_new and new_only:
    print("error: --no-new and --new-only flags conflict. Please only choose one.")
    sys.exit(1)

# Check if we are inside the base/sounds/music folder
path = os.getcwd()
if path.split("\\")[-1] != "music":
    print("error: You need to run this script from the music folder.")
    sys.exit(1)

# Read/parse music.yaml
config = None
try:
    with open(yaml_path, "r") as yaml_file:
        config = ordered_load(yaml_file.read())
except OSError:
    print(f"The YAML file {yaml_path} could not be opened. A new one will be created.")

# config will be none if the file could not be loaded or a blank file was loaded.
if config is None:
    config = []

# Extract song objects from each category
songs = []
for category in config:
    for track in category["songs"]:
        songs.append(track)
song_names = [s["name"] for s in songs]

# Check if there is a category called "Uncategorized"
# If not, create one
uncategorized_category = [c for c in config if c["category"] == "Uncategorized"]
uncategorized_category_present = True
if len(uncategorized_category) == 0:
    uncategorized_category_present = False
    uncategorized_category = OrderedDict([
        ("category", "Uncategorized"), ("songs", [])
    ])
else:
    uncategorized_category = uncategorized_category[0]

file_list = os.listdir(os.getcwd())
if new_only:
    file_list = [f for f in file_list if f not in song_names]

progress = 0
progress_max = len(file_list)
for file in file_list:
    progress += 1
    if file.split(".")[-1] not in ("mp3", "wav", "ogg", "opus"):
        continue
    try:
        # Invoke ffprobe to extract the length
        process = subprocess.Popen(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        out, err = process.communicate()
        length = float(out.decode("utf-8").strip().split("\r\n")[0])

        # Compose song/track object
        track = OrderedDict([
            ("name", file), ("length", length)
        ])

        # There could theoretically be the same song in multiple categories.
        # We'll cover the case just for the sake of it.
        entries = [s for s in songs if s["name"] == file]

        # Check if the song is in the list
        if len(entries) != 0:
            # Update the length property in each song entry
            # that matched the name criterion
            for entry in entries:
                entry["length"] = track["length"]
        elif not no_new:
            # Add it to the uncategorized category
            uncategorized_category["songs"].append(track)

        print(f"({progress}/{progress_max}) {file}" + " " * 15 + "\r", end="")
    except ValueError:
        print(f"Could not open track {file}. Skipping.")
    except KeyboardInterrupt:
        print()
        print("Scan aborted! No changes have been written to disk.")
        sys.exit(2)

print("Scan complete." + " " * 20)

# Add the uncategorized category if it was used
if not uncategorized_category_present and len(uncategorized_category["songs"]) != 0:
    config.append(uncategorized_category)

dump = ordered_dump(config, default_flow_style=False)

# Write the final config to file if everything went well
with open(yaml_path, "w") as yaml_file:
    yaml_file.write(dump)