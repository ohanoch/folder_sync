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

import hashlib

import logging

class FileMeta:
    def __init__(self, fullname, mod_time=None, size=None, md5=None):
        self.fullname = fullname
        self.mod_time = mod_time
        self.size = size
        self.md5=md5

def input_thread(stop_flag, is_sleeping):
    while(True):
        try:
            key_input = input()
            print(is_sleeping.value)
            if key_input == "quit":
                if is_sleeping.value == True:
                    logging.info("Closing program after quit command.")
                    return 0
                else:
                    logging.info("finishing current synchronization loop. Program will exit once this is complete")
                    stop_flag.value = True
                    return 1
        except Exception as e:
            pass

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

#make sure source and replica directories exist
def check_directories(input_source_dir, input_replica_dir):
    source_dir = None
    if input_source_dir[-1] == os.sep:
        source_dir = input_source_dir[:-1]
    else:
        source_dir = input_source_dir

    replica_dir = None
    if input_replica_dir[-1] == os.sep:
        replica_dir = input_replica_dir[:-1]
    else:
        replica_dir = input_replica_dir

    #check if source directory exists - if not, return error and close program
    if not os.path.isdir(source_dir):
        raise Exception("Source directory not found.")
    #check if replica directory exists - if not, create it
    if not os.path.isdir(replica_dir):
        os.makedirs(replica_dir, exist_ok = True)

    return source_dir, replica_dir

def interval_to_seconds(input_interval):
    try:
        if not "d" in input_interval and\
            not "h" in input_interval and\
            not "m" in input_interval and\
            not "s" in input_interval:
                raise Exception("d,m,h,s not found in interval input.")

        if "d" in input_interval:
            days = int(input_interval.split("d")[0])
            input_interval = "".join(input_interval.split("d")[1:])
        else:
            days = 0
        if "h" in input_interval:
            hours = int(input_interval.split("h")[0])
            input_interval = "".join(input_interval.split("h")[1:])
        else:
            hours = 0
        if "m" in input_interval:
            minutes = int(input_interval.split("m")[0])
            input_interval = "".join(input_interval.split("m")[1:])
        else:
            minutes = 0
        if "s" in input_interval:
            seconds = int(input_interval.split("s")[0])
        else:
            seconds = 0
    except:
        raise Exception("Bad interval entered. Interval should be of shape ##d##h##m##s - got: " + input_interval)
    return days*24*60*60  + hours*60*60 + minutes*60 + seconds

#https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
def md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def sync_action(source_dir, replica_dir, file_record=[]):
    logging.info("Starting sync")
    #if replica directory is empty - copy everything from source directory over.
    if len(os.listdir(replica_dir)) == 0:
        logging.info("replica directory is empty, copying over entire source directory")
        shutil.copytree(source_dir, replica_dir, dirs_exist_ok=True)
    else:
        #go over recorded file names and modification dates - md5 all files in source and all files in replica that are not in the list
        #this is to avoid hashing unnecessary files, which can be relavent if we have large files
        logging.info("Going over previously recorded files...")
        source_files = glob.glob(source_dir + '/**/*', recursive=True)
        replica_files = glob.glob(replica_dir + '/**/*', recursive=True)
        for file_pair in file_record:
            if file_pair[0].fullname in source_files and \
                    file_pair[0].mod_time == os.path.getmtime(file_pair[0].fullname) and\
                    file_pair[0].size == os.path.getsize(file_pair[0].fullname) and\
                    file_pair[1].fullname in replica_files and \
                    file_pair[1].mod_time == os.path.getmtime(file_pair[1].fullname) and\
                    file_pair[1].size == os.path.getsize(file_pair[1].fullname):
                        source_files.remove(file_pair[0].fullname)
                        replica_files.remove(file_pair[1].fullname)
            else:
                file_record.remove(file_pair)

        logging.debug("File record size " + str(len(file_record)))
        logging.debug("Unmatched source files: " + str(source_files))
        logging.debug("Unmatched replica files: " + str(replica_files))

        logging.info("Hashing source files with md5...") 
        source_meta = []
        source_md5 = []
        for f_name in source_files:
            if os.path.isdir(f_name):
                continue
            f_md5 = md5(f_name)
            source_meta.append(FileMeta(fullname=f_name, mod_time=os.path.getmtime(f_name), size=os.path.getsize(f_name), md5=f_md5))
            source_md5.append(f_md5)
        
        #Find items in replica hashes that are not in source hashes and delete these files.
        #https://stackoverflow.com/questions/41125909/python-find-elements-in-one-list-that-are-not-in-the-other
        logging.info("Hashing replica files with md5 and deleting unmatched files...") 
        replica_meta = []
        replica_md5 = []
        for f_name in replica_files:
            if os.path.isdir(f_name):
                continue
            f_md5 = md5(f_name)
            if f_md5 not in source_md5:
                logging.info("Deleting file from replica directory: " + f_name)
                os.remove(f_name)
                replica_files.remove(f_name)
            else:
                replica_meta.append(FileMeta(fullname=f_name, mod_time=os.path.getmtime(f_name), size=os.path.getsize(f_name), md5=f_md5))
                replica_md5.append(f_md5)

        #Go through all hashes in source
        #For items in source that are not in replica - copy them over. Record the file name and modification date of file in source and in replica
        logging.info("Copying and moving files in replica to match source...") 
        for source_f in source_meta:
            f_relative_fullname = source_f.fullname.replace(source_dir + os.sep,"")
            replica_f_dir = os.path.join(replica_dir, os.sep.join(f_relative_fullname.split(os.sep)[:-1]))
            if not os.path.isdir(replica_f_dir):
                    os.makedirs(replica_f_dir, exist_ok=True)
            replica_f_fullname = os.path.join(replica_dir, f_relative_fullname)

            if source_f.md5 not in replica_md5:
                
                logging.info("Copying file from source to replica: " + f_relative_fullname)
                shutil.copyfile(source_f.fullname, replica_f_fullname)
                file_record.append((\
                        source_f,\
                        FileMeta(fullname=replica_f_fullname, mod_time=os.path.getmtime(replica_f_fullname), size=os.path.getsize(replica_f_fullname), md5=source_f.md5)))
            #For items in source that are in replica - move/rename the file in replica to the same as in source
            else: 
                for replica_f in replica_meta:
                    if replica_f.md5 == source_f.md5:
                        logging.info("Moving file in replica from: " + replica_f.fullname + " to: " + replica_f_fullname)
                        shutil.move(replica_f.fullname, replica_f_fullname)
                        file_record.append((\
                                source_f,\
                                replica_f))
                        break

        #Search for folders that are not in source and delete them from replica
        #This is being done at the end so that we avoid deleting files that have changed names before we had a chance to move them
        for f_name in replica_files:
            if os.path.isdir(f_name):
                if not os.path.isdir(os.path.join(source_dir, f_name.replace(replica_dir + os.sep, ""))):
                    logging.info("Deleting directory from replica that does not exist in source: " + f_name)
                    shutil.rmtree(f_name)

    logging.info("Sync finished")
    return file_record


def sync_loop(source_dir, replica_dir, interval, stop_flag, is_sleeping):
    logging.info("Starting synchronization from " + source_dir + " to " + replica_dir + " every " + str(interval))
    logging.info("to close this program enter the word \"quit\" and then Enter")
    #https://stackoverflow.com/questions/13180941/how-to-kill-a-while-loop-with-a-keystroke

    file_record=[]
    if(os.path.exists("file_record.txt")):
        with open("file_record.txt", "r") as fr:
            for line in fr.readlines():
                source_f = line.split("^^^")[0]
                replica_f = line.split("^^^")[1]

                s_fullname = source_f.split(";")[0]
                s_mod_time = source_f.split(";")[1]
                s_size = source_f.split(";")[2]
                s_md5 = source_f.split(";")[3]
                r_fullname = replica_f.split(";")[0]
                r_mod_time = replica_f.split(";")[1]
                r_size = replica_f.split(";")[2]
                r_md5 = replica_f.split(";")[3]

                file_record.append((
                        FileMeta(s_fullname, s_mod_time, s_size, s_md5),\
                        FileMeta(r_fullname, r_mod_time, r_size, r_md5)\
                        ))

    while not stop_flag.value:
        start_time = int(time.time())
        file_record = sync_action(source_dir, replica_dir, file_record)
        
        with open("file_record.txt", "w") as fr:
            for f in file_record:
                fr.write(f[0].fullname + ";" + str(f[0].mod_time) + ";" + str(f[0].size) + ";" + f[0].md5 +\
                        "^^^" +\
                        f[1].fullname + ";" + str(f[1].mod_time) + ";" + str(f[1].size) + ";" + f[1].md5
                        )

        if stop_flag.value:
            break
        
        if os.getppid() == 1:
            sys.exit(0)

        sleep_time = start_time + interval - time.time()
        if sleep_time > 0:
            logging.info("Next sync in: " + str(int(sleep_time)) + " seconds")
            is_sleeping.value = True
            time.sleep(sleep_time)
            is_sleeping.value = False

    sys.exit(0)

##########################################

def main(argv=None):
    parser = argparse.ArgumentParser("This program will synchronize files between 2 directories periodically.")

    parser.add_argument("-s", "--source-dir", help = "Source directory to be synced.", required=True)
    parser.add_argument("-r", "--replica-dir", help = "Replica directory to be synced to.", required=True)
    parser.add_argument("-i", "--interval", help = "Synchronization interval for syncing. Format is ##d##h##m##s", required=True)
    parser.add_argument("-l", "--log-dir", help = "Location of log file to be saved.", required=True)
    args = parser.parse_args(argv)
    
    try:
        setup_logging(args.log_dir)
    except Exception as e:
        print("ERROR: probelm creating log file in: " + args.log_dir)
        print("ERROR: " + str(e))
        traceback.print_exc()
        raise Exception(e)

    #Check if source and replica directories are valid
    try:

        source_dir, replica_dir = check_directories(args.source_dir, args.replica_dir)
    except Exception as e:
        logging.error("Directory path validation crashed with error: " + str(e))
        logging.error("Traceback: ", exc_info=True)
        raise Exception(e)
    
    #translate interval into seconds
    try:
        interval = interval_to_seconds(args.interval)
        logging.info("Interval " + args.interval + " in seconds = " + str(interval))
    except Exception as e:
        logging.error("Interval calculation crashed with error: " + str(e))
        logging.error("Traceback: ", exc_info=True)
        raise Exception(e)

    try:
        is_sleeping = multiprocessing.Value('b', False)
        stop_flag = multiprocessing.Value('b', False)
        loop_process = multiprocessing.Process(target=sync_loop,args=(source_dir, replica_dir, interval, stop_flag, is_sleeping, ), daemon=True)
        loop_process.start()
        if(input_thread(stop_flag, is_sleeping) == 1):
            loop_process.join()
        loop_process.terminate()

    except Exception as e:
        logging.error("Sync loop crashed with error: " + str(e))
        logging.error("Traceback: ", exc_info=True)
        raise Exception(e)


if __name__ == "__main__":
    sys.exit(main())
