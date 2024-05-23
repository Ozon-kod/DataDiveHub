import unittest
import json
from unittest.mock import patch, MagicMock, mock_open, call
import app
from flask_testing import TestCase
from io import BytesIO
import os
import subprocess

class TestExecuteQuery(unittest.TestCase):
    # Check when execute query works
    @patch('app.requests.get')
    def test_execute_query_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Query result"
        mock_get.return_value = mock_response


        result = app.execute_query("sample_query")

        self.assertEqual(result, "Query result")

    # Check that execute query returns none when failed
    @patch('app.requests.get')
    def test_execute_query_failure(self, mock_get):
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

class test_routes(TestCase,unittest.TestCase):
    def create_app(self):
        app.app.config['TESTING'] = True
        return app.app
    
    def test_latitude_endpoint(self):
        response = self.client.get('/get-latitude')
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(response.status_code, 200)

class TestProcessGarminFile(unittest.TestCase):
    def setUp(self):
        self.file = MagicMock()
        self.file.filename = 'test.fit'
        self.latitude = 34.0522
        self.longitude = -118.2437
        self.name = 'Test Dive Site'

    @patch('app.os.remove')
    @patch('app.subprocess.run')
    @patch('app.open', new_callable=mock_open, read_data='processed xml content')
    @patch('app.secure_filename')
    @patch('app.update_xml_with_coordinates')
    def test_process_garmin_file_success(self, mock_update_xml, mock_secure_filename, mock_open, mock_run, mock_remove):
        mock_secure_filename.side_effect = lambda x: x  # Return filename unchanged
        mock_run.return_value = None  # Simulate successful subprocess execution

        xml_data, error = app.process_garmin_file(self.file, self.latitude, self.longitude, self.name)

        print("Called with:", mock_update_xml.call_args_list)  # Log the arguments passed

        expected_path = os.path.join("testupload", "test.xml")
        mock_update_xml.assert_called_once_with(
            expected_path, self.latitude, self.longitude, self.name
        )

        self.assertIsNotNone(xml_data)
        self.assertIsNone(error)
        self.assertEqual(mock_update_xml.call_args, call(
            expected_path, self.latitude, self.longitude, self.name
        ))

        mock_run.assert_called_once()
        mock_remove.assert_any_call(os.path.join("testupload", "test.fit"))
        mock_remove.assert_any_call(os.path.join("testupload", "test.xml"))

    @patch('app.subprocess.run')
    def test_process_garmin_file_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')  # Simulate subprocess error

        xml_data, error = app.process_garmin_file(self.file, self.latitude, self.longitude, self.name)

        self.assertIsNone(xml_data)
        self.assertIn("Error processing file", error)
if __name__ == '__main__':
    unittest.main()
