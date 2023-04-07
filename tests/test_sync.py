import pytest
import shutil
import tempfile

import sys
sys.path.append('..')

from src.sync_folder import *

def prepare_test_area():
    try:
        shutil.rmtree("sd")
        shutil.rmtree("rd")
        shutil.rmtree("ld")
        os.mkdir("sd")
        os.mkdir("rd")
        os.mkdir("ld")
    except OSError as e:
        print("Error preparing testing area: " + e.strerror)

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


def test_replica_empty():
    prepare_test_area()
    os.makedirs(os.path.join("sd","d1","d2","d3"), exist_ok=True)
    temp = []
    temp.append(tempfile.NamedTemporaryFile(dir="sd"))
    temp.append(tempfile.NamedTemporaryFile(dir=os.path.join("sd","d1")))
    temp.append(tempfile.NamedTemporaryFile(dir=os.path.join("sd","d1","d2")))
    sync_action("sd","rd")
    sd_count = sum([len(files) for r, d, files in os.walk("sd")])
    rd_count = sum([len(files) for r, d, files in os.walk("rd")])
    assert sd_count == rd_count and\
            md5(temp[0].name) == md5(os.path.join("rd",temp[0].name)) and\
            md5(temp[1].name) == md5(os.path.join("rd", "d1",temp[1].name)) and\
            md5(temp[2].name) == md5(os.path.join("rd", "d1", "d2",temp[2].name))

