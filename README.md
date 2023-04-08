# Synch folders
This program is intended to copy a source directory into a replica directory.
This will be done periodically.
A log file is saved and documents what is happening.
A file named file_record.txt will be created keeping track of the files that were already synched in the past.

### Note:
Do not use files with ";" or "^^^" in their names - this will conflict with the format used in file_record.txt

## Usage
python3 src/sync_folder.py -s SOURCE_DIR -r REPLICA_DIR -i INTERVAL -l LOG_DIR

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE_DIR, --source-dir SOURCE_DIR
                        Source directory to be synced.
  -r REPLICA_DIR, --replica-dir REPLICA_DIR
                        Replica directory to be synced to.
  -i INTERVAL, --interval INTERVAL
                        Synchronization interval for syncing. Format is ##d##h##m##s
  -l LOG_DIR, --log-dir LOG_DIR
                        Location of log file to be saved.

During the running of the program enter the word "quit" to safely exit. This will finish the current sync (if one is in progress) and exit at the end of it.

## Tested using:
- Linux Mint 20 x86_64
- Python 3.8.10

### Note:
- This was not tested on Windows machines. There are no specific Linux references that I can think of, so it may work on Windows, but I was not able to confirm this.

