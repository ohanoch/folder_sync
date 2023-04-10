import argparse
import time
import datetime

from threading import Thread
import multiprocessing

import sys
import os
import shutil
import glob
import traceback
import signal

import logging

from  helper import *

"""
This class is used for items in the file record
"""
class FileMeta:
    def __init__(self, fullpath, mod_time=None, size=None, md5=None):
        self.fullpath = fullpath
        self.mod_time = mod_time
        self.size = size
        self.md5=md5

"""
This function runs in the background in an infinit loop waiting for the word "quit".
When "quit" is entered it checks if the loop is in its sleeping stage and exists accordingly to dignal immidiate or not immidiate exiting of the sync loop.
In the end it changes stop_flag so the sync loop is exited.
"""
def input_thread(stop_flag, is_sleeping):
    while(not stop_flag.value):
        try:
            key_input = input()
            if key_input == "quit":
                if is_sleeping.value == True:
                    logging.info("Closing program after quit command.")
                    stop_flag.value = True
                    return 0
                else:
                    logging.info("finishing current synchronization loop. Program will exit once this is complete")
                    stop_flag.value = True
                    return 1
        except Exception as e:
            #logging.error("ERROR: something went wrong in input_thread: " + str(e))
            sys.stdout.flush()
            sys.stdin.flush()

"""
Takes in the log directory inputted by the user.
Creates log directory if it does not exist yet
Creates log file in the log directory with the name YYmmdd_HHMMSS.log using the current time.
"""
def setup_logging(input_log_dir):
    #check if log file location exists - if not, create it
    log_dir = None
    if input_log_dir[-1] == "/":
        log_dir = input_log_dir[:-1]
    else:
        log_dir = input_log_dir

    if not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(\
            level = logging.DEBUG,\
            handlers = [
                logging.FileHandler(os.path.join(input_log_dir, time.strftime("%Y%m%d_%H%M%S") + '.log')),
                logging.StreamHandler()
            ],
            format='%(asctime)s - %(levelname)s - %(message)s',\
            datefmt='%d-%b-%y %H:%M:%S',\
            force=True)
    logging.info("Log file created: " + os.path.join(input_log_dir, time.strftime("%Y%m%d_%H%M%S") + '.log')) 

"""
Takes source file list, source directory name, replica directory name and file record.
Copies everything from source to replica while populating the file record,
return updated file record.
"""
def replica_dir_empty(source_files, source_dir, replica_dir, file_record):
    for source_f in source_files:
        if os.path.isdir(source_f):
            continue
        f_relative_fullpath = source_f.replace(clean_dir_name(source_dir) + os.sep,"")
        replica_f_dir = os.path.join(replica_dir, os.sep.join(f_relative_fullpath.split(os.sep)[:-1]))
        if not os.path.isdir(replica_f_dir):
                os.makedirs(replica_f_dir, exist_ok=True)
        replica_f_fullpath = os.path.join(replica_dir, f_relative_fullpath)

        logging.info("Copying file from source to replica: " + f_relative_fullpath)
        shutil.copyfile(source_f, replica_f_fullpath)
        file_record.append((\
                FileMeta(fullpath=source_f, mod_time=os.path.getmtime(source_f), size=os.path.getsize(source_f), md5="unknown"),\
                FileMeta(fullpath=replica_f_fullpath, mod_time=os.path.getmtime(replica_f_fullpath), size=os.path.getsize(replica_f_fullpath), md5="unknown")))

    return file_record

"""
takes in the list of files in the source and in the replica.
For each file in the file record check if it is in the source and if the coresponding file in the replica has the same name, modification time, and size as in the file record.
    - if so, remove the file from the source and replica lists (as it does not need to be copied over)
    - if not - remove the file from the record
return updated file record  lists with only files that have not been synced yet.
"""
def compare_with_file_record(source_files, replica_files, file_record):
    for file_pair in file_record:
        if file_pair[0].fullpath in source_files and \
                file_pair[0].mod_time == os.path.getmtime(file_pair[0].fullpath) and\
                file_pair[0].size == os.path.getsize(file_pair[0].fullpath) and\
                file_pair[1].fullpath in replica_files and \
                file_pair[1].mod_time == os.path.getmtime(file_pair[1].fullpath) and\
                file_pair[1].size == os.path.getsize(file_pair[1].fullpath):
                    source_files.remove(file_pair[0].fullpath)
                    replica_files.remove(file_pair[1].fullpath)
        else:
            file_record.remove(file_pair)

    return source_files, replica_files, file_record

"""
take source files/directories and replica files/directories lists.
All files in the lists.
Delete files in replica that do not have correpondence in source
return the md5s and the FileMetas of the files
"""
def md5_source_replica(source_files, replica_files):
    source_meta = []
    source_md5 = []
    for f_name in source_files:
        if os.path.isdir(f_name):
            continue
        f_md5 = md5(f_name)
        source_meta.append(FileMeta(fullpath=f_name, mod_time=os.path.getmtime(f_name), size=os.path.getsize(f_name), md5=f_md5))
        source_md5.append(f_md5)
    
    logging.info("Hashing replica files with md5 and deleting unmatched files...") 
    replica_meta = []
    replica_md5 = []
    for f_name in replica_files:
        if os.path.isdir(f_name):
            continue
        f_md5 = md5(f_name)
        #Delete files that don't exist in source
        if f_md5 not in source_md5:
            logging.info("Deleting file from replica directory: " + f_name)
            os.remove(f_name)
            replica_files.remove(f_name)
        else:
            replica_meta.append(FileMeta(fullpath=f_name, mod_time=os.path.getmtime(f_name), size=os.path.getsize(f_name), md5=f_md5))
            replica_md5.append(f_md5)
    
    return source_meta, source_md5, replica_meta, replica_md5

"""
takes in all details of files from source and replica that do not have corresponding files.
Copies files that do not have a matching md5
Moves and renames files that do have corresponding md5
Updates file list of copied and moved files and returns it.
"""
def copy_and_move_files(source_dir, replica_dir, source_meta, source_md5, replica_meta, replica_md5, file_record):
    for source_f in source_meta:
        f_relative_fullpath = source_f.fullpath.replace(clean_dir_name(source_dir) + os.sep,"")
        replica_f_dir = os.path.join(replica_dir, os.sep.join(f_relative_fullpath.split(os.sep)[:-1]))
        if not os.path.isdir(replica_f_dir):
                os.makedirs(replica_f_dir, exist_ok=True)
        replica_f_new_fullpath = os.path.join(replica_dir, f_relative_fullpath)

        if source_f.md5 not in replica_md5:
            
            logging.info("Copying file from source to replica: " + f_relative_fullpath)
            shutil.copyfile(source_f.fullpath, replica_f_new_fullpath)
            file_record.append((source_f,\
                    FileMeta(fullpath=replica_f_new_fullpath, mod_time=os.path.getmtime(replica_f_new_fullpath), size=os.path.getsize(replica_f_new_fullpath), md5=source_f.md5)))
        #For items in source that are in replica - move/rename the file in replica to the same as in source
        else: 
            for replica_f in replica_meta:
                if replica_f.md5 == source_f.md5:
                    logging.info("Moving file in replica from: " + replica_f.fullpath + " to: " + replica_f_new_fullpath)
                    shutil.move(replica_f.fullpath, replica_f_new_fullpath)
                    file_record.append((source_f, replica_f))
                    break

    return file_record

"""
Takes in source directory and replica files/directories list
If a directory is detected in replica and not in source - delete it
"""
def delete_empty_directories(source_dir, replica_dir, replica_files):
    for f_name in replica_files:
        if os.path.isdir(f_name):
            if not os.path.isdir(os.path.join(source_dir, f_name.replace(replica_dir + os.sep, ""))):
                logging.info("Deleting directory from replica that does not exist in source: " + f_name)
                shutil.rmtree(f_name)

"""
takes source directory, replica directory, and file record containing pairs of previously copied files in the shape of FileMeta.
If files are not in file_record it will md5 the files to check if they have been moved or renaimed.
If file is not found it will be copied.
If file is found but with a different name/location it will be moved and renamed.
"""
def sync_action(source_dir, replica_dir, file_record=[]):
    logging.info("Starting sync")

# collect lists of all files and directories in source and replica directories. These will be used as the files that need to be copied over from source, or deleted from replcia.
    source_files = glob.glob(source_dir + '/**/*', recursive=True)
    replica_files = glob.glob(replica_dir + '/**/*', recursive=True)

# Check if the replica directory is empty. If so, copy over all the files from the source one by one, while recording the name, size and modification time in the file record variable.
    if len(os.listdir(replica_dir)) == 0:
        logging.info("replica directory is empty, copying over entire source directory")
        file_record = replica_dir_empty(source_files,source_dir, replica_dir, file_record)

    else:
        # Go over the file record and check if the pair of files still exists, including size and modification time, in the source and replica directories respectively. If so - we can conclude that these are the same files have already been copied through and left unchanged, and we can remove the from the file lists to be copied. These will save us time doing md5 on these files (which is especially relavent if they are big).
        # *Note - technically if someone switches a file with a different file and manipulates the metadate to match this can be a problem. If security needs to be taken into account to this degree this needs to be removed.
        logging.info("Going over previously recorded files...")
        source_files, replica_files, file_record = compare_with_file_record(source_files, replica_files, file_record)

        logging.debug("File record size " + str(len(file_record)))
        logging.debug("Unmatched source files: " + str(source_files))
        logging.debug("Unmatched replica files: " + str(replica_files))

        # md5 all the files that still exist in the source and replica directory lists
        #Find items in replica hashes that are not in source hashes and delete these files.
        #https://stackoverflow.com/questions/41125909/python-find-elements-in-one-list-that-are-not-in-the-other
        logging.info("Hashing source files with md5...") 
        source_meta, source_md5, replica_meta, replica_md5 = md5_source_replica(source_files, replica_files)

        # Go through all hashes in source
        # Go over all files in source and search for equivalent md5 hashes files in the replica.
        # 1. If they are not found - copy them over and document them in file record.
        # 2. If the md5 hash from source is found in replica it means the file name was changed (as we know the contents are the same and otherwise it would have been removed from the list earlier). In this case we move the file to the correct place and name, creating any subdirectories needed in the replica.
        logging.info("Copying and moving files in replica to match source...") 
        file_record = copy_and_move_files(source_dir, replica_dir, source_meta, source_md5, replica_meta, replica_md5, file_record)
        # Delete all unecessary old directories from replica - these directories would be empty directories that had files in them but they were moved/deleted in this sync action - leaving them empty. If the directories don't exist in the source now then they are deleted from replica.
        # This is being done at the end so that we avoid deleting files that have changed names before we had a chance to move them
        delete_empty_directories(source_dir, replica_dir, replica_files)

    logging.info("Sync finished")
    return file_record

"""
takes path of file record and loads the records in as FileMeta object pairs of source and replica files into a list
"""
def get_file_record(file_record_path):
    file_record = []
    with open(file_record_path, "r") as fr:
        for line in fr.readlines():
            source_f = line.split("^^^")[0].replace(os.linesep,"")
            replica_f = line.split("^^^")[1].replace(os.linesep,"")

            s_fullpath = source_f.split(";")[0]
            s_mod_time = source_f.split(";")[1]
            s_size = source_f.split(";")[2]
            s_md5 = source_f.split(";")[3]
            r_fullpath = replica_f.split(";")[0]
            r_mod_time = replica_f.split(";")[1]
            r_size = replica_f.split(";")[2]
            r_md5 = replica_f.split(";")[3]

            file_record.append((
                    FileMeta(s_fullpath, s_mod_time, s_size, s_md5),\
                    FileMeta(r_fullpath, r_mod_time, r_size, r_md5)\
                    ))
    return file_record

"""
Loads the file_record from file_record.txt that is saved in the src directory (if it exists)
Starts the main infinit loop that runs the sync.
calls sync_action and updates file_record every sync itteration.
This loop continues until stop_flag is changed to True by input_thread() or until the parent pid is detected as 1 - meaning the parent has terminated.
While the loop is sleeping until next sync interval it sets is_sleeping to True to indicate immidiate termination of program if "quit" is entered (see input_thread() and main()).
"""
def sync_loop(source_dir, replica_dir, interval, stop_flag, is_sleeping):
    logging.info("Starting synchronization from " + source_dir + " to " + replica_dir + " every " + str(interval) + " seconds")
    logging.info("to close this program enter the word \"quit\" and then Enter")
    #https://stackoverflow.com/questions/13180941/how-to-kill-a-while-loop-with-a-keystroke

    # File record is loaded from a file - this file contains pairs of files, 1 from source and 1 from replica, where the source file was already copied into the replica file in the past, their size and modification time. This will save us from running md5 on unecesary files later on.
    file_record_path = os.path.join(os.path.dirname(__file__),"file_record.txt")
    file_record = []
    if len(os.listdir(replica_dir)) == 0:
        if os.path.exists(file_record_path):
            os.remove(file_record_path)
    elif(os.path.exists(file_record_path)):
        file_record = get_file_record(file_record_path)

    # An infinit loop is started that sleeps every "interval" amount of time. The sleeping takes into account the time it took for the sync process, i.e. if the sync took 2 seconds and the interval was 5 secounds it will only sleep for 3 seconds.
    #The loop will stop when a variable is changed on the main thread. This happens once the word "quit" is entered.
    while not stop_flag.value:
        if os.getppid() == 1:
            sys.exit(0)
        start_time = int(time.time())
        file_record = sync_action(source_dir, replica_dir, file_record)
        
        with open(file_record_path, "w") as fr:
            for f in file_record:
                fr.write(f[0].fullpath + ";" + str(f[0].mod_time) + ";" + str(f[0].size) + ";" + f[0].md5 +\
                        "^^^" +\
                        f[1].fullpath + ";" + str(f[1].mod_time) + ";" + str(f[1].size) + ";" + f[1].md5 +\
                        os.linesep)

        if stop_flag.value:
            break
        if os.getppid() == 1:
            sys.exit(0)

        sleep_time = start_time + interval - time.time()
        if sleep_time > 0:
            logging.info("Next sync in: " + str(int(sleep_time)) + " seconds")
            is_sleeping.acquire()
            is_sleeping.value = True
            is_sleeping.release()
            time.sleep(sleep_time)
            is_sleeping.acquire()
            is_sleeping.value = False
            is_sleeping.release()

    sys.exit(0)

##########################################

def main(argv=None):
    #argparse will parse the arguments.
    parser = argparse.ArgumentParser("This program will synchronize files between 2 directories periodically.")

    parser.add_argument("-s", "--source-dir", help = "Source directory to be synced.", required=True)
    parser.add_argument("-r", "--replica-dir", help = "Replica directory to be synced to.", required=True)
    parser.add_argument("-i", "--interval", help = "Synchronization interval for syncing. Format is ##d##h##m##s", required=True)
    parser.add_argument("-l", "--log-dir", help = "Location of log file to be saved.", required=True)
    args = parser.parse_args(argv)
    
    #Set up the logging - creating the log directory provided if it does not exist yet and naming the log file using the date and time.
    try:
        setup_logging(args.log_dir)
    except Exception as e:
        print("ERROR: probelm creating log file in: " + args.log_dir)
        print("ERROR: " + str(e))
        traceback.print_exc()
        raise Exception(e)

    # Confirm that the source and replica directory exist. If a directory  does not exist - it will create it.
    try:
        source_dir, replica_dir = check_directories(args.source_dir, args.replica_dir)
    except Exception as e:
        logging.error("Directory path validation crashed with error: " + str(e))
        logging.error("Traceback: ", exc_info=True)
        raise Exception(e)
    
    # Convert interval from ##d##h##m##s into seconds.
    try:
        interval = interval_to_seconds(args.interval)
        logging.info("Interval " + args.interval + " in seconds = " + str(interval))
    except Exception as e:
        logging.error("Interval calculation crashed with error: " + str(e))
        logging.error("Traceback: ", exc_info=True)
        raise Exception(e)
    
    # Start a new thread that will run the infinit loop. This thread is defined a daemon so that is closes when the main program is closed.
    try:
        is_sleeping = multiprocessing.Value('b', False)
        stop_flag = multiprocessing.Value('b', False)
        loop_process = multiprocessing.Process(target=sync_loop,args=(source_dir, replica_dir, interval, stop_flag, is_sleeping, ), daemon=True)
        loop_process.start()
        # input thread is an infnit loop waiting for the user to enter the word "quit" - this will allow for safe exiting of the program by waiting for the sync loop to finish before exiting, so that copying processes dont get inturupted in the middle.
        if(input_thread(stop_flag, is_sleeping) == 1):
            loop_process.join()
        loop_process.terminate()

    except Exception as e:
        logging.error("Sync loop crashed with error: " + str(e))
        logging.error("Traceback: ", exc_info=True)
        raise Exception(e)


if __name__ == "__main__":
    sys.exit(main())
