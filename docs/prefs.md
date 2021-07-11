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
    - If True, the Jukebox is in play for this area, which acts like a playlist of music to keep the area DJed automatically.
    - If False, music has to be chosen manually.
    - Default: *False*
* **non_int_pres_only**
    - If True, all preanimations will process the text immediately with no delay, reducing overall downtime between messages being displayed. Equivalent to forcing "immediate" checkbox to always be on. CMs and above bypass this restriction.
    - If False, preanimations will stop text processing unless "immediate" checkbox is ticked on by the user.
    - Default: *False*
* **blankposting_allowed**
    - If True, messages are not filtered for blankposting and can contain no message or just whitespace.
    - If False, no message is allowed to be a blankpost or composed solely of []' etc., each msg must at least have some text. CMs and above bypass this restriction.
    - Default: *True*
* **hide_clients**
    - If True, the number of clients present in the area is hidden from the client's area list for normal users. Note that this preference does not touch the ability to /getarea.
    - If False, number of clients is displayed.
    - Default: *False*
* **client_music**
    - If True, clients are allowed to load a custom music list on the client side.
    - If False, client-side music lists are not allowed.
    - Default: *True*
* **replace_music**
    - If True, this area's music list will completely overwrite the server or hub music list.
    - If False, the music lists will be stacked.
    - Default: *False*
* **can_dj**
    - If True, normal users can choose songs in this area.
    - If False, only CMs and above can choose songs.
    - Default: *True*
* **hidden**
    - If True, this area will be hidden from the client area lists.
    - If False, the area is visible in the client area lists.
    - Default: *False*
* **can_whisper**
    - If True, users are allowed to whisper to each other using an IC command /w \<msg> or /w \<id(,s)> \<msg>.
    - If False, only CMs and above can use the IC command.
    - Default: *True*
* **can_wtce**
    - If True, anyone can use Witness Testimony/Cross Examination/etc. judge buttons.
    - If False, only CMs and above may use the judge buttons.
    - Default: *True*
* **music_autoplay**
    - If True, the music will play automatically for any user that enters the area.
    - If False, the music will not play automatically, and the user would have to use /getmusic to play the area's track.
    - Default: *False*
* **can_spectate**
    - If True, anyone can switch to a Spectator, which is a character that doesn't permit you to speak and hides you from /getarea etc.
    - If False, only CMs and above are allowed to be a Spectator.
    - Default: *True*
* **can_getarea**
    - If True, anyone can use /getarea to see the players present in that particular area.
    - If False, only CMs and above are permitted to use /getarea.
    - Default: *True*
* **can_cross_swords**
    - If True, the cross-swords trial minigame can be used by players through IC or using /cs.
    - If False, cross-swords trial minigame is disabled.
    - Default: *False*
* **can_scrum_debate**
    - If True, the scrum debate trial minigame can be used by players through IC or using /cs.
    - If False, scrum debate trial minigame is disabled.
    - Default: *False*
* **can_panic_talk_action**
    - If True, the panic talk action trial minigame can be used by players through IC or using /pta.
    - If False, panic talk action trial minigame is disabled.
    - Default: *False*
* **force_sneak**
    - If True, all area OOC enter/leave messages are hidden.
    - If False, area OOC enter/leave messages are shown unless the player is hidden, sneaking, a spectator, etc.
    - Default: *False*
### Game Masters and above
* **can_cm**
    - Whether or not someone can become a Case Maker in this area.
    - Default: *False*
* **locking_allowed**
    - If True, normal users are allowed to lock this area using /lock.
    - If False, only CMs or above can lock the area, or the users with the appropriate 'keys' (Look at /keys command for more info).
    - Default: *False*
* **iniswap_allowed**
    - If True, users can change to custom char.ini's not recognized by the server's base content.
    - If False, only the server's base content characters and char.ini's may be used.
    - Default: *False*
* **locked**
    - Whether or not the area is locked. Used by /area_lock and /area_unlock.
    - Do not change this directly!
    - Default: *False*
* **muted**
    - Whether or not this area is muted. Used by /area_mute and /area_unmute.
    - Do not change this directly!
    - Default: *False*
* **can_change_status**
    - If True, this area's /status can be changed by normal users.
    - If False, this area's /status can only be changed by a CM or above.
    - Default: *False*
* **use_backgrounds_yaml**
    - If True, the area is only allowed to have backgrounds from the server's backgrounds.yaml configuration file.
    - If False, any custom BG name is allowed.
    - Default: *False*
* **dark**
    - Whether the area is dark or not. Used by the /lights command.
    - Do not change this directly!
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