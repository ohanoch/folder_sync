import pytest
import shutil
import tempfile
import random
import string
import time
import multiprocessing

import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.dirname((__file__))),"src"))
import pyautogui

from sync_folder import *
from helper import *

MAX_LETTERS_IN_FILE = 999
FILE_RECORD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),"src","file_record.txt")


#test that md5 algorithm works corretly
#this uses a file called DO_NOT_CHANGE.txt to do so. If this test fails make sure this file is:
#Last modified: Apr  8 08:24
#Size: 80 bytes
#If this is not the case - replace this file with a new one correct this test accordingly
def test_md5():
    assert md5(os.path.join(os.path.dirname(os.path.dirname(__file__)),"tests","DO_NOT_CHANGE.txt")) == "9b3a4f11c3cf7278746d07bdf4bdd101"


#test that interval conversion from ##d##h##m##s to seconds is done correctly
def test_intervals():
    assert interval_to_seconds("5d4h3m2s") == 446582
    assert interval_to_seconds("05d04h03m02s") == 446582
    assert interval_to_seconds("05d4h03m2s") == 446582
    assert interval_to_seconds("05d03m02s") == 432182
    assert interval_to_seconds("05d03m") == 432180
    assert interval_to_seconds("04h02s") == 14402
    assert interval_to_seconds("03m02s") == 182
    assert interval_to_seconds("05d") == 432000
    assert interval_to_seconds("04h") == 14400
    assert interval_to_seconds("03m") == 180
    assert interval_to_seconds("2s") == 2

def keyboard_input(s):
    print("Automating keyboard input - please do not press anything")
    time.sleep(2)
    pyautogui.write("quit")
    pyautogui.press("enter")

    time.sleep(2)
    pyautogui.write("quit")
    pyautogui.press("enter")
    print("Automating keyboard input done.")

def test_quit():
    is_sleeping = multiprocessing.Value('b', False)
    stop_flag = multiprocessing.Value('b', False)
    
    process = multiprocessing.Process(target=keyboard_input, args=("quit", ), daemon=True)
    process.start()
    assert input_thread(stop_flag, is_sleeping,) == 1
    is_sleeping.acquire()
    is_sleeping.value = True
    is_sleeping.release()
    stop_flag.acquire()
    stop_flag.value = False
    stop_flag.release()
    assert input_thread(stop_flag, is_sleeping,) == 0

    process.terminate()

def get_glob_count(sd, rd):
    sd_glob = glob.glob(os.path.join(sd.dirname,sd.basename) + '/**/*', recursive=True)
    rd_glob = glob.glob(os.path.join(rd.dirname,rd.basename) + '/**/*', recursive=True)
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    return sd_glob, rd_glob, sd_count, rd_count

def run_loop_instance(sd, rd, ld):
    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))

    return get_glob_count(sd,rd)

#logs folder does not exist
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> empty
def test_no_log_directory(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")

    process = multiprocessing.Process(target=main,args=(["-s", os.path.join(tmpdir, "sd"), "-r", os.path.join(tmpdir, "rd"), "-l", os.path.join(tmpdir, "ld"), "-i", "1s"],))
    process.start()
    time.sleep(5)
    process.terminate()
    os.remove(FILE_RECORD_PATH)

    assert len(os.listdir(os.path.join(tmpdir, "ld"))) == 1

    sd_glob, rd_glob, sd_count, rd_count = get_glob_count(sd, rd)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(os.path.join(tmpdir, "rd"),sf1.basename))
    assert md5(sf21) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,sf3.basename))

#log gets created
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> empty
def test_log_created(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")

    process = multiprocessing.Process(target=main,args=(["-s", os.path.join(tmpdir, "sd"), "-r", os.path.join(tmpdir, "rd"), "-l", os.path.join(tmpdir, "ld"), "-i", "1s"],))
    process.start()
    time.sleep(1)
    process.terminate()
    os.remove(FILE_RECORD_PATH)

    assert len(os.listdir(os.path.join(tmpdir, "ld"))) == 1


#source folder does not exist
#sd -> doesnt exist
#rd -> exists
def test_no_source_directory(tmpdir):
    print(tmpdir)
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")

    process = multiprocessing.Process(target=main,args=(["-s", os.path.join(tmpdir, "sd"), "-r", os.path.join(tmpdir, "rd"), "-l", os.path.join(tmpdir, "ld"), "-i", "1s"],))
    process.start()
    time.sleep(5)
    process.terminate()
    os.remove(FILE_RECORD_PATH)

    sd_glob = glob.glob(os.path.join(tmpdir, "sd") + '/**/*', recursive=True)
    rd_glob = glob.glob(os.path.join(tmpdir, "rd") + '/**/*', recursive=True)
    sd_count = sum([len(files) for r, d, files in os.walk(os.path.join(tmpdir, "sd"))])
    rd_count = sum([len(files) for r, d, files in os.walk(os.path.join(tmpdir, "rd"))])
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)

#replica folder does not exist
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> doesnt exist
def test_no_replica_directory(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    ld = tmpdir.mkdir("ld")

    process = multiprocessing.Process(target=main,args=(["-s", os.path.join(tmpdir, "sd"), "-r", os.path.join(tmpdir, "rd"), "-l", os.path.join(tmpdir, "ld"), "-i", "1s"],))
    process.start()
    time.sleep(5)
    process.terminate()
    os.remove(FILE_RECORD_PATH)

    sd_glob = glob.glob(os.path.join(sd.dirname,sd.basename) + '/**/*', recursive=True)
    rd_glob = glob.glob(os.path.join(tmpdir, "rd") + '/**/*', recursive=True)
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(os.path.join(tmpdir, "rd"))])
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(os.path.join(tmpdir, "rd"),sf1.basename))
    assert md5(sf21) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,sf3.basename))

#test source with empty replica. file structure:
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> empty
def test_replica_empty(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")
    
    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test source with empty source. file structure:
#sd -> empty
#rd -> (rf1, rd1 -> (rf21, rf22, rd2->(rf3)))
def test_source_empty(tmpdir):
    print(tmpdir)
    rd = tmpdir.mkdir("rd")
    rf1 = rd.join("rf1.txt")
    rf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd1 = rd.mkdir("rd1")
    rf21 = rd1.join("rf21.txt")
    rf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rf22 = rd1.join("rf22.txt")
    rf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd2 = rd1.mkdir("rd2")
    rf3 = rd2.join("rf3.txt")
    rf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd = tmpdir.mkdir("sd")
    ld = tmpdir.mkdir("ld")

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob) and rd_count == 0

#test with empty source and replica. file structure:
#sd -> empty
#rd -> empty
def test_source_replica_empty(tmpdir):
    print(tmpdir)
    rd = tmpdir.mkdir("rd")
    sd = tmpdir.mkdir("sd")
    ld = tmpdir.mkdir("ld")

    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    
    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob) and rd_count == 0

#test identical full source and replica. file structure:
#sd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
#rd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
def test_source_replica_identical(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf1 = shutil.copyfile(sf1, os.path.join(rd, "sf1.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rd2 = rd1.mkdir("sd2")
    rf3 = shutil.copyfile(sf3, os.path.join(rd2, "sf3.txt"))
    ld = tmpdir.mkdir("ld")

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test identical full source and replica except for extra file in replica in each ddirectory. file structure:
#sd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
#rd -> (sf1, rf12, sd1 -> (sf21, sf22, rf23, sd2->(sf3, rf32)))
def test_extra_file_replica(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf1 = shutil.copyfile(sf1, os.path.join(rd, "sf1.txt"))
    rf12 = rd.join("rf12.txt")
    rf12.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rf23 = rd1.join("rf23.txt")
    rf23.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd2 = rd1.mkdir("sd2")
    rf3 = shutil.copyfile(sf3, os.path.join(rd2, "sf3.txt"))
    rf32 = rd2.join("rf32.txt")
    rf32.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    ld = tmpdir.mkdir("ld")

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test identical full source and replica + extra files in each source directory. file structure:
#sd -> (sf11, sf12, sd1 -> (sf21, sf22, sf23, sd2->(sf31, sf32)))
#rd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
def test_extra_file_source(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf11 = sd.join("sf11.txt")
    sf11.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf12 = sd.join("sf12.txt")
    sf12.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf23 = sd1.join("sf23.txt")
    sf23.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf31 = sd2.join("sf31.txt")
    sf31.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf32 = sd2.join("sf32.txt")
    sf32.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf11 = shutil.copyfile(sf11, os.path.join(rd, "sf11.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rd2 = rd1.mkdir("sd2")
    rf31 = shutil.copyfile(sf31, os.path.join(rd2, "sf31.txt"))
    ld = tmpdir.mkdir("ld")

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf11) == md5(os.path.join(rd,sf11.basename))
    assert md5(sf12) == md5(os.path.join(rd,sf12.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf23) == md5(os.path.join(rd,sd1.basename,sf23.basename))
    assert md5(sf31) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf31.basename))
    assert md5(sf32) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf32.basename))

#test identical full source and replica. file structure:
#sd -> (sf11, sf13, sd1 -> (sf21, sf22, sf24, sd2->(sf31, sf33)))
#rd -> (sf11, sf12, sd1 -> (sf21, sf22, sf23, sd2->(sf31, sf32)))
#where sf13=sf12, sf24=sf23, sf33=sf32
def test_file_name_change_source(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf11 = sd.join("sf11.txt")
    sf11.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf12 = sd.join("sf12.txt")
    sf12.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf23 = sd1.join("sf23.txt")
    sf23.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf31 = sd2.join("sf31.txt")
    sf31.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf32 = sd2.join("sf32.txt")
    sf32.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf11 = shutil.copyfile(sf11, os.path.join(rd, "sf11.txt"))
    rf12 = shutil.copyfile(sf12, os.path.join(rd, "sf12.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rf23 = shutil.copyfile(sf23, os.path.join(rd1, "sf23.txt"))
    rd2 = rd1.mkdir("sd2")
    rf31 = shutil.copyfile(sf31, os.path.join(rd2, "sf31.txt"))
    rf32 = shutil.copyfile(sf32, os.path.join(rd2, "sf32.txt"))
    ld = tmpdir.mkdir("ld")

    shutil.move(os.path.join(sd, "sf12.txt"), os.path.join(sd, "sf13.txt"))
    shutil.move(os.path.join(sd1, "sf23.txt"), os.path.join(sd1, "sf24.txt"))
    shutil.move(os.path.join(sd2, "sf32.txt"), os.path.join(sd2, "sf33.txt"))

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf11) == md5(os.path.join(rd,sf11.basename))
    assert md5(os.path.join(sd,"sf13.txt")) == md5(os.path.join(rd,"sf13.txt"))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(os.path.join(sd,sd1.basename,"sf24.txt")) == md5(os.path.join(rd,sd1.basename,"sf24.txt"))
    assert md5(sf31) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf31.basename))
    assert md5(os.path.join(sd,sd1.basename,sd2.basename,"sf33.txt")) == md5(os.path.join(rd,sd1.basename,sd2.basename,"sf33.txt"))

#test identical full source and replica. file structure:
#sd -> (sf11, sf13, sd1 -> (sf21, sf22, sf24, sd2->(sf31, sf33)))
#rd -> (sf11, sf12, sd1 -> (sf21, sf22, sf23, sd2->(sf31, sf32)))
#where sf13=sf12, sf24=sf23, sf33=sf32
def test_file_name_change_replica(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf11 = sd.join("sf11.txt")
    sf11.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf12 = sd.join("sf12.txt")
    sf12.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf23 = sd1.join("sf23.txt")
    sf23.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf31 = sd2.join("sf31.txt")
    sf31.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf32 = sd2.join("sf32.txt")
    sf32.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf11 = shutil.copyfile(sf11, os.path.join(rd, "sf11.txt"))
    rf12 = shutil.copyfile(sf12, os.path.join(rd, "sf12.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rf23 = shutil.copyfile(sf23, os.path.join(rd1, "sf23.txt"))
    rd2 = rd1.mkdir("sd2")
    rf31 = shutil.copyfile(sf31, os.path.join(rd2, "sf31.txt"))
    rf32 = shutil.copyfile(sf32, os.path.join(rd2, "sf32.txt"))
    ld = tmpdir.mkdir("ld")

    shutil.move(os.path.join(rd, "sf12.txt"), os.path.join(rd, "sf13.txt"))
    shutil.move(os.path.join(rd1, "sf23.txt"), os.path.join(rd1, "sf24.txt"))
    shutil.move(os.path.join(rd2, "sf32.txt"), os.path.join(rd2, "sf33.txt"))

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf11) == md5(os.path.join(rd,sf11.basename))
    assert md5(sf12) == md5(os.path.join(rd,sf12.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf23) == md5(os.path.join(rd,sd1.basename,sf23.basename))
    assert md5(sf31) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf31.basename))
    assert md5(sf32) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf32.basename))
#test identical full source and replica. 1 file moved between directorues. file structure:
#sd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
#rd -> (sf1, sd1 -> (sf21, sd2->(sf3, sf22)))
def test_source_file_moved(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf1 = shutil.copyfile(sf1, os.path.join(rd, "sf1.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rd2 = rd1.mkdir("sd2")
    rf3 = shutil.copyfile(sf3, os.path.join(rd2, "sf3.txt"))
    ld = tmpdir.mkdir("ld")

    shutil.move(os.path.join(sd1, "sf22.txt"), os.path.join(sd2, "sf22.txt"))

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(os.path.join(sd2, "sf22.txt")) == md5(os.path.join(rd, sd1.basename ,sd2.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test identical full source and replica. 1 file moved between directorues. file structure:
#sd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
#rd -> (sf1, sd1 -> (sf21, sd2->(sf3, sf22)))
def test_replica_file_moved(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf1 = shutil.copyfile(sf1, os.path.join(rd, "sf1.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rd2 = rd1.mkdir("sd2")
    rf3 = shutil.copyfile(sf3, os.path.join(rd2, "sf3.txt"))
    ld = tmpdir.mkdir("ld")

    shutil.move(os.path.join(rd1, "sf22.txt"), os.path.join(rd2, "sf22.txt"))

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd, sd1.basename ,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test identical full source and replica. 1 file moved between directories and changed name. file structure:
#sd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
#rd -> (sf1, sd1 -> (sf21, sd2->(sf3, sf22)))
def test_source_file_moved_name_changed(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf1 = shutil.copyfile(sf1, os.path.join(rd, "sf1.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rd2 = rd1.mkdir("sd2")
    rf3 = shutil.copyfile(sf3, os.path.join(rd2, "sf3.txt"))
    ld = tmpdir.mkdir("ld")

    shutil.move(os.path.join(sd1, "sf22.txt"), os.path.join(sd2, "sf23.txt"))

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(os.path.join(sd,sd1.basename, sd2.basename,"sf23.txt")) == md5(os.path.join(rd,sd1.basename, sd2.basename,"sf23.txt"))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test identical full source and replica. 1 file moved between directories and changed name. file structure:
#sd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
#rd -> (sf1, sd1 -> (sf21, sd2->(sf3, sf22)))
def test_replica_file_moved_name_changed(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf1 = shutil.copyfile(sf1, os.path.join(rd, "sf1.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rd2 = rd1.mkdir("sd2")
    rf3 = shutil.copyfile(sf3, os.path.join(rd2, "sf3.txt"))
    ld = tmpdir.mkdir("ld")

    shutil.move(os.path.join(rd1, "sf22.txt"), os.path.join(rd2, "sf23.txt"))

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test identical full source and replica. 1 file which was alone if folder in source deleted. file structure:
#sd -> (sf1, sd1 -> (sf21, sf22, sd2->()))
#rd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
def test_source_last_file_deleted(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf1 = shutil.copyfile(sf1, os.path.join(rd, "sf1.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rd2 = rd1.mkdir("sd2")
    rf3 = shutil.copyfile(sf3, os.path.join(rd2, "sf3.txt"))
    ld = tmpdir.mkdir("ld")

    os.remove(os.path.join(sd2, "sf3.txt"))

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))

#test identical full source and replica. 1 file which was alone if folder in replica deleted. file structure:
#sd -> (sf1, sd1 -> (sf21, sf22, sd2->(sf3)))
#rd -> (sf1, sd1 -> (sf21, sf22, sd2->()))
def test_replica_last_file_deleted(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf1 = shutil.copyfile(sf1, os.path.join(rd, "sf1.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rd2 = rd1.mkdir("sd2")
    rf3 = shutil.copyfile(sf3, os.path.join(rd2, "sf3.txt"))
    ld = tmpdir.mkdir("ld")

    os.remove(os.path.join(rd2, "sf3.txt"))

    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test source with empty replica. spaces in file/folder names. file structure:
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> empty
def test_replica_empty_spaces_in_names(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf 1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf 21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd 2")
    sf3 = sd2.join("sf 3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")
    
    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test source with empty replica. sending directory names that end with "/" file structure:
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> empty
def test_replica_empty_names_with_slash(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")
    
    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename) + os.sep, os.path.join(rd.dirname, rd.basename) + os.sep)
    
    sd_glob, rd_glob, sd_count, rd_count = get_glob_count(sd, rd)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test source with empty replica. 1 file is 0 bytes. file structure:
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> empty
def test_zero_byte_file(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write('')
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")
    
    sd_glob, rd_glob, sd_count, rd_count = run_loop_instance(sd, rd, ld)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(rd,sf1.basename))
    assert md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))


#general loop test
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> empty
#interval is 5s
#after 2s first loop is sleeping -> move file in source and rename
#after 5s second loop is sleeping -> delete file from replica
#after 5s third loop is sleeping -> delete file from source

def test_general_loop(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")

    process = multiprocessing.Process(target=main,args=(["-s", os.path.join(tmpdir, "sd"), "-r", os.path.join(tmpdir, "rd"), "-l", os.path.join(tmpdir, "ld"), "-i", "5s"],))
    process.start()
    
    time.sleep(2)
    sd_glob, rd_glob, sd_count, rd_count = get_glob_count(sd, rd)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(os.path.join(tmpdir, "rd"),sf1.basename))
    assert md5(sf21) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf21.basename))
    assert md5(sf22) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf22.basename))
    assert md5(sf3) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,sf3.basename))
    
    #move sf22 from sd1 to sd2 and rename it to sf24
    shutil.move(os.path.join(sd1, "sf22.txt"), os.path.join(sd2, "sf24.txt"))
    time.sleep(5)
    sd_glob, rd_glob, sd_count, rd_count = get_glob_count(sd, rd)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(os.path.join(tmpdir, "rd"),sf1.basename))
    assert md5(sf21) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf21.basename))
    assert md5(os.path.join(sd2, "sf24.txt")) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,"sf24.txt"))
    assert md5(sf3) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,sf3.basename))
    
    #delete sf21.txt from sd1 in replica
    os.remove(os.path.join(tmpdir,"rd","sd1", "sf21.txt"))
    time.sleep(5)
    sd_glob, rd_glob, sd_count, rd_count = get_glob_count(sd, rd)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf1) == md5(os.path.join(os.path.join(tmpdir, "rd"),sf1.basename))
    assert md5(sf21) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf21.basename))
    assert md5(os.path.join(sd2, "sf24.txt")) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,"sf24.txt"))
    assert md5(sf3) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,sf3.basename))
    
    #delete sf1.txt from sd in source
    os.remove(os.path.join(sd, "sf1.txt"))
    time.sleep(5)
    sd_glob, rd_glob, sd_count, rd_count = get_glob_count(sd, rd)
    assert sd_count == rd_count
    assert len(sd_glob) == len(rd_glob)
    assert md5(sf21) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sf21.basename))
    assert md5(os.path.join(sd2, "sf24.txt")) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,"sf24.txt"))
    assert md5(sf3) == md5(os.path.join(os.path.join(tmpdir, "rd"),sd1.basename,sd2.basename,sf3.basename))

    process.terminate()
    os.remove(FILE_RECORD_PATH)

#test that file_record gets saved properly
#sd -> (sf1, sd1 -> (sf20, sf21, sd2->(sf3)))
#rd -> empty
def test_file_record(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")

    process = multiprocessing.Process(target=main,args=(["-s", os.path.join(tmpdir, "sd"), "-r", os.path.join(tmpdir, "rd"), "-l", os.path.join(tmpdir, "ld"), "-i", "5s"],))
    process.start()
    time.sleep(2)
    process.terminate()

    print(FILE_RECORD_PATH)
    with open(FILE_RECORD_PATH, "r") as fr:
        fr.seek(0)
        all_lines = []
        for line in fr.readlines():
            all_lines.append(line.replace(os.linesep, ""))

        line1 = os.path.join(sf1.dirname, sf1.basename) + ";" + \
                str(os.path.getmtime(sf1)) + ";" +\
                str(os.path.getsize(sf1)) + ";" + \
                "unknown" + "^^^" +\
                os.path.join(tmpdir, "rd", sf1.basename) + ";" + \
                str(os.path.getmtime(os.path.join(tmpdir, "rd", sf1.basename))) + ";" +\
                str(os.path.getsize(os.path.join(tmpdir, "rd", sf1.basename))) + ";" + \
                "unknown"
        assert line1 in all_lines

        line2 = os.path.join(sf21.dirname, sf21.basename) + ";" + \
                str(os.path.getmtime(sf21)) + ";" +\
                str(os.path.getsize(sf21)) + ";" + \
                "unknown" + "^^^" +\
                os.path.join(tmpdir, "rd", "sd1",sf21.basename) + ";" + \
                str(os.path.getmtime(os.path.join(tmpdir, "rd", "sd1",sf21.basename))) + ";" +\
                str(os.path.getsize(os.path.join(tmpdir, "rd", "sd1", sf21.basename))) + ";" + \
                "unknown"
        assert line2 in all_lines

        line3 = os.path.join(sf22.dirname, sf22.basename) + ";" + \
                str(os.path.getmtime(sf22)) + ";" +\
                str(os.path.getsize(sf22)) + ";" + \
                "unknown" + "^^^" +\
                os.path.join(tmpdir, "rd", "sd1",sf22.basename) + ";" + \
                str(os.path.getmtime(os.path.join(tmpdir, "rd", "sd1",sf22.basename))) + ";" +\
                str(os.path.getsize(os.path.join(tmpdir, "rd", "sd1", sf22.basename))) + ";" + \
                "unknown"
        assert line3 in all_lines

        line4 = os.path.join(sf3.dirname, sf3.basename) + ";" + \
                str(os.path.getmtime(sf3)) + ";" +\
                str(os.path.getsize(sf3)) + ";" + \
                "unknown" + "^^^" +\
                os.path.join(tmpdir, "rd", "sd1", "sd2",sf3.basename) + ";" + \
                str(os.path.getmtime(os.path.join(tmpdir, "rd", "sd1", "sd2",sf3.basename))) + ";" +\
                str(os.path.getsize(os.path.join(tmpdir, "rd", "sd1", "sd2", sf3.basename))) + ";" + \
                "unknown"
        assert line4 in all_lines


    os.remove(FILE_RECORD_PATH)
