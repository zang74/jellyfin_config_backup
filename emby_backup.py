#!/usr/bin/env python3
import argparse
import shutil
import os
import datetime
import zipfile
import glob
from subprocess import run

from justlog import justlog, settings
from justlog.classes import Severity, Output, Format

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--destination", help="Destination folder for backup", required=True)
parser.add_argument("-k", "--keep", help="Days to keep archives.", type=int, default=5)
parser.add_argument("-s", "--systempath", help="Emby's system path", default="/var/lib/emby")
parser.add_argument("-o", "--other", help="Additional file to include. Can be repeated", action='append')
parser.add_argument("-c", "--oncompletion", help="Command to execute on completion.")

args = parser.parse_args()

folders = ['config', 'plugins', 'data/collections', 'data/playlists']
files = ['data/displaypreferences.db', 'data/users.db', 'data/library.db']

SYSPATH = args.systempath
TMP_DIR = "emby_bkp_temp"

VERSION = "0.1"

# Setup logger
logger = justlog.Logger(settings.Settings())
logger.settings.colorized_logs = True
logger.settings.log_output = [Output.STDOUT]
logger.settings.log_format = Format.TEXT
logger.settings.update_field("timestamp", "$TIMESTAMP")
logger.settings.update_field("level", "$CURRENT_LOG_LEVEL")
logger.settings.string_format = "[ $timestamp ] :: $CURRENT_LOG_LEVEL :: $message"

def intro():
  logger.info(f"Emby backup script version {VERSION}")
  logger.info(f"System date is {datetime.datetime.now()}")

def preflight_check():
  if os.path.isdir(TMP_DIR):
    logger.error(f"{TMP_DIR} was not cleaned last run, please remove manually.")
    exit(1)
  for file in files:
    if os.path.isfile(f"{SYSPATH}/{file}"):    
      logger.info(f"{SYSPATH}/{file} exists.")
    else:
      logger.warning(f"{SYSPATH}/{file} does not exist.")
  for folder in folders:
    if os.path.isdir(f"{SYSPATH}/{folder}"):
      logger.info(f"{SYSPATH}/{folder} exists.")
    else:
      logger.warning(f"{SYSPATH}/{folder} does not exist.")

def zipdir(path, ziph):
  for root, dirs, files in os.walk(path):
        for file in files:
            path = os.path.join(root, file)
            name_dest = os.path.relpath(os.path.join(root, file), 'emby_bkp_temp')            
            ziph.write(path, f"emby/{name_dest}")

def build_archive():
  logger.info("Creating archive...")
  os.mkdir(TMP_DIR)
  for file in files:
    if not os.path.isfile(f"{SYSPATH}/{file}"):
      continue
    os.makedirs(os.path.dirname(f"{TMP_DIR}/{file}"), exist_ok=True)
    shutil.copy2(f"{SYSPATH}/{file}", f"{TMP_DIR}/{file}")
  for folder in folders:
    if not os.path.isdir(f"{SYSPATH}/{folder}"):
      continue
    shutil.copytree(f"{SYSPATH}/{folder}", f"{TMP_DIR}/{folder}")
  if args.other:
    for file in args.other:
      if not os.path.isfile(file):
        continue
      os.makedirs(os.path.dirname(f"{TMP_DIR}/{file}"), exist_ok=True)
      shutil.copy2(file, f"{TMP_DIR}/{file}")
  now = datetime.datetime.now().strftime("%Y_%m_%d")
  zip = zipfile.ZipFile(f"{args.destination}/emby_backup_{now}.zip", 'w', zipfile.ZIP_DEFLATED)
  zipdir(TMP_DIR, zip)
  zip.close()
  logger.info(f"Archive created at {args.destination}/emby_backup_{now}.zip")
  logger.info("Cleaning up...")
  try:
    shutil.rmtree(TMP_DIR)
  except Exception as e:
    logger.error(str(e))

def rotate():
  logger.info(f"Checking backups for rotation.({args.keep} days)")
  for bkp in glob.glob(f"{args.destination}/emby_backup*.zip"):
    file = os.path.basename(bkp)
    timestamp = datetime.datetime.strptime(file, "emby_backup_%Y_%m_%d.zip")
    now = datetime.datetime.now()
    if (now - timestamp).days > args.keep:
      logger.info(f"Deleting {bkp}, {(now - timestamp).days} days old.")
      try:
        os.remove(bkp)
      except Exception as e:
        logger.error(str(e))

def exec(cmd):
  try:
    pipe = run(cmd.split())
  except Exception as e:
    logger.error(str(e))

def success(cmd):
  logger.info("Executing success command")
  exec(cmd)

intro()
preflight_check()
build_archive()
rotate()
if args.oncompletion:
  success(args.oncompletion)
