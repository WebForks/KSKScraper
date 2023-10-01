import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urlparse
import time
import tarfile
from datetime import datetime

# nohup python -u kskscraper.py > output.log 2>&1 &
# tail -f output.log
# ps aux | grep kskscraper.py

json_folder = "kskmoejson"
starting_page = 1

start_time = time.time()
current_datetime = datetime.now()
print(current_datetime)

# Make a GET request to the website
url = 'https://ksk.moe/browse'
response = requests.get(url)
time.sleep(3)

# Create a folder for JSON files
if not os.path.exists(json_folder):
    os.makedirs(json_folder)

# open txt file that has the first downloaded doujin

# Get last page to scrape
soup = BeautifulSoup(response.text, 'html.parser')
last_page_link = soup.find('a', title='Go to the last page')
href = last_page_link['href']
last_page = href.split("/")[-1]

for i in range(starting_page, int(last_page) + 1):
    # go to initial page and send a request
    url = f"https://ksk.moe/browse/page/{i}"
    print("Page:", i, "----------------------------------------------------------------------------------------------------------------------------------------------------------------")
    response = requests.get(url)
    time.sleep(1)
    soup = BeautifulSoup(response.text, 'html.parser')

    # get list of all links to doujin on the current page
    bookmark_links = soup.find_all('a', rel='bookmark')
    doujin_list = [link['href'] for link in bookmark_links]

    page_data = {}

    # iterate through the links to doujin gotten from the current page
    for x in doujin_list:
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                # gets the doujin page and finds the Title
                response = requests.get("https://ksk.moe" + x)
                time.sleep(1)
                soup = BeautifulSoup(response.content, "html.parser")
                metadata_section = soup.find("section", id="metadata")

                h2_tag = metadata_section.find("h2")
                Title = h2_tag.text.strip()
                print(Title)

                # store title, artist, metadata, length, tag, size original, size resampled

                # Gets the title
                h1_tag = metadata_section.find("h1")
                if h1_tag:
                    Title_Json = h1_tag.text.strip()
                else:
                    Title_Json = Title
                    

                # Gets the artist
                artist_link = soup.find("a", href=lambda href: href and "/artists/" in href)
                if artist_link:
                    span_tag = artist_link.find("span")
                    Artist_Json = span_tag.text.strip()
                else:
                    Artist_Json = ""
                    

                # Gets the metadata
                metadata = soup.find("a", rel="nofollow noopener")
                if metadata:
                    span_tag = metadata.find("span")
                    Metadata_Json = span_tag.text.strip()
                else:
                    Metadata_Json = ""
                    

                # Gets the length
                target_strong = soup.find("strong", string="Length")
                if target_strong:
                    target_span = target_strong.find_next("span")
                    int_pages = target_span.text.strip()
                    string_length = int_pages.replace("Pages", "")
                    Length_Json = int(string_length)
                else:
                    Length_Json = 1
                    

                # Gets the tags
                strong_tag = soup.find("strong", string="Tag")
                if strong_tag:
                    Tags_Json = []
                    if strong_tag:
                        a_tags = strong_tag.find_all_next("a", href=lambda href: href and "/tags/" in href)
                        for a_tag in a_tags:
                            span_tag = a_tag.find("span")
                            if span_tag:
                                span_text = span_tag.text
                                Tags_Json.append(span_text)
                else:
                    Tags_Json = []
                    

                # Gets the size Original
                target_strong = soup.find("strong", string="Size (Ori.)")
                target_span = target_strong.find_next("span")
                OriginalSize_Json = target_span.text.strip()

                # Gets the size Resampled
                target_strong = soup.find("strong", string="Size (Res.)")
                target_span = target_strong.find_next("span")
                ResampledSize_Json = target_span.text.strip()

                # Create json file if it doesn't exist and send to json file without overwriting existing data
                data = {
                        "Artist": Artist_Json,
                        "Metadata": Metadata_Json,
                        "Length": Length_Json,
                        "Tags": Tags_Json,
                        "OriginalSize": OriginalSize_Json,
                        "ResampledSize": ResampledSize_Json,
                        "Link": "https://ksk.moe" + x
                }

                page_data[Title_Json] = data


                # send post request in order to get response header (link to download files)
                post_url = x.replace("/view/", "/download/")
                postURL = "https://ksk.moe" + post_url

                original_button = soup.find("button", {"class": "original"})
                original_hash = original_button.get("value")

                resampled_button = soup.find("button", {"class": "resampled"})
                resampled_hash = resampled_button.get("value")

                original_data = {'hash': original_hash}
                original_response = requests.post(postURL, data=original_data, allow_redirects=False)
                resampled_data = {'hash': resampled_hash}
                resampled_response = requests.post(postURL, data=resampled_data, allow_redirects=False)


                # links to the original and resampled files
                original_download_link = original_response.headers.get('location')
                resampled_download_link = resampled_response.headers.get('location')


                # Define the folder name
                folder_name = "kskmoe"

                # Create the folder if it doesn't exist
                if not os.path.exists(folder_name):
                    os.makedirs(folder_name)


                original_file_downloaded = requests.get(original_download_link)
                resampled_file_downloaded = requests.get(resampled_download_link)
                time.sleep(6)

                # Extract the filename from the URL
                original_file_name = os.path.basename(urlparse(original_download_link).path)
                resampled_file_name = os.path.basename(urlparse(resampled_download_link).path)

                # Create the subfolder with the desired name
                subfolder_name = Title_Json
                subfolder_path = os.path.join(folder_name, subfolder_name)
                if not os.path.exists(subfolder_path):
                    os.makedirs(subfolder_path)

                # Get the file extension
                original_file_extension = os.path.splitext(original_file_name)[1]
                resampled_file_extension = os.path.splitext(resampled_file_name)[1]

                new_original_file_name = Title + " - Original" + original_file_extension
                new_resampled_file_name = Title + " - Resampled" + original_file_extension

                # Define the path to save the file in the subfolder with the original name and extension
                new_original_file_path = os.path.join(subfolder_path, new_original_file_name)
                new_resampled_file_path = os.path.join(subfolder_path, new_resampled_file_name)

                with open(new_original_file_path, "wb") as file:
                    file.write(original_file_downloaded.content)

                with open(new_resampled_file_path, "wb") as file:
                    file.write(resampled_file_downloaded.content)

                break  # Exit the retry loop if no error occurred
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                retry_count += 1
                print(f"Retrying in 1 minute... (Attempt {retry_count}/{max_retries})")
                time.sleep(60)
        else:
            print(f"Error occurred for link '{x}' {max_retries} times in a row. Skipping...")

    # Create a JSON file for the current page
    json_file_path = os.path.join(json_folder, f"page_{i}.json")
    with open(json_file_path, "w") as json_file:
        json.dump(page_data, json_file, indent=4)


def create_tar_archive(folder_path, archive_name):
    print("Creating tar archive...")
    with tarfile.open(archive_name, 'w') as tar:  # Change the open mode to 'w'
        tar.add(folder_path, arcname='')
    print("Tar archive created successfully!")

# Usage example
folder_path = './kskmoe'
archive_name = 'kskmoe.tar'
create_tar_archive(folder_path, archive_name)


print("Done")

end_time = time.time()
elapsed_time = end_time - start_time
print(f"Elapsed Time: {elapsed_time} seconds.")
