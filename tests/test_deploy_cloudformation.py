import unittest

from unittest.mock import Mock, patch

from minipipe import deploy_cloudformation


class TestHandler(unittest.TestCase):
    """Test handler methods"""


    @patch('minipipe.cf_check_status')
    @patch('minipipe.cf_create')
    @patch('minipipe.cf_update')
    def test_cf_create(self, mock_cf_update, mock_cf_create, mock_cf_check_status):
        mock_cf_check_status.return_value = None
        deploy_cloudformation('minipipe-test', 'test')
        mock_cf_create.assert_called_once()


    @patch('minipipe.cf_check_status')
    @patch('minipipe.cf_create')
    @patch('minipipe.cf_update')
    def test_cf_update(self, mock_cf_update, mock_cf_create, mock_cf_check_status):
        mock_cf_check_status.return_value = {'Stacks': [{'StackId': 'minipipe-test'}]}
        deploy_cloudformation('minipipe-test', 'test')
        mock_cf_update.assert_called_once()
