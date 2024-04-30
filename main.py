# main.py
import asyncio
from webscraper.quick_scrapes.parse_sample import get_text_file_paths, ContentExtractor
from webscraper.quick_scrapes.quick_scraper import main

print(f"This is the quick scraper app for AI Matrix Engine")


# This scrapes and also runs multiple different parsers. Don't be confused by all of the print statements. It's multiple different parse logic tests.
async def quick_scrape_and_parse():
    url = "https://www.dermstore.com/skinceuticals-c-e-ferulic-with-15-l-ascorbic-acid-vitamin-c-serum-30ml/11289609.html"
    options = ['get_image_links', 'get_main_headers', 'extract_content_by_headers', 'get_tables', 'get_filtered_images']

    result = asyncio.run(main(url, options, task='scrape', text_file='../../soup.txt'))

    return result


# This is set up so that you can test parsing previous scrapes.
# You can simply provide the number '0' to get the last scrape, or use 1, 2, 3, etc. for previous ones.
# Each new scrape is saved to a list that allows this to always work.
async def parse_last_scrape_again():
    text_file_paths = [
        # If you have a text file, you can put it here, but it's not required, since it saves the soup for you automatically.
    ]

    if not text_file_paths:
        text_file_paths = get_text_file_paths()

    extractor = ContentExtractor()

    print(f"Opening last Text Entry")

    # 0 for the last scrape, or 1, 2, 3, etc. for previous ones.
    extractor.load_soup_from_text(text_file_paths[0])

    # Comment out the other one and use this, if you want.
    # use_local_html_file()

if __name__ == "__main__":
    # asyncio.run(quick_scrape_and_parse())
    asyncio.run(parse_last_scrape_again())
