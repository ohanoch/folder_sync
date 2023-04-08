#Synch folders
This program is intended to copy a source directory into a replica directory.
This will be done periodically.
A log file is saved and documents what is happening.

##Usage
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

##Tested using:
- Linux Mint 20 x86_64
- Python 3.8.10

###Note:
- This was not tested on Windows machines. There are no specific Linux references that I can think of, so it may work on Windows, but I was not able to confirm this.

##Possible improvements:
- After running the code it will always have "file_record" empty in the first loop. This means that for files that are identical in source and replica it will not know that they were already copied over and will attempt to do it anyways, causing it to md5 them and then perform a "move" action for the file in the replica to the same place it already is at.
	- This can be fixed by logging the file_record in an external file and loading it back in when starting the code. It requires using json, or other formats.


