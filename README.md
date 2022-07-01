# Jellyfin Config Backup (for Docker on Synology)
### **This script requires Python 3 and is designed for Synology DSM7** 
This script backs up a Jellyfin server configuration running in a Docker container on Synology DSM7. It is designed only to back up the configuration files in the event of corruption or deletion. It *is not* meant to backup your entire Jellyfin media folder. It has only been tested with the Python3.8 that's default for DSM7.

This works best if you have a static data folder for your Jellyfin container. Otherwise, you'll need to find out the hash for your data container. Additionally updating the container without a static data location will mean the hash will change, and you'll need to update your script. So it's always recommended to use a static data folder.

Credit to Gabisonfire for the original emby_backup from which this is based.

## How It Works

The script is pretty simple. It copies a slightly-customizable list of Jellyfin config files to a temporary directory, compresses the directory and saves that a .zip file in the destination folder. It then proceeds to delete old backups so that you have a customizable number remaining.

## Note
You must be logged into your Synology via SSH and have Sudo priviledges:

[How to access DSM via SSH](https://kb.synology.com/en-ca/DSM/tutorial/How_to_login_to_DSM_with_root_permission_via_SSH_Telnet "SSH Instructions for Synology DSM")

## Script Installation
This is a one-step command-line install. 

SSH into your Synology, switch to root and cut & paste the following: 
```
mkdir /volume1/.scripts/ && wget -O /volume1/.scripts/jellyfin_config_backup.py https://raw.githubusercontent.com/zang74/jellyfin_backup/master/jellyfin_config_backup.py && chmod +x /volume1/.scripts/jellyfin_config_backup.py
```
Setting it up to auto-run is performed within the DSM UI and instructions are in the wiki. 

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
- "-p", "--datapath",
  - Jellyfin's data container path. It defaults to /volume1/docker/jellyfin".
- "-d", "--destination",
  - Destination folder for backups. This is required.
- "-k", "--keep",
  - [Optional] Number of saved archives. If you are backing up metadata (see below) it's recommended to keep this number relatively low to avoid filling up your Synology with unnecessarily large files. The default is five.
- "-o", "--other",
  - [Optional] Additional file(s) to include. Can be repeated once per file.
- "-m", "--metadata" 
  - [Optional] This will also back up the Jellyfin metadata folder and is off by default. Use this option with caution, as including metadata can be both slow and will dramatically increase the size of the backup files. A better, faster option is storing metadata alongside media files in the form of .NFO and associated image files and doing regular incremental backups of your media file directories.
- "-l", "--logfile",
  - [Optional] /path/to/logfile. Change this if you want logs in a more easily accessible location, such as on one of the NAS' SMB shares. The default save location is /var/log/jellyfinbackup.log
- "-i", "--ignoredevicehash",
  - [Optional] Skip backing up the device.txt hash file. This might be useful if moving the config from one machine to another.
## Examples

```
python3 /volume1/.scripts/jellyfin_config_backup.py -p "/path/to/jellyfin/config/" -d "/path/to/backup/destination/" -o "/etc/additional_file" -o "/some/other/file" -m
python3 /volume1/.scripts/jellyfin_config_backup.py --datapath "/path/to/jellyfin/config/" --destination "/path/to/backup/destination/" --logfile "/path/to/network/share" --ignoredevicehash
python3 /volume1/.scripts/jellyfin_config_backup.py -d "/path/to/backup/destination/" -k 3
```
## Warning

I'm serious about avoiding a backup of the metadata directory. That's why it's off by default. On my own system, what is a 62MiB file easily balloons to almost 3GiB if I add metadata. If you're backing up even a couple of times a week, this can easily become a big problem, shrinking your filespace dramatically and repeatedly creating huge files of almost entirely the same data.
