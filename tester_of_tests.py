import unittest
import json
from unittest.mock import patch, MagicMock
import app
from flask_testing import TestCase
from io import BytesIO

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
        result = app.execute_query("sample_query")

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
        result = app.execute_query("sample_query")

        # Assert that the function returns None in case of failure
        self.assertIsNone(result)
    
    @patch('requests.put')
    def test_add_xml_data_to_database_success(self, mock_put):
        mock_put.return_value.status_code = 201
        success, message = app.add_xml_data_to_database("dives", "dummy.xml", "<data></data>")
        self.assertTrue(success)

class test_extract_numbers_between_tags(unittest.TestCase):
    def setUp(self):
        # Example XML data
        self.xml_data = """
        <root>
            <latitude>34.0522</latitude>
            <longitude>-118.2437</longitude>
            <depth>200</depth>
            <depth>150</depth>
            <depth>100</depth>
        </root>
        """

    def test_extract_numbers_from_latitude(self):
        # Testing extraction from <latitude> tag
        latitudes = app.extract_numbers_between_tags(self.xml_data, 'latitude')
        self.assertEqual(latitudes, ['34.0522'], "Should extract the latitude")

    def test_extract_numbers_from_depth(self):
        # Testing extraction from <depth> tag
        depths = app.extract_numbers_between_tags(self.xml_data, 'depth')
        self.assertEqual(depths, ['200', '150', '100'], "Should extract all depths")

    def test_no_tags_found(self):
        # Testing with a tag not present in the data
        results = app.extract_numbers_between_tags(self.xml_data, 'temperature')
        self.assertEqual(results, [], "Should return an empty list when no tags found")

class test_routes(TestCase):
    def create_app(self):
        app.app.config['TESTING'] = True
        return app.app
    
    def test_latitude_endpoint(self):
        response = self.client.get('/get-latitude')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'latitude': '34.0522'})

    def test_upload_route_to_no_file(self):
        response = self.client.post('/upload', data={})
        self.assertEqual(response.status_code, 400)

    def test_upload_route_wrong_file_type(self):
        data = {'xmlFile': (BytesIO(b'content'), 'test.txt')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
    
    def test_upload_route_success(self):
        data = {'xmlFile': (BytesIO(b'content'), 'test.xml')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertequal(response.status_code, 200)
    
if __name__ == '__main__':
    unittest.main()
