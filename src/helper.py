import os
import hashlib

"""
Fix directory names to not end with slashes.
"""
def clean_dir_name(input_dir):
    tmp_dir = None
    if input_dir[-1] == os.sep:
        tmp_dir = input_dir[:-1]
    else:
        tmp_dir = input_dir
    return tmp_dir

"""
Check if source and repplica directories exist - if not, create them
"""
def check_directories(input_source_dir, input_replica_dir):
    source_dir = clean_dir_name(input_source_dir)
    replica_dir = clean_dir_name(input_replica_dir)

    #check if source directory exists - if not, return error and close program
    if not os.path.isdir(source_dir):
        os.makedirs(source_dir, exist_ok = True)
    #check if replica directory exists - if not, create it
    if not os.path.isdir(replica_dir):
        os.makedirs(replica_dir, exist_ok = True)

    return source_dir, replica_dir

"""
Accept interval in shapre ##d##h##m##s
calculate and return the time in seconds
Raise an eception if the shape is wrong
"""
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

"""
Perform md5 on file in chunks. This helps with lare files
"""
#https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
def md5(filename):
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()
