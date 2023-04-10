# Source Files
The main code is found in sync_folder.py
Helper functions for md5 and other calculations can be found in helper.py
if a file record of past syncs exists it will be in this directory in file_record.txt

## The Process
The following will happen when the code is run:
1. argparse will parse the arguments.
2. Confirm that the source and replica directory exist. If a directory  does not exist - it will create it.
3. Confirm that the source and replica directory exist. If the source does not exist - it will terminat. If the replica does not exist - it will create it.
4. Convert interval from ##d##h##m##s into seconds.
5. Start a new thread that will run the infinit loop. This thread is defined a daemon so that is closes when the main program is closed.
    1. In the main thread a function called "input thread" is called. This is an infnit loop waiting for the user to enter the word "quit" - this will allow for safe exiting of the program by waiting for the sync loop to finish before exiting, so that copying processes dont get inturupted in the middle.
6. In the loop thread:  
    1. File record is loaded from a file - this file contains pairs of files, 1 from source and 1 from replica, where the source file was already copied into the replica file in the past, their size and modification time. This will save us from running md5 on unecesary files later on.
    2. An infinit loop is started that sleeps every "interval" amount of time. The sleeping takes into account the time it took for the sync process, i.e. if the sync took 2 seconds and the interval was 5 secounds it will only sleep for 3 seconds.
    3. The loop will stop when a variable is changed on the main thread. This happens once the word "quit" is entered.
    4. The sync action in the loop will do the following:
        1. collect lists of all files and directories in source and replica directories. These will be used as the files that need to be copied over from source, or deleted from replcia.
        2. Check if the replica directory is empty. If so, copy over all the files from the source one by one, while recording the name, size and modification time in the file record variable.
        3. If the replica directory is not empty:
            1. Go over the file record and check if the pair of files still exists, including size and modification time, in the source and replica directories respectively. If so - we can conclude that these are the same files have already been copied through and left unchanged, and we can remove the from the file lists to be copied. These will save us time doing md5 on these files (which is especially relavent if they are big).
            *Note - technically if someone switches a file with a different file and manipulates the metadate to match this can be a problem. If security needs to be taken into account to this degree this needs to be removed.
            2. md5 all the files that still exist in the source and replica directory lists
                1. For replica files we also delete files that are not existant in the source.
            3. Go over all files in source and search for equivalent md5 hashes files in the replica.
                1. If they are not found - copy them over and document them in file record.
                2. If the md5 hash from source is found in replica it means the file name was changed (as we know the contents are the same and otherwise it would have been removed from the list earlier). In this case we move the file to the correct place and name, creating any subdirectories needed in the replica.
            4. Delete all unecessary old directories from replica - these directories would be empty directories that had files in them but they were moved/deleted in this sync action - leaving them empty. If the directories don't exist in the source now then they are deleted from replica.
    5. After the sync action is taken the file record variable gets put into the file record file.


