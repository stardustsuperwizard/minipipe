import os
import tempfile
import unittest

from unittest.mock import Mock, patch

from minipipe import run_updates


class TestHandler(unittest.TestCase):
    """Test handler methods"""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()

    # def tearDown(self):


    @patch('minipipe.deploy_cloudformation')
    def test_cf_create(self, mock_deploy_cloudformation):
        with self.test_dir as tempdirname:
            with open(f'{tempdirname}/test.yaml', 'w') as f:
                f.write('hello: world')
            run_updates(f'{tempdirname}/test.yaml')  
            mock_deploy_cloudformation.assert_called_once()
