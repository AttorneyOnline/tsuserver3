# Area Prefs
This doc explains what each area preference is responsible for when you use the /area_pref command. Note this is still WIP!
If you're looking for the list of commands, it can be found [here](commands.md).

### Case Makers and above
* **bg_lock**
    - If True, this area's background cannot be changed by anyone that's not a CM and above.
    - If False, normal users can change the background, provided they're not muted/spectating and the area is not dark (/lights off).
    - Default: *False*
* **showname_changes_allowed**
    - If True, users are allowed to change their showname.
    - If False, only CMs and above are allowed to change their showname.
    - Default: *True*
* **shouts_allowed**
    - If True, users are allowed to use Objection/Hold It/Take That/Custom shouts.
    - If False, only CMs and above can use shouts.
    - Default: *True*
* **jukebox**
    - Default: *False*
* **non_int_pres_only**
    - Default: *False*
* **blankposting_allowed**
    - Default: *True*
* **hide_clients**
    - Default: *False*
* **client_music**
    - Default: *True*
* **replace_music**
    - Default: *False*
* **can_dj**
    - Default: *True*
* **hidden**
    - Default: *False*
* **can_whisper**
    - Default: *True*
* **can_wtce**
    - Default: *True*
* **music_autoplay**
    - Default: *False*
* **can_spectate**
    - Default: *False*
* **can_getarea**
    - Default: *True*
* **can_cross_swords**
    - Default: *False*
* **can_scrum_debate**
    - Default: *False*
* **can_panic_talk_action**
    - Default: *False*
* **force_sneak**
    - Default: *False*
### Game Masters and above
* **can_cm**
    - Whether or not someone can become a Case Maker in this area.
    - Default: *False*
* **locking_allowed**
    - Whether or not a normal user is allowed to lock this area using /lock even without having the appropriate 'keys' (Look at /keys command for more info).
    - Default: *False*
* **iniswap_allowed**
    - Default: *False*
* **locked**
    - Default: *False*
* **muted**
    - Default: *False*
* **can_change_status**
    - Default: *False*
* **use_backgrounds_yaml**
    - If True, the area is only allowed to have backgrounds from the server's backgrounds.yaml configuration file.
    - If False, any custom BG name is allowed.
    - Default: *False*
* **dark**
    - Whether the area is dark or not. Note that you normally shouldn't set this perm directly, use the /lights command instead.
    - Default: *False*
* **old_muted**
    - The remembered mute status of the area by the Trial Minigames it will return to once the minigame is over.
    - Do not change this directly!
    - Default: *False*
* **recording**
    - When True, this area is currently recording testimony. This happens when you use /testimony_start or when the Witness Testimony WTCE is played by the CM.
    - Do not change this directly!
    - Default: *False*
### Mods Only
* Nothing here yet!