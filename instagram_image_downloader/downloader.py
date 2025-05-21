import requests
from bs4 import BeautifulSoup

# Custom Exceptions
class InstagramDownloaderException(Exception):
    """Base exception for this application."""
    pass

class InstagramURLError(InstagramDownloaderException):
    """Indicates an issue with the provided Instagram URL (e.g., invalid format, 404 not found)."""
    pass

class ParsingError(InstagramDownloaderException):
    """Indicates an error during HTML parsing or if expected image elements cannot be found."""
    pass

class NetworkError(InstagramDownloaderException):
    """Indicates a network-related error during HTTP requests (e.g., connection error, timeout, server error)."""
    pass

class DownloadError(InstagramDownloaderException):
    """Indicates an error specifically during the image download phase (e.g., HTTP error on image URL)."""
    pass

class SaveError(InstagramDownloaderException):
    """Indicates an error during file saving (e.g., IO error, permissions issue)."""
    pass


def extract_image_urls(post_url: str) -> list[str]:
    """
    Extracts image URLs from a given public Instagram post URL.

    It sends a GET request to the URL, parses the HTML content, and looks for
    meta tags with `property="og:image"` to find image URLs.
    Note: This method is dependent on Instagram's current HTML structure for public posts
    and may not work if the structure changes or for private posts.

    Args:
        post_url: The string URL of the Instagram post.
                  Example: "https://www.instagram.com/p/Cxyz123abc/"

    Returns:
        A list of strings, where each string is a URL of an image found on the post.
        If multiple `og:image` tags are found, all corresponding URLs are returned.

    Raises:
        InstagramURLError: If the `post_url` is malformed (e.g., doesn't start with
                           "https://www.instagram.com/p/"), not a valid Instagram URL,
                           or if the post is not found (404), or other client-side HTTP errors occur.
        NetworkError: If there's a network issue like a connection error, timeout,
                      or an Instagram server-side error (5xx).
        ParsingError: If no `og:image` tags are found in the HTML (which might indicate
                      a private post, a post with no images, or a change in Instagram's
                      HTML structure), or if any other unexpected error occurs during HTML parsing.
    """
    # Validate the basic format of the Instagram post URL.
    if not post_url or not post_url.startswith("https://www.instagram.com/p/"):
        raise InstagramURLError(f"Invalid Instagram post URL format: {post_url}. URL must start with 'https://www.instagram.com/p/'.")

    try:
        headers = {
            # Using a common User-Agent to mimic a browser request. This can be crucial
            # for sites like Instagram that might block or serve different content to simple script-like requests.
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Timeout is set to 10 seconds to prevent indefinite hanging if the server is unresponsive.
        response = requests.get(post_url, headers=headers, timeout=10)
        # raise_for_status() will raise an HTTPError for 4xx (client) or 5xx (server) status codes.
        response.raise_for_status()

        # Parse the HTML content of the page.
        soup = BeautifulSoup(response.content, 'html.parser')
        image_urls = []

        # Instagram (and many other sites) use Open Graph (og) meta tags to specify
        # images for social media sharing. This is often a reliable way to get the main image(s)
        # for a public post.
        og_image_tags = soup.find_all('meta', property='og:image')
        for tag in og_image_tags:
            image_url = tag.get('content')
            if image_url: # Ensure the 'content' attribute exists and has a value.
                image_urls.append(image_url)
        
        if image_urls:
            return image_urls # Return the list of found image URLs.
        else:
            # If no og:image tags are found, it implies images are not specified in this standard way.
            # This could be due to various reasons: the post is private, it's a video post without a
            # specific og:image for a thumbnail, Instagram changed its HTML, or the page is not as expected.
            raise ParsingError(f"Could not find 'og:image' meta tags. The post may be private, contain no standard images, or Instagram's page structure might have changed for {post_url}.")

    except requests.exceptions.HTTPError as e:
        # Handle specific HTTP errors from the 'requests' library.
        if e.response.status_code == 404: # Not Found
            raise InstagramURLError(f"Instagram post not found (404 error) at URL: {post_url}")
        elif 400 <= e.response.status_code < 500: # Other client errors (e.g., 403 Forbidden, 400 Bad Request)
            raise InstagramURLError(f"Client error ({e.response.status_code}) accessing Instagram URL: {post_url}. This may be due to a private post, an invalid URL, or access restrictions.")
        elif 500 <= e.response.status_code < 600: # Server errors (e.g., 500 Internal Server Error, 503 Service Unavailable)
            raise NetworkError(f"Instagram server error ({e.response.status_code}) for URL: {post_url}. Please try again later.")
        else: # Other HTTP errors not covered above.
            raise NetworkError(f"An HTTP error occurred while fetching URL {post_url}: {e}")
    except requests.exceptions.ConnectionError as e:
        # Raised for network connectivity issues (e.g., DNS failure, refused connection).
        raise NetworkError(f"Connection error for {post_url}. Please check your internet connection: {e}")
    except requests.exceptions.Timeout as e:
        # Raised if the server does not send any data in the allotted time.
        raise NetworkError(f"Request timed out for {post_url}. The server might be too slow to respond or there might be a network issue: {e}")
    except requests.exceptions.RequestException as e: # A catch-all for other exceptions raised by 'requests'.
        raise NetworkError(f"A network request error occurred for URL {post_url}: {e}")
    except Exception as e: # Catch-all for any other unexpected errors (e.g., during BeautifulSoup parsing).
        # This helps in catching unforeseen issues during the parsing stage.
        raise ParsingError(f"An unexpected error occurred during HTML parsing for {post_url}: {e}")

def download_image(image_url: str, save_path: str) -> bool:
    """
    Downloads an image from a given URL and saves it to a specified local path.

    It streams the image content to handle potentially large files efficiently without
    consuming too much memory at once.

    Args:
        image_url: The string URL of the image to download.
        save_path: The string local file path where the image will be saved.
                   Example: "instagram_downloads/my_image.jpg"

    Returns:
        True if the image was downloaded and saved successfully.

    Raises:
        NetworkError: If a network problem occurs during image download (e.g., connection error, timeout).
        DownloadError: If a non-network error occurs during download (e.g., HTTP 404 for the image URL,
                       or other HTTP errors directly related to the image resource).
        SaveError: If an error occurs while trying to write the image file to `save_path`
                   (e.g., IOError due to permissions or invalid path).
    """
    try:
        headers = {
            # Standard User-Agent. While less critical for direct image URLs, it's good practice.
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # stream=True allows downloading the response content incrementally.
        # timeout is set for the request to avoid indefinite hangs.
        response = requests.get(image_url, headers=headers, stream=True, timeout=10)
        # Check if the request for the image itself was successful.
        response.raise_for_status() # Raises HTTPError for 4xx/5xx status on the image URL.

        # Open the file in binary write mode ('wb'). The directory for save_path should exist.
        with open(save_path, 'wb') as f:
            # iter_content downloads the file in chunks (8KB here), which is memory-efficient for large files.
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True # Indicates successful download and save.

    except requests.exceptions.HTTPError as e:
        # Specific HTTP errors related to accessing the image URL (e.g., image not found, access denied).
        raise DownloadError(f"HTTP error {e.response.status_code} while downloading image {image_url}: {e}")
    except requests.exceptions.ConnectionError as e:
        raise NetworkError(f"Connection error while downloading image {image_url}. Check your internet connection: {e}")
    except requests.exceptions.Timeout as e:
        raise NetworkError(f"Request timed out while downloading image {image_url}: {e}")
    except requests.exceptions.RequestException as e: # Catch-all for other 'requests' issues.
        raise DownloadError(f"Network request error while downloading image {image_url}: {e}")
    except IOError as e:
        # This typically happens if the save_path is invalid, the disk is full, or there are no write permissions.
        raise SaveError(f"File system error (IOError) saving image to {save_path}: {e}")
    except Exception as e: # Catch-all for other unexpected errors during the download process.
        raise DownloadError(f"An unexpected error occurred while trying to download image {image_url}: {e}")

def main():
    """
    Command-line interface for the Instagram Image Downloader.

    This function serves as the main entry point when the script is executed.
    It parses command-line arguments (expecting an Instagram post URL),
    then calls `extract_image_urls` to get image URLs from the post,
    and finally calls `download_image` for each URL to save the images.
    Images are saved into a directory named 'instagram_downloads' created in the
    current working directory.
    It handles and prints user-friendly messages for custom exceptions raised
    during the process, providing feedback on success or failure.
    """
    import argparse # For parsing command-line arguments.
    import os       # For file system operations like creating directories and joining paths.
    from urllib.parse import urlparse # For parsing URLs to generate filenames.

    # Setup command-line argument parser with a description and epilog for help message.
    parser = argparse.ArgumentParser(
        description="Download images from a public Instagram post URL. Images are saved in an 'instagram_downloads' directory.",
        epilog="Example: python downloader.py https://www.instagram.com/p/your_post_id/"
    )
    # Define the 'url' argument that the script will accept.
    parser.add_argument("url", help="The URL of the public Instagram post (e.g., https://www.instagram.com/p/xxxxxx/).")
    
    args = parser.parse_args()
    post_url = args.url
    image_urls = [] # Initialize to an empty list; will be populated by extract_image_urls.

    try:
        print(f"Attempting to extract image URLs from: {post_url}")
        image_urls = extract_image_urls(post_url)
        
        if not image_urls:
            # This case should ideally be covered by ParsingError if no og:image tags are found.
            # However, this check acts as a safeguard or if extract_image_urls logic changes
            # to return an empty list in some non-error scenarios (currently it raises ParsingError).
            print(f"No image URLs were successfully extracted for {post_url}. The post might have no recognizable images, or they are in a format not currently supported by this tool.")
            return # Exit if no URLs to process.

        print(f"Found {len(image_urls)} image(s). Starting download process...")

    # Handle exceptions that can occur during URL extraction.
    # These are caught here to provide user-friendly messages directly from the CLI.
    except InstagramURLError as e:
        print(f"Error: The provided Instagram URL is invalid or the post could not be accessed. Details: {e}")
        return # Exit the script.
    except ParsingError as e:
        print(f"Error: Could not find or parse images from the provided URL. This might be due to a private post, no images, or changes in Instagram's page structure. Details: {e}")
        return
    except NetworkError as e:
        print(f"Error: A network problem occurred while trying to fetch post details. Please check your connection and Instagram's status. Details: {e}")
        return
    except InstagramDownloaderException as e: # Catch any other specific custom exceptions from the app.
        print(f"An application error occurred: {e}")
        return
    except Exception as e: # Catch any other unexpected non-custom exceptions.
        print(f"A critical unexpected error occurred during URL extraction: {e}") # Consider logging `e` for debugging in a real app.
        return

    # Define the download directory name. This will be created in the CWD.
    download_dir = "instagram_downloads"
    # Create the download directory if it doesn't already exist.
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
            print(f"Created download directory: {download_dir}")
        except OSError as e: # Handles errors like permission issues or invalid directory names.
            print(f"Error: Could not create download directory '{download_dir}'. Reason: {e}")
            return # Cannot proceed if download directory can't be created.

    successful_downloads = 0
    # Loop through each extracted image URL and attempt to download it.
    for i, img_url in enumerate(image_urls):
        try:
            # Attempt to generate a somewhat meaningful filename from the image URL.
            # This uses the last part of the URL's path.
            parsed_url = urlparse(img_url)
            filename_base = os.path.basename(parsed_url.path)
            
            # Basic validation and fallback for filename.
            # If the parsed filename is empty or doesn't seem to have an extension,
            # create a generic sequential filename.
            if not filename_base or '.' not in filename_base: 
                filename_base = f"image_{i+1}.jpg" # Default filename (e.g., image_1.jpg).
            else:
                # Ensure a common image extension. If the original extension is unusual or missing,
                # default to .jpg. This is a simple heuristic.
                name, ext = os.path.splitext(filename_base)
                if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    filename_base = name + ".jpg" 
            
            # Construct the full save path for the image.
            save_path = os.path.join(download_dir, filename_base)
            
            print(f"Downloading image {i+1} of {len(image_urls)}: {img_url}...")
            # download_image will return True on success or raise an exception on failure.
            if download_image(img_url, save_path): 
                print(f"Successfully downloaded and saved: {save_path}")
                successful_downloads += 1
            
        # Handle exceptions that can occur during the download or saving of a single image.
        # This allows the loop to continue trying to download other images if one fails.
        except DownloadError as e:
            print(f"Error: Failed to download image {img_url}. Details: {e}")
        except SaveError as e:
            print(f"Error: Failed to save image {filename_base} (from {img_url}). Details: {e}")
        except NetworkError as e: 
            print(f"Error: A network problem occurred while downloading {img_url}. Details: {e}")
        except InstagramDownloaderException as e: # Catch other custom app errors related to this image.
            print(f"Application error processing image {img_url}: {e}")
        except Exception as e: # Catch any other non-custom, unexpected errors for this specific image.
            print(f"An unexpected error occurred while processing image {img_url}: {e}")

    # Print a summary of the download process to the user.
    print(f"\n--- Download Summary ---")
    print(f"Successfully downloaded {successful_downloads} of {len(image_urls)} image(s) to the '{download_dir}' directory.")
    if successful_downloads < len(image_urls):
        print(f"{len(image_urls) - successful_downloads} image(s) could not be downloaded due to errors. Please check the messages above for details.")

if __name__ == '__main__':
    # This standard Python construct ensures that main() is called only when the script
    # is executed directly (e.g., `python downloader.py ...`), not when it's imported as a module.
    main()
