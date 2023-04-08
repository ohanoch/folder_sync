import pytest
import shutil
import tempfile
import random
import string

import sys
sys.path.append('..')

from src.sync_folder import *

#test that md5 algorithm works corretly
#this uses a file called DO_NOT_CHANGE.txt to do so. If this test fails make sure this file is:
#Last modified: Apr  8 08:24
#Size: 80 bytes
#If this is not the case - replace this file with a new one correct this test accordingly
def test_md5():
    assert md5("DO_NOT_CHANGE.txt") == "9b3a4f11c3cf7278746d07bdf4bdd101"


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

#test source with file structure:
#sd -> (f1, d1 -> (f2, d2->(f3)))
#rd -> empty
def test_replica_empty(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf1 = sd.join("sf1.txt")
    sf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,999999))))
    sd1 = sd.mkdir("sd1")
    sf2 = sd1.join("sf2.txt")
    sf2.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,999999))))
    sd2 = sd1.mkdir("sd2")
    sf3 = sd2.join("sf3.txt")
    sf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,999999))))
    rd = tmpdir.mkdir("rd")
    ld = tmpdir.mkdir("ld")
    
    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and\
            md5(sf1) == md5(os.path.join(rd,sf1.basename)) and\
            md5(sf2) == md5(os.path.join(rd,sd1.basename,sf2.basename)) and\
            md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

#test source with file structure:
#sd -> empty
#rd -> (f1, d1 -> (f2, d2->(f3)))
def test_source_empty(tmpdir):
    print(tmpdir)
    rd = tmpdir.mkdir("rd")
    rf1 = rd.join("rf1.txt")
    rf1.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,999999))))
    rd1 = rd.mkdir("rd1")
    rf2 = rd1.join("rf2.txt")
    rf2.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,999999))))
    rd2 = rd1.mkdir("rd2")
    rf3 = rd2.join("rf3.txt")
    rf3.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,999999))))
    sd = tmpdir.mkdir("sd")
    ld = tmpdir.mkdir("ld")

    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and rd_count == 0

