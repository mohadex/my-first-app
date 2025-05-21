# Instagram Image Downloader

A command-line tool to download images from public Instagram posts.

## Disclaimer

**Important:** This tool is intended for personal, educational, or research purposes only. Downloading content from Instagram may violate Instagram's Terms of Service. Users are solely responsible for ensuring they comply with all applicable terms, conditions, and copyright laws when using this tool. The developers of this tool are not responsible for any misuse. Always respect content creators' rights and Instagram's policies.

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1.  **Clone the repository (Optional):**
    If you have git installed, you can clone the repository:
    ```bash
    git clone <repository_url> 
    cd instagram_image_downloader
    ```
    Alternatively, you can download the source code (e.g., as a ZIP file) and extract it.

2.  **Install Dependencies:**
    Navigate to the project directory (`instagram_image_downloader`) and install the required Python packages using `requirements.txt`:
    ```bash
    python3 -m pip install -r requirements.txt
    ```

## Usage

To download images from an Instagram post, run the script from the command line, providing the URL of the Instagram post as an argument:

```bash
python3 downloader.py <INSTAGRAM_POST_URL>
```

For example:
```bash
python3 downloader.py https://www.instagram.com/p/Cxyz123abc/
```

Images will be saved in a directory named `instagram_downloads` created in the same directory where you run the script.

## Error Handling

The tool includes error handling for common issues such as:
- Invalid Instagram URLs
- Network problems (connection errors, timeouts)
- Posts not found or inaccessible (e.g., private posts, deleted content)
- Errors during image parsing or saving

User-friendly messages will be displayed in the console if an error occurs.

## Limitations

-   **Relies on `og:image` tags:** The current version primarily extracts images by looking for `<meta property="og:image">` tags in the HTML of the Instagram post. This method works for many public posts but might not capture all images, especially in complex carousels or if Instagram significantly changes its HTML structure.
-   **Public Posts Only:** The tool is designed for publicly accessible Instagram posts. It will likely not work for private posts or content requiring login.
-   **Dynamic Content:** Instagram loads content dynamically. While `og:image` tags are usually present in the initial HTML for main images, more complex scraping techniques (like using a headless browser) would be needed for comprehensive coverage of all scenarios (e.g., all images in a carousel, images loaded by JavaScript after initial page load).

## Running Tests

Unit tests are included to ensure the core functionality works as expected. To run the tests, navigate to the `instagram_image_downloader` directory and use the following command:

```bash
python3 -m unittest tests/test_downloader.py
```

This will discover and run tests located in the `tests/test_downloader.py` file.
File 'instagram_image_downloader/README.md' created successfully.
