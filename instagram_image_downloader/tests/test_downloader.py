import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Adjust sys.path to include the parent directory so 'downloader' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from downloader import (
    extract_image_urls,
    download_image,
    InstagramURLError,
    ParsingError,
    NetworkError,
    DownloadError,
    SaveError
)
import requests # Import requests to mock its exceptions

class TestExtractImageUrls(unittest.TestCase):

    @patch('downloader.requests.get')
    def test_extract_single_og_image(self, mock_get):
        html_content = """
        <html><head>
        <meta property="og:image" content="http://example.com/image1.jpg" />
        </head></html>
        """
        mock_response = MagicMock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock() # Ensure this doesn't raise an error
        mock_get.return_value = mock_response

        urls = extract_image_urls("https://www.instagram.com/p/validpost/")
        self.assertEqual(urls, ["http://example.com/image1.jpg"])
        mock_get.assert_called_once_with("https://www.instagram.com/p/validpost/", headers=unittest.mock.ANY, timeout=10)

    @patch('downloader.requests.get')
    def test_extract_multiple_og_images(self, mock_get):
        # Based on current implementation, only the first og:image found in sequence is returned,
        # or rather, all og:image tags are collected.
        html_content = """
        <html><head>
        <meta property="og:image" content="http://example.com/image1.jpg" />
        <meta property="og:image" content="http://example.com/image2.jpg" />
        </head></html>
        """
        mock_response = MagicMock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        urls = extract_image_urls("https://www.instagram.com/p/validpost/")
        self.assertEqual(urls, ["http://example.com/image1.jpg", "http://example.com/image2.jpg"])

    @patch('downloader.requests.get')
    def test_no_og_image_found(self, mock_get):
        html_content = "<html><head></head></html>"
        mock_response = MagicMock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with self.assertRaisesRegex(ParsingError, "Could not find image URLs"):
            extract_image_urls("https://www.instagram.com/p/nopost/")

    def test_invalid_url_format(self):
        with self.assertRaisesRegex(InstagramURLError, "Invalid Instagram URL"):
            extract_image_urls("http://example.com/notinstagram")

    @patch('downloader.requests.get')
    def test_network_error_request_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Test network error")
        with self.assertRaisesRegex(NetworkError, "Error fetching URL"):
            extract_image_urls("https://www.instagram.com/p/networkissue/")
            
    @patch('downloader.requests.get')
    def test_http_404_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(InstagramURLError, "Instagram post not found \(404\)"):
            extract_image_urls("https://www.instagram.com/p/notfoundpost/")

    @patch('downloader.requests.get')
    def test_http_client_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 403 # Example client error
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(InstagramURLError, "Client error accessing Instagram URL \(403\)"):
            extract_image_urls("https://www.instagram.com/p/clienterror/")

    @patch('downloader.requests.get')
    def test_http_server_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 503 # Example server error
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        with self.assertRaisesRegex(NetworkError, "Instagram server error \(503\)"):
            extract_image_urls("https://www.instagram.com/p/servererror/")

class TestDownloadImage(unittest.TestCase):

    @patch('downloader.requests.get')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_download_image_success(self, mock_file_open, mock_get):
        mock_image_content = b"fakeimagedata"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        # Configure iter_content for the mock response
        mock_response.iter_content = MagicMock(return_value=iter([mock_image_content]))
        mock_get.return_value = mock_response

        result = download_image("http://example.com/image.jpg", "dummy/path/image.jpg")

        self.assertTrue(result)
        mock_get.assert_called_once_with("http://example.com/image.jpg", headers=unittest.mock.ANY, stream=True, timeout=10)
        mock_file_open.assert_called_once_with("dummy/path/image.jpg", 'wb')
        mock_file_open().write.assert_called_once_with(mock_image_content)

    @patch('downloader.requests.get')
    def test_download_image_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Test connection error")
        with self.assertRaisesRegex(NetworkError, "Connection error downloading image"):
            download_image("http://example.com/image.jpg", "dummy/path/image.jpg")

    @patch('downloader.requests.get')
    def test_download_image_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        with self.assertRaisesRegex(DownloadError, "HTTP error 404 downloading image"):
            download_image("http://example.com/image404.jpg", "dummy/path/image.jpg")

    @patch('downloader.requests.get')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_download_image_io_error(self, mock_file_open, mock_get):
        mock_image_content = b"fakeimagedata"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content = MagicMock(return_value=iter([mock_image_content]))
        mock_get.return_value = mock_response
        
        mock_file_open.side_effect = IOError("Test IO error")

        with self.assertRaisesRegex(SaveError, "Error saving image"):
            download_image("http://example.com/image.jpg", "dummy/path/image.jpg")


if __name__ == '__main__':
    unittest.main()
