# jellyfinbackup.py
### **Requires Python 3** 
This script backs up a Jellyfin server configuration running in a Docker container on Synology DSM7. It is designed only to back up the configuration files in the event of corruption or deletion. It *is not* meant to backup your entire Jellyfin media folder.

This works best if you have a static data folder for your Jellyfin container. Otherwise, you'll need to find out the hash for your data container. Additionally updating the container without a static data location will mean the hash will change, and you'll need to update your script. So it's always recommended to use a static data folder.

Credit to Gabisonfire for the original emby_backup from which this is based.

## NOTE
You must be logged into your Synology via SSH and have Sudo priveledges:

[How to access DSM via SSH](https://kb.synology.com/en-ca/DSM/tutorial/How_to_login_to_DSM_with_root_permission_via_SSH_Telnet "SSH Instructions for Synology DSM")

## Script installation
This is a one-step command-line install. 
```
wget -O - https://raw.githubusercontent.com/zang74/jellyfin_backup/master/installscript.sh | bash
```
## GIT installation
This requires the GIT package be installed on your DSM from the Synology Package Center. If you install in this method, make sure you remember where you put it; it'll be important for later.
```
git clone git@github.com:zang74/jellyfin_backup.git
cd jellyfin_backup
chmod +x jellyfinbackup.py
./jellyfinbackup.py -h
```

## USAGE

- "-v", "--version",
  - Gives the current version of the script
- "-d", "--destination",
  - Destination folder for backup, required.
- "-k", "--keep",
  - Days to keep archives. If you are backing up metadata (see below) it's recommended to keep this number relatively low to avoid filling up your Synology with unnecessarily large files default=5
- "-s", "--systempath",
  - The Jellyfin data container path, default="/var/lib/emby"
- "-o", "--other",
  - Additional file to include. Can be repeated.
- "-c", "--oncompletion",
  - Command to execute on completion.
- "-m", "--metadata" 
  - This will also back up the Jellyfin metadata folder. Use this option with caution, as including metadata can be both slow and will dramatically increase the size of the backup files. A better, faster option is storing metadata with the files in the form of .NFO and associated image files.
## Examples

```
python3 /volume1/.scripts/jellyfinbackup.py -d "/path/to/jellyfin/data/" -o "/etc/additional_file" -o "/some/other/file" -m
python3 /volume1/.scripts/jellyfinbackup.py -d "/path/to/jellyfin/data/" -k 5
python3 /volume1/.scripts/jellyfinbackup.py -d "/path/to/jellyfin/data/" -c "echo 'Backup Completed.'"
```
