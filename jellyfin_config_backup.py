#!/usr/bin/env python3
import argparse
import shutil
import os
import datetime
import zipfile
import glob
from subprocess import run
import logging
from logging.handlers import RotatingFileHandler

version = "1.0"

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--version", dest="getversion", help="Gives the current version of the script.", default=False, action='store_true')
parser.add_argument("-p", "--datapath", dest="datapath",  help="Jellyfin's data container path.", default="/volume1/docker/jellyfin")
parser.add_argument("-d", "--destination", dest="backupdest", help="Destination folder for backups.")
parser.add_argument("-k", "--keep", dest="keepbackups", help="Number of saved archives. If you are backing up metadata (see below) it's recommended to keep this number relatively low to avoid filling up your Synology with unnecessarily large files. The default is five.", type=int, default=5)
parser.add_argument("-o", "--optionalfile",  dest="optionalfile", help="Additional file(s) to include. Can be repeated once per file.", action='append')
parser.add_argument("-m", "--metadata", dest="metadata", help="This will also back up the Jellyfin metadata folder and is off by default. Use this option with caution, as including metadata can be both slow and will dramatically increase the size of the backup files. A better, faster option is storing metadata alongside media files in the form of .NFO and associated image files and doing regular incremental backups of your media file directories.", default=False, action='store_true')
parser.add_argument("-l", "--logfile", dest="optlogfileloc", help="/path/to/logfile/directory. Optionally change this if you want logs in a more easily accessible location, such as on one of the NAS' SMB shares. File will be named jellyfin_config_backup.log. The default save location is within /var/log/")
parser.add_argument("-i", "--ignoredevicehash", dest="devicehash", help="Skip backing up the device.txt hash file. This might be useful if moving the config from one machine to another.", default=True, action='store_false')

args = parser.parse_args()

showversion = args.getversion
backupdest = args.backupdest
datapath = args.datapath
optlogfileloc = args.optlogfileloc
metadata = args.metadata
keepbackups = args.keepbackups
devicehash = args.devicehash
optionalfiles = args.optionalfile


# Show version number and quit

if showversion:
	print (f"Jellyfin Config Backup v{version} by Zang74\nhttps://github.com/zang74/jellyfin_backup")
	exit()

if not backupdest:
	print ("A backup destination is a required.")
	exit()
# Folders to back up

folders = ['config', 'plugins', 'data/subtitles', 'data/collections', 'data/playlists']

if metadata:
	folders.append('metadata')

# Files to back up

files = ['data/jellyfin.db', 'data/library.db', 'data/splashscreen.png']

if optionalfiles:
  for file in optionalfiles:
    files.append(file)

if devicehash:
	files.append("data/device.txt")

scriptpath = os.path.abspath(os.path.dirname(__file__))
tempdir = scriptpath + "/jfcfg_bkp_temp"
defaultlogloc = "/var/log/jellyfin_config_backup.log"

#Set Up Logger

## Check if logfile location is legit
if optlogfileloc and os.path.isdir(os.path.dirname(optlogfileloc)):
  logfileloc = optlogfileloc
else: 
  logfileloc = defaultlogloc
	
log_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
log_handler = RotatingFileHandler(logfileloc, mode='a', maxBytes=3145728, backupCount=2, encoding=None, delay=0)
log_handler.setFormatter(log_format)
log_handler.setLevel(logging.INFO)
thislog = logging.getLogger('root')
thislog.setLevel(logging.INFO)
thislog.addHandler(log_handler)


thislog.info(f"Logs to be saved to {logfileloc}")

def intro():
  thislog.info(f"---- Jellyfin backup script version {version} ----")

def preflight_check():
  if os.path.isdir(tempdir):
    thislog.info(f"{tempdir} was not cleaned last run, deleting.")
    shutil.rmtree(f'{tempdir}')
    
  for file in files:
    if os.path.isfile(f"{datapath}/{file}"):    
      thislog.info(f"{datapath}/{file} exists.")
    else:
      thislog.warning(f"{datapath}/{file} does not exist.")
  for folder in folders:
    if os.path.isdir(f"{datapath}/{folder}"):
      thislog.info(f"{datapath}/{folder} exists.")
    else:
      thislog.warning(f"{datapath}/{folder} does not exist.")

def zipdir(path, ziph):
  for root, dirs, files in os.walk(path):
    for file in files:
      path = os.path.join(root, file)
      name_dest = os.path.relpath(os.path.join(root, file), 'jf_bkp_temp')            
      ziph.write(path, f"jellyfin/{name_dest}")

def build_archive():
  thislog.info("Creating archive...")
  os.mkdir(tempdir)
  for file in files:
    if not os.path.isfile(f"{datapath}/{file}"):
      continue
    os.makedirs(os.path.dirname(f"{tempdir}/{file}"), exist_ok=True)
    shutil.copy2(f"{datapath}/{file}", f"{tempdir}/{file}")
  for folder in folders:
    if not os.path.isdir(f"{datapath}/{folder}"):
      continue
    shutil.copytree(f"{datapath}/{folder}", f"{tempdir}/{folder}")

  now = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
  zip = zipfile.ZipFile(f"{backupdest}/jellyfin_config_backup_{now}.zip", 'w', zipfile.ZIP_DEFLATED)
  zipdir(tempdir, zip)
  zip.close()
  thislog.info(f"Archive created at {backupdest}/jellyfin_config_backup_{now}.zip")
  thislog.info("Cleaning up...")
  try:
    shutil.rmtree(tempdir)
  except Exception as error:
    thislog.error(str(error))

def sizeof(size, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(size) < 1024.0:
            return f"{size:3.1f}{unit}{suffix}"
        size /= 1024.0
    return f"{size:.1f}Yi{suffix}"

def rotate():
  thislog.info(f"Checking backups for rotation.({keepbackups} iterations to be kept.)")
  while len(glob.glob(f"{backupdest}/jellyfin_config_backup_*.zip")) > keepbackups:
    totalbackups = glob.glob(f"{backupdest}/jellyfin_config_backup_*.zip")
    todelete = min(totalbackups, key=os.path.getctime)
    try:  
      os.remove(todelete)
      thislog.info(f"{todelete} deleted.")
    except OSError as error:
      thislog.error(str(error))
	
  backupsleft = glob.glob(f"{backupdest}/jellyfin_config_backup_*.zip")
  numberofbackups = len(backupsleft)
  
  if numberofbackups == 1:
  	suffx = ""
  else:
  	suffx = "s"
  	
  dirsize = 0
  for thisone in backupsleft:
  	dirsize = dirsize + os.path.getsize(thisone)
  
  totalsize = sizeof(dirsize)
  thislog.info(f"{totalsize} of Jellyfin config backups in {numberofbackups} file{suffx}")
  
def endall():
  logging.shutdown()
  
  if optlogfileloc:
    os.chmod(logfileloc, 0o664)

intro()
preflight_check()
build_archive()
rotate()
endall()
