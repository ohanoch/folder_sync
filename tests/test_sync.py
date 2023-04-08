import pytest
import shutil
import tempfile
import random
import string

import sys
sys.path.append('..')

from src.sync_folder import *

MAX_LETTERS_IN_FILE = 999

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
    
    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and\
            md5(sf1) == md5(os.path.join(rd,sf1.basename)) and\
            md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename)) and\
            md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename)) and\
            md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

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

    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and rd_count == 0

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
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and rd_count == 0

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

    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and\
            md5(sf1) == md5(os.path.join(rd,sf1.basename)) and\
            md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename)) and\
            md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename)) and\
            md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

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

    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and\
            md5(sf1) == md5(os.path.join(rd,sf1.basename)) and\
            md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename)) and\
            md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename)) and\
            md5(sf3) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf3.basename))

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

    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and\
            md5(sf11) == md5(os.path.join(rd,sf11.basename)) and\
            md5(sf12) == md5(os.path.join(rd,sf12.basename)) and\
            md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename)) and\
            md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename)) and\
            md5(sf23) == md5(os.path.join(rd,sd1.basename,sf23.basename)) and\
            md5(sf31) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf31.basename)) and\
            md5(sf32) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf32.basename))

#test identical full source and replica. file structure:
#sd -> (sf11, sf13, sd1 -> (sf21, sf22, sf24, sd2->(sf31, sf33)))
#rd -> (sf11, sf12, sd1 -> (sf21, sf22, sf23, sd2->(sf31, sf32)))
#where sf13=sf12, sf24=sf23, sf33=sf32
def test_file_name_change_source(tmpdir):
    print(tmpdir)
    sd = tmpdir.mkdir("sd")
    sf11 = sd.join("sf11.txt")
    sf11.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf13 = sd.join("sf13.txt")
    sf13.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd1 = sd.mkdir("sd1")
    sf21 = sd1.join("sf21.txt")
    sf21.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf22 = sd1.join("sf22.txt")
    sf22.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf24 = sd1.join("sf24.txt")
    sf24.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sd2 = sd1.mkdir("sd2")
    sf31 = sd2.join("sf31.txt")
    sf31.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    sf33 = sd2.join("sf33.txt")
    sf33.write(''.join(random.choice(string.ascii_letters) for i in range(random.randint(1,MAX_LETTERS_IN_FILE))))
    rd = tmpdir.mkdir("rd")
    rf11 = shutil.copyfile(sf11, os.path.join(rd, "sf11.txt"))
    rf12 = shutil.copyfile(sf13, os.path.join(rd, "sf12.txt"))
    rd1 = rd.mkdir("sd1")
    rf21 = shutil.copyfile(sf21, os.path.join(rd1, "sf21.txt"))
    rf22 = shutil.copyfile(sf22, os.path.join(rd1, "sf22.txt"))
    rf23 = shutil.copyfile(sf24, os.path.join(rd1, "sf23.txt"))
    rd2 = rd1.mkdir("sd2")
    rf31 = shutil.copyfile(sf31, os.path.join(rd2, "sf31.txt"))
    rf32 = shutil.copyfile(sf33, os.path.join(rd2, "sf32.txt"))
    ld = tmpdir.mkdir("ld")

    setup_logging(os.path.join(ld.dirname, ld.basename))
    sync_action(os.path.join(sd.dirname, sd.basename), os.path.join(rd.dirname, rd.basename))
    sd_count = sum([len(files) for r, d, files in os.walk(sd)])
    rd_count = sum([len(files) for r, d, files in os.walk(rd)])
    assert sd_count == rd_count and\
            md5(sf11) == md5(os.path.join(rd,sf11.basename)) and\
            md5(sf13) == md5(os.path.join(rd,"sf13.txt")) and\
            md5(sf21) == md5(os.path.join(rd,sd1.basename,sf21.basename)) and\
            md5(sf22) == md5(os.path.join(rd,sd1.basename,sf22.basename)) and\
            md5(sf24) == md5(os.path.join(rd,sd1.basename,"sf24.txt")) and\
            md5(sf31) == md5(os.path.join(rd,sd1.basename,sd2.basename,sf31.basename)) and\
            md5(sf33) == md5(os.path.join(rd,sd1.basename,sd2.basename,"sf33.txt"))
