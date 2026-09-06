import re

import monetils


def test_import():
    assert re.match(r"^\d+\.\d+\.\d+", monetils.__version__)
