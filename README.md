# jellyfin_config_backup.py
### **This Script Requires Python 3 and is designed for Synology DSM7** 
This script backs up a Jellyfin server configuration running in a Docker container on Synology DSM7. It is designed only to back up the configuration files in the event of corruption or deletion. It *is not* meant to backup your entire Jellyfin media folder.

This works best if you have a static data folder for your Jellyfin container. Otherwise, you'll need to find out the hash for your data container. Additionally updating the container without a static data location will mean the hash will change, and you'll need to update your script. So it's always recommended to use a static data folder.

Credit to Gabisonfire for the original emby_backup from which this is based.

## How It Works

The script is pretty simple. It copies files to a temporary directory, compresses the file and saves that file in the destination folder. It then proceeds to delete old backups so that you have a preset number remaining.

## NOTE
You must be logged into your Synology via SSH and have Sudo priveledges:

[How to access DSM via SSH](https://kb.synology.com/en-ca/DSM/tutorial/How_to_login_to_DSM_with_root_permission_via_SSH_Telnet "SSH Instructions for Synology DSM")

## Script Installation
This is a one-step command-line install. 
```
wget -O - https://raw.githubusercontent.com/zang74/jellyfin_backup/master/installscript.sh | bash
```
## GIT Installation
This requires the GIT package be installed on your DSM from the Synology Package Center. If you install in this method, make sure you remember where you put it; it'll be important for later. I recommend creating and installing to /volume1/.scripts/.
```
git clone git@github.com:zang74/jellyfin_config_backup.git
cd jellyfin_config_backup
chmod +x jellyfin_config_backup.py
./jellyfin_config_backup.py -h
```

## Usage

- "-v", "--version",
  - Gives the current version of the script.
- "-d", "--destination",
  - Destination folder for backups. This is required.
- "-k", "--keep",
  - Number of saved archives. If you are backing up metadata (see below) it's recommended to keep this number relatively low to avoid filling up your Synology with unnecessarily large files. The default is five.
- "-p", "--datapath",
  - Jellyfin's data container path. It defaults to /volume1/docker/jellyfin"
- "-o", "--other",
  - "Additional file(s) to include. Can be repeated once per file.
- "-m", "--metadata" 
  - This will also back up the Jellyfin metadata folder and is off by default. Use this option with caution, as including metadata can be both slow and will dramatically increase the size of the backup files. A better, faster option is storing metadata with the files in the form of .NFO and associated image files.
- "-l", "--logfile",
  - /path/to/logfile. Optionally change this if you want logs in a more easily accessible location, such as on one of the NAS' SMB shares. The default save location is /var/log/jellyfinbackup.log
- "-i", "--ignoredevicehash",
  - Skip backing up the device.txt hash file. This might be useful if moving the config from one machine to another.
## Examples

```
python3 /volume1/.scripts/jellyfin_config_backup.py -d "/path/to/jellyfin/data/" -o "/etc/additional_file" -o "/some/other/file" -m
python3 /volume1/.scripts/jellyfin_config_backup.py -d "/path/to/jellyfin/data/" -k 3

```
