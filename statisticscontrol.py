from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException
import time
import pandas as pd
from urllib.parse import urlparse
from termcolor import colored
import os

def alternate_test(ublock_path, website_list, num_tests=10, restart_interval=50):
    results = {}
    iteration_count = 0  # Initialize iteration count

    def setup_driver(options, position=None):
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(60)
        if position:
            driver.set_window_position(*position)
        return driver

    options1 = Options()
    options2 = Options()

    # Set up two browser windows side by side
    driver1 = setup_driver(options1, position=(0, 0))
    driver1.install_addon(ublock_path, temporary=True)

    driver2 = setup_driver(options2, position=(driver1.get_window_rect()['width']/2, driver1.get_window_rect()['height']/4))

    for site in website_list:
        load_times1 = []
        load_times2 = []
        results[site] = {'With uBlock': [], 'Without uBlock': []}

        for i in range(num_tests):
            iteration_count += 1  # Increment iteration count

            try:
                if iteration_count % restart_interval == 0:
                    driver1.quit()
                    driver2.quit()
                    driver1 = setup_driver(options1, position=(0, 0))
                    driver1.install_addon(ublock_path, temporary=True)
                    driver2 = setup_driver(options2, position=(driver1.get_window_rect()['width']/2, driver1.get_window_rect()['height']/4))

                try:
                    start_time1 = time.time()
                    driver1.get(f"https://{site}")
                    WebDriverWait(driver1, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    load_time = (time.time() - start_time1) * 1000
                    load_times1.append(load_time)
                except WebDriverException as e:
                    load_times1.append(60000)  # Append timeout value if an error occurs
                    print(colored(f"Iteration {iteration_count}: uBlock client timeout on {site}. Restarting WebDriver.", 'yellow'))
                    driver1.quit()
                    driver1 = setup_driver(options1, position=(0, 0))
                    driver1.install_addon(ublock_path, temporary=True)

                try:
                    start_time2 = time.time()
                    driver2.get(f"https://{site}")
                    WebDriverWait(driver2, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    load_time = (time.time() - start_time2) * 1000
                    load_times2.append(load_time)
                except WebDriverException as e:
                    load_times2.append(60000)  # Append timeout value if an error occurs
                    print(colored(f"Iteration {iteration_count}: Non-uBlock client timeout on {site}. Restarting WebDriver.", 'yellow'))
                    driver2.quit()
                    driver2 = setup_driver(options2, position=(driver1.get_window_rect()['width']/2, driver1.get_window_rect()['height']/4))

                # Clear browser state for both drivers
                driver1.execute_script("window.localStorage.clear();")
                driver1.delete_all_cookies()
                driver2.execute_script("window.localStorage.clear();")
                driver2.delete_all_cookies()

                # Verbose output
                if load_times1[-1] < load_times2[-1]:
                    print(colored(f"{iteration_count}/{num_tests}: uBlock client was faster on {site}", 'green'))
                else:
                    print(colored(f"{iteration_count}/{num_tests}: Non-uBlock client was faster on {site}", 'red'))
            
            except WebDriverException as e:
                print(colored(f"Iteration {i+1} on {site} encountered an error: {e}. Restarting WebDriver.", 'red'))
                driver1.quit()
                driver2.quit()
                driver1 = setup_driver(options1)
                driver1.install_addon(ublock_path, temporary=True)
                driver2 = setup_driver(options2)
                continue  # Skip this iteration and continue with the next one

        # Save the current site's results to Excel after each site is completed
        excel_file_name = f'load_times_details_iteration_{num_tests}.xlsx'
        # Check if the file already exists
        if os.path.exists(excel_file_name):
            book = pd.ExcelWriter(excel_file_name, engine='openpyxl', mode='a')
        else:
            book = pd.ExcelWriter(excel_file_name, engine='openpyxl')

        with book as writer:
            domain = urlparse('http://' + site).netloc
            df = pd.DataFrame({
                'Load Time With uBlock (ms)': load_times1,
                'Load Time Without uBlock (ms)': load_times2
            })
            # If the sheet does not exist, it will be created. If it exists, it will be overwritten.
            df.to_excel(writer, sheet_name=domain, index=False)
            writer._save()

        print(f"Data for {site} has been saved to {excel_file_name}")

    driver1.quit()
    driver2.quit()

# Path to the uBlock Origin .xpi file
ublock_path = r"ublock_origin-1.52.2.xpi"

# List of websites to test
websites = [
    # "google.com/search?q=tacos+near+me",
    "bing.com/search?q=tacos+near+me",
    "pinterest.com/search/pins/?q=tacos",
    "duckduckgo.com/?va=q&t=hc&q=tacos+near+me",

    "youtube.com",
    "amazon.com",
    "target.com/s?searchTerm=tacos&tref=typeahead%7Cterm%7Ctacos%7C%7C%7Chistory",
    "walmart.com/search?q=tacos",
    "yahoo.com",
    "reddit.com",
    "imdb.com",
    "twitch.tv",
    "tripadvisor.com/Search?q=tacos&ssrc=e&search",
    "etsy.com/search?q=tacos%20near%20me",
    "quora.com/search?q=tacos%20near%20me",
    "zillow.com/homes/for_sale/tacos-near-me_rb/",
    "booking.com/searchresults.html?ss=Las+Vegas%2C+United+States+of+America",
    "aliexpress.us/?gatewayAdapt=glo2usa",
    "weather.com",
    "apple.com",
    "stackoverflow.com/search?q=tacos+near+me&s=8bc580a2-5ea6-47ff-98f5-1c2eeba95440",
    "webmd.com",
    "store.steampowered.com",

    "msn.com/en-us/news",
    "cnn.com",
    "breitbart.com",
    "foxnews.com",
    "nytimes.com",
    "cnet.com",
    "bbc.com/news",
    "theguardian.com",
    "aljazeera.com",
    "reuters.com",
    "washingtonpost.com",
    "bloomberg.com",
    "wsj.com",
    "theatlantic.com",
    "npr.org",
    "news.vice.com",
    "politico.com",
    "axios.com",
    "espn.com",
    "nfl.com",
    "xda-developers.com",
    "techcrunch.com",
    "engadget.com",
    "investopedia.com/young-adults-are-running-out-of-cash-to-pay-emergency-expenses-8391317",
    "apnews.com/article/israel-hamas-war-news-11-6-2023-51286d15dddd77ae0dd7ea76ee52bc71",

    "wikipedia.org",
    "linkedin.com",
    "spotify.com",
    "netflix.com",
    # "paypal.com",
    "protonmail.com",
    "github.com",
    "medium.com",
    "coursera.org",
    "zoom.us",
    "signal.org",
    "vimeo.com",
    "trello.com",
    "basecamp.com",
    "discord.com",
    "weather.jaedynchilton.com",
    "time.gov",
    "edx.org",
    "khanacademy.org",
    "letu.edu"

]

# Run tests and collect results
alternate_test(ublock_path, websites, 50, 223)
