#!/usr/bin/env python3
import argparse
import shutil
import os
import getpass
import datetime
import zipfile
import glob
from subprocess import run
import logging
from logging.handlers import RotatingFileHandler

version = "1.1b"

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--version", dest="getversion", help="Gives the current version of the script.", default=False, action='store_true')
parser.add_argument("-c", "--configpath", dest="configpath", help="Jellyfin's data container config path.", default="/volume1/docker/jellyfin/config")
parser.add_argument("-d", "--destination", dest="backupdest", help="Destination folder for backups.")
parser.add_argument("-k", "--keep", dest="keepbackups", help="Number of saved archives. If you are backing up metadata (see below) it's recommended to keep this number relatively low to avoid filling up your Synology with unnecessarily large files. The default is five.", type=int, default=5)
parser.add_argument("-o", "--optionalfile",	dest="optionalfile", help="Additional file(s) to include. Can be repeated per file.", action='append')
parser.add_argument("-m", "--metadata", dest="metadata", help="This will also back up the Jellyfin metadata folder and is off by default. Use this option with caution, as including metadata can be both slow and will dramatically increase the size of the backup files. A better, faster option is storing metadata alongside media files in the form of .NFO and associated image files and doing regular incremental backups of your media file directories.", default=False, action='store_true')
parser.add_argument("-l", "--logfile", dest="optlogfileloc", help="/path/to/logfile/directory. Optionally change this if you want logs in a more easily accessible location, such as on one of the NAS' SMB shares. File will be named jellyfin_config_backup.log. The default save location is where the script is located.")
parser.add_argument("-i", "--ignoredevicehash", dest="devicehash", help="Skip backing up the device.txt hash file. This might be useful if moving the config from one machine to another.", default=True, action='store_false')

args = parser.parse_args()

showversion = args.getversion
backupdest = args.backupdest
configpath = args.configpath
optlogfileloc = args.optlogfileloc
metadata = args.metadata
keepbackups = args.keepbackups
devicehash = args.devicehash
optionalfiles = args.optionalfile
scriptuser = getpass.getuser()
scriptuserpath = "/var/services/homes/" + scriptuser
skipahead = ""
# Show version number and quit

if showversion:
	print (f"Jellyfin Config Backup v{version} by Zang74\nhttps://github.com/zang74/jellyfin_backup")
	exit()

	
folders = ['config', 'plugins', 'data/subtitles', 'data/collections', 'data/playlists']

if metadata:
	folders.append('metadata')

# Files to back up

files = ['data/jellyfin.db', 'data/library.db', 'data/splashscreen.png']

# Collect optional files
if optionalfiles:
	for file in optionalfiles:
		files.append(file)

# Add devicehash (on by default)
if devicehash:
	files.append("data/device.txt")

scriptpath = os.path.abspath(os.path.dirname(__file__))
tempdir = scriptpath + "/jfcfg_bkp_temp"
defaultlogloc = scriptpath + "/jellyfin_config_backup.log"

# Logging
def trimpaths(pathtotrim):
	if pathtotrim.endswith('/'):
		return pathtotrim[:-1]
	else:
		return pathtotrim

# Trim end slash if it exists, just for cleaner paths.
backupdest = trimpaths(backupdest)
configpath = trimpaths(configpath)
optlogfileloc = trimpaths(optlogfileloc)
	
# Check if logfile argument exists
if optlogfileloc:
	# Check if the optional log save location is writeable
	if not os.access(optlogfileloc, os.W_OK):
		print(f"You don't have write permissions to save the log file to '{optlogfileloc}' or the directory doesn't exist. Exiting.")
		exit()
	else:
		logfileloc = optlogfileloc + "/jellyfin_config_backup.log"
else:
	#save log to default location instead
	logfileloc = defaultlogloc

# Set up Logger
log_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
log_handler = RotatingFileHandler(logfileloc, mode='a', maxBytes=3145728, backupCount=2, encoding=None, delay=0)
log_handler.setFormatter(log_format)
log_handler.setLevel(logging.INFO)
thislog = logging.getLogger(scriptuser)
thislog.setLevel(logging.INFO)
thislog.addHandler(log_handler)

thislog.info(f"===== Jellyfin backup script version {version} =====")
thislog.info(f"Logs to be saved to {logfileloc}")


# Make minimum 1 retained backup so user doesn't create one and then immediately delete it.
def howmanybackups(keepbackups):
	if keepbackups == 0:
		thislog.warning (f"Number of retained backups cannot be zero. Defaulting to one.")
		return 1
	else:
		return keepbackups


		
def introchecks():

	# kick user out if it's a non-standard one without a home directory
	if not os.path.isdir(scriptuserpath):
		thislog.error("No user home directory exists. Please use an active user with a home directory.")
		logging.shutdown()
		exit()

	# We *need* a backup destination
	if not backupdest:
		thislog.error ("A backup destination is a required.")
		logging.shutdown()
		exit()

	# Is backup destination writeable?
	if os.access(backupdest, os.W_OK) is False:
		thislog.error (f"You don't have the proper permissions to write a back up to {backupdest}")
		logging.shutdown()
		exit()

	# Is config location readable?
	if os.access(configpath, os.R_OK) is False:
		thislog.error (f"You don't have the proper permissions to read {configpath}")
		logging.shutdown()
		exit()



def preflight_check():
	# Check if previous temporary directory wasn't cleared out
	if os.path.isdir(tempdir):
		thislog.info(f"{tempdir} was not cleaned last run, deleting.")
		shutil.rmtree(f'{tempdir}')

	# Check for individual files to backup
	for file in files:
		if os.path.isfile(f"{configpath}/{file}"):		
			thislog.info(f"{configpath}/{file} exists.")
		else:
			thislog.warning(f"{configpath}/{file} does not exist.")

	# Check for individual directories to backup
	for folder in folders:
		if os.path.isdir(f"{configpath}/{folder}"):
			thislog.info(f"{configpath}/{folder} exists.")
		else:
			thislog.warning(f"{configpath}/{folder} does not exist.")

def zipdir(path, ziph):

	# Zip files up
	for root, dirs, files in os.walk(path):
		for file in files:
			path = os.path.join(root, file)
			name_dest = os.path.relpath(os.path.join(root, file), 'jfcfg_bkp_temp')						
			ziph.write(path, f"jellyfin/{name_dest}")

def build_archive():

	# Collect files in temporary director for zipping 
	thislog.info("Creating archive...")
	os.mkdir(tempdir)
	for file in files:
		if not os.path.isfile(f"{configpath}/{file}"):
			continue
		os.makedirs(os.path.dirname(f"{tempdir}/{file}"), exist_ok=True)
		shutil.copy2(f"{configpath}/{file}", f"{tempdir}/{file}")
	for folder in folders:
		if not os.path.isdir(f"{configpath}/{folder}"):
			continue
		shutil.copytree(f"{configpath}/{folder}", f"{tempdir}/{folder}")

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
	# Summarize bit size into readable abbreviations
	for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
		if abs(size) < 1024.0:
			return f"{size:3.1f}{unit}{suffix}"
		size /= 1024.0
	return f"{size:.1f}Yi{suffix}"

def rotate():
	keeps = howmanybackups(keepbackups)
	#rotate backups
	thislog.info(f"Checking backups for rotation.({keeps} iterations to be kept.)")
	while len(glob.glob(f"{backupdest}/jellyfin_config_backup_*.zip")) > keeps:
		totalbackups = glob.glob(f"{backupdest}/jellyfin_config_backup_*.zip")
		todelete = min(totalbackups, key=os.path.getctime)
		try:	
			# Delete older backups beyond specified number
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
	# Collect total number and size of existing backups
	for thisone in backupsleft:
		dirsize = dirsize + os.path.getsize(thisone)
	
	totalsize = sizeof(dirsize)
	thislog.info(f"{totalsize} of Jellyfin config backups in {numberofbackups} file{suffx}")
	
def endall():
	thislog.info("===== Done =====\n\n")
	# Shutdown logging
	logging.shutdown()
	
	# Change log permissions slightly.
	if optlogfileloc:
		os.chmod(logfileloc, 0o664)

introchecks()
preflight_check()
build_archive()
rotate()
endall()
