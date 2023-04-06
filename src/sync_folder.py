import argparse
import time
import _thread
import sys

def input_thread(stop_flag, is_sleeping):
    key_input = input()
    if key_input == "quit":
        if is_sleeping:
            print("Closing program after keyboard interupt.")
            sys.exit(0)
        else:
            print("finishing current synchronization loop. Program will exit once this is complete")
            stop_flag.append(True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("This program will synchronize files between 2 directories periodically.")

    parser.add_argument("-s", "--source", help = "Source directory to be synced.")
    parser.add_argument("-r", "--replica", help = "Replica directory to be synced to.")
    parser.add_argument("-i", "--interval", help = "Synchronization interval for syncing. Format is ##d##h##m##s")
    parser.add_argument("-l", "--log-file", help = "Location of log file to be saved.")
    args = parser.parse_args()

    #check if source directory exists - if not, return error and close program
    #check if replica directory exists - if not, create it
    #check if log file location eists - if not, create it
    
    #translate interval into seconds
    interval = interval_to_seconds()
    
    print("Starting synchronization from " + args.source + " to " args.replica)
    print("to close this program enter the word \"quit\" and then Enter")
    #https://stackoverflow.com/questions/13180941/how-to-kill-a-while-loop-with-a-keystroke

    is_sleeping = false
    stop_flag = []
    _thread.start_new_thread(input_thread, (stop_flag, is_sleeping,))
    while not stop_flag:
        start_time = int(time.time())
        #if replica directory is empty
            #copy everything from source directory over.
        #else:
            #go over recorded file names and modification dates - md5 all files in source and all files in replica that are not in the list
            #find items in replica hashes that are not in source hashes and delete these files.
                #https://stackoverflow.com/questions/41125909/python-find-elements-in-one-list-that-are-not-in-the-other
                #wtire in log
            #go through all hashes in source
                #for items in source that are not in replica - copy them over. Record the file name and modification date of file in source and in replica
                #write in log
                #for items in source that are in replica -rename the file in replica to the same as in source
                #write in log

        if stop_flag:
            break

        sleep_time = start_time + interval - time.time()
        if sleep_time > 0:
            is_sleeping = true
            time.sleep(sleep_time)
            is_sleeping = false


