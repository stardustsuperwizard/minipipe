import os
import tempfile
import unittest

from unittest.mock import Mock, patch

from minipipe import list_files


class TestHandler(unittest.TestCase):
    """Test handler methods"""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    # def tearDown(self):


    def test_cf_create(self):
        with self.test_dir as tempdirname:
            with open(f'{tempdirname}/test.yaml', 'w') as f:
                f.write('hello: world')
            results = list_files(tempdirname)  
            self.assertTrue(results, ['test.yaml'])
