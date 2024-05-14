import unittest
from unittest.mock import patch, MagicMock
from app import execute_query

class TestExecuteQuery(unittest.TestCase):
    # Check when execute query works
    @patch('app.requests.get')
    def test_execute_query_success(self, mock_get):
        # Simulate a successful response from the database
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Query result"
        mock_get.return_value = mock_response

        # Call the execute_query function with a sample query
        result = execute_query("sample_query")

        # Assert that the function returns the expected result
        self.assertEqual(result, "Query result")

    # Check that execute query returns none when failed
    @patch('app.requests.get')
    def test_execute_query_failure(self, mock_get):
        # Simulate a failed response from the database
        mock_response = MagicMock()
        mock_response.status_code = 500  # Simulate failure with status code 500
        mock_get.return_value = mock_response

        # Call the execute_query function with a sample query
        result = execute_query("sample_query")

        # Assert that the function returns None in case of failure
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
