# emby_backup.py
### **Requires python 3** 
Python script to backup Emby media server.

## Usage
```
git clone git@github.com:Gabisonfire/emby_backup.git
cd emby_backup
chmod +x emby_backup.py
pip install justlog
./emby_backup.py -h
```

- "-d", "--destination",
  - Destination folder for backup, required.
- "-k", "--keep",
  - Days to keep archives. default=5
- "-s", "--systempath",
  - Emby's system path, default="/var/lib/emby"
- "-o", "--other",
  - Additional file to include. Can be repeated.
- "-c", "--oncompletion",
  - Command to execute on completion.

## Examples

```
./emby_backup.py -d "~/emby-backups" -o "/etc/additional_file" -o "/some/other/file"
./emby_backup.py -d "~/emby-backups" -k 30
./emby_backup.py -d "~/emby-backups" -c "echo 'Backup Completed.'"
```
