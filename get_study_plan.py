import os
import time
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
)


def download_study_plan_pdf(url, output_path=None):
    """
    Download study plan PDF from a given URL using Selenium

    Args:
        url: URL of the webpage containing the study plan button
        output_path: Path where to save the PDF (optional)

    Returns:
        Path to the downloaded PDF file or None if download failed
    """
    # Setup Chrome options
    chrome_options = Options()

    # Set default download directory if provided
    if output_path:
        download_dir = os.path.dirname(os.path.abspath(output_path))
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,  # Don't open PDF in browser
        }
        chrome_options.add_experimental_option("prefs", prefs)
    else:
        # Use current directory as download location
        download_dir = os.path.abspath(os.getcwd())
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

    # Add additional options for better automation
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-notifications")

    # Setup WebDriver
    driver = None
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        # Wait for the page to load completely
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # List of possible selectors for the study plan download button
        button_selectors = [
            # Exact text match
            "//button[text()='Скачать учебный план']",
            # Contains text
            "//button[contains(text(), 'Скачать учебный план')]",
            # By class name
            "//button[contains(@class, 'ButtonSimple_button__JbIQ5')]",
            "//button[contains(@class, 'ButtonSimple_button_masterProgram__JK8b_')]",
            # Broader search for buttons with similar text
            "//button[contains(text(), 'учебный план')]",
            "//a[contains(text(), 'Скачать учебный план')]",
            "//a[contains(text(), 'учебный план')]",
            # Generic download buttons
            "//button[contains(text(), 'Скачать')]",
            "//a[contains(text(), 'Скачать')]",
        ]

        button = None
        used_selector = None

        # Try each selector until we find a matching element
        for selector in button_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    button = elements[0]
                    used_selector = selector
                    print(f"Found button using selector: {selector}")
                    print(f"Button text: {button.text}")
                    break
            except Exception as e:
                continue

        if not button:
            print("Could not find the download button")
            return None

        # Get the count of PDF files in the download directory before clicking
        pdf_files_before = set(
            f for f in os.listdir(download_dir) if f.lower().endswith(".pdf")
        )

        # Scroll to the button to make sure it's visible
        driver.execute_script("arguments[0].scrollIntoView();", button)
        time.sleep(1)  # Small delay after scrolling

        # Try to click the button
        try:
            # First try a regular click
            button.click()
        except ElementNotInteractableException:
            # If regular click fails, try JavaScript click
            driver.execute_script("arguments[0].click();", button)

        print("Clicked the download button")

        # Wait for the download to complete (max 30 seconds)
        download_wait_time = 30
        download_completed = False

        # First check if there's a direct redirect to PDF
        if driver.current_url.lower().endswith(".pdf"):
            print(f"Direct PDF URL: {driver.current_url}")

            # Use the current URL for direct download
            pdf_url = driver.current_url

            # Set up a new browser session to download the PDF
            download_options = Options()
            download_prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "plugins.always_open_pdf_externally": True,
            }
            download_options.add_experimental_option("prefs", download_prefs)

            pdf_driver = webdriver.Chrome(options=download_options)
            pdf_driver.get(pdf_url)

            # Wait for download to complete
            time.sleep(5)
            pdf_driver.quit()
            download_completed = True
        else:
            # Wait for new PDF file to appear in download directory
            start_time = time.time()
            while time.time() - start_time < download_wait_time:
                current_pdf_files = set(
                    f for f in os.listdir(download_dir) if f.lower().endswith(".pdf")
                )
                new_files = current_pdf_files - pdf_files_before

                if new_files:
                    download_completed = True
                    print(f"New PDF file(s) detected: {new_files}")
                    break

                time.sleep(1)

        # If no new file is detected, look for a download link that might have appeared
        if not download_completed:
            print(
                "No download detected. Looking for download links that may have appeared..."
            )

            # Try to find PDF links that might have appeared after clicking
            pdf_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")

            if pdf_links:
                pdf_url = pdf_links[0].get_attribute("href")
                print(f"Found PDF link: {pdf_url}")

                # Navigate to the PDF URL
                driver.get(pdf_url)
                time.sleep(5)  # Wait for download to start

                # Check again for new PDF files
                current_pdf_files = set(
                    f for f in os.listdir(download_dir) if f.lower().endswith(".pdf")
                )
                new_files = current_pdf_files - pdf_files_before

                if new_files:
                    download_completed = True
                    print(f"New PDF file(s) detected after following link: {new_files}")

        # If download still not detected, check for any new PDFs and page changes
        if not download_completed:
            # One last check for new files
            current_pdf_files = set(
                f for f in os.listdir(download_dir) if f.lower().endswith(".pdf")
            )
            new_files = current_pdf_files - pdf_files_before

            if new_files:
                download_completed = True
                print(f"New PDF file(s) detected: {new_files}")
            else:
                print("No PDF download detected.")
                print(f"Current URL after clicking: {driver.current_url}")

                # Check if we're now on a PDF page
                if driver.current_url.lower().endswith(".pdf"):
                    print(f"Redirected to PDF URL: {driver.current_url}")

                    # Handle direct PDF URL differently
                    pdf_url = driver.current_url
                    filename = os.path.basename(urllib.parse.urlparse(pdf_url).path)

                    if not filename:
                        filename = "study_plan.pdf"

                    # If output_path is provided, use it, otherwise create one based on the URL
                    final_path = (
                        output_path
                        if output_path
                        else os.path.join(download_dir, filename)
                    )

                    # Use a different approach to download the PDF from the URL
                    import requests

                    response = requests.get(pdf_url)
                    with open(final_path, "wb") as f:
                        f.write(response.content)

                    print(f"Downloaded PDF directly to: {final_path}")
                    return final_path

                return None

        # If download completed, get the path to the downloaded file
        if download_completed:
            # Find the most recently created PDF file
            current_pdf_files = [
                f for f in os.listdir(download_dir) if f.lower().endswith(".pdf")
            ]
            if not current_pdf_files:
                print("No PDF files found in download directory")
                return None

            # Sort by creation time (newest first)
            newest_pdf = max(
                [os.path.join(download_dir, f) for f in current_pdf_files],
                key=os.path.getctime,
            )

            # If output_path is provided, rename/move the file
            if output_path and newest_pdf != output_path:
                try:
                    os.rename(newest_pdf, output_path)
                    newest_pdf = output_path
                except Exception as e:
                    print(f"Error renaming file: {e}")

            print(f"PDF downloaded successfully to: {newest_pdf}")
            return newest_pdf

        return None

    except Exception as e:
        print(f"Error during PDF download: {e}")
        return None

    finally:
        # Always close the driver
        if driver:
            driver.quit()


def get_study_plan(url, output_path=None):
    """
    Simple wrapper function that takes a URL and returns the path to the downloaded PDF

    Args:
        url: URL of the webpage containing the study plan
        output_path: Optional path where to save the PDF

    Returns:
        Path to the downloaded PDF file or None if download failed
    """
    return download_study_plan_pdf(url, output_path)


if __name__ == "__main__":
    # Example usage
    url = input("Enter the URL of the webpage with the study plan: ")

    # Optional: specify output path
    custom_path = input("Enter output path (leave blank for default): ")
    output_path = custom_path if custom_path else None

    pdf_path = get_study_plan(url, output_path)

    if pdf_path:
        print(f"Success! The study plan PDF is saved at: {pdf_path}")
    else:
        print("Failed to download the study plan PDF.")
