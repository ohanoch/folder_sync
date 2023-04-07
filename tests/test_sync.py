import pytest
import shutil

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





