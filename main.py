import requests
from bs4 import BeautifulSoup
from googlesearch import search
from urllib.parse import urlparse
import csv
import re
import time
import phonenumbers
from tqdm import tqdm

# Create a set to store unique domains
unique_domains = set()
data = []

# Define multiple phone number patterns using re
phone_number_patterns_re = [
    re.compile(r'تلفن:\s*([\d-]+)'),  
    re.compile(r'شماره تماس:\s*([\d-]+)'), 
    re.compile(r'021[\d-]+'), 
    re.compile(r'09[\d-]+'), 
    re.compile(r'تماس:\s*([\d-]+)'), 
    
]

address_patterns_re = [
    re.compile(r'آدرس\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),  
    re.compile(r'نشانی\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),
    re.compile(r'آدرس:\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),  
    re.compile(r'نشانی:\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),
    re.compile(r'ایران،:\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),
    re.compile(r'آدرس :\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),  
    re.compile(r'نشانی :\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),
    re.compile(r'بلوار\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),
    re.compile(r'تهران\s*([\u0600-\u06FF\s\d]+)', re.IGNORECASE),
]

# Regular expression pattern for removing non-digit characters from phone numbers
clean_phone_number_pattern = re.compile(r'\D')

# Initialize a timer
start_time = time.time()

# Option to filter domains
filter_domains = True  # Set to True to enable domain filtering

# Track the number of results fetched so far
total_fetched_results = 0

def is_valid_mobile(string):
    try:
        parsed_number = phonenumbers.parse(string, "IR")
        return phonenumbers.is_valid_number(parsed_number)
    except phonenumbers.phonenumberutil.NumberFormatException:
        return False

# Define the search query outside of the tqdm loop
search_query = "مطب دندان پزشکی تهران"

# Perform the Google search with tqdm progress bar
search_results = list(search(search_query, num= 100))
with tqdm(total=len(search_results), desc="Processing Websites", dynamic_ncols=True) as pbar:
    for result in search_results:
        try:
            response = requests.get(result)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                parsed_url = urlparse(result)
                domain_name = parsed_url.netloc

                if not filter_domains or (filter_domains and domain_name not in unique_domains):
                    unique_domains.add(domain_name)
                    title = soup.title.string.strip() if soup.title else "No title found"

                    # Initialize empty list to store phone numbers
                    phone_numbers = []

                    # Search for phone numbers using re
                    for phone_number_pattern_re in phone_number_patterns_re:
                        phone_number_matches_re = phone_number_pattern_re.findall(response.text)
                        phone_numbers.extend(phone_number_matches_re)

                    # Clean phone numbers by removing non-digit characters
                    phone_numbers = [clean_phone_number_pattern.sub('', number) for number in phone_numbers]

                    # Validate phone numbers using is_valid_mobile
                    valid_phone_numbers = [number for number in phone_numbers if is_valid_mobile(number)]

                    # Join valid phone numbers into a single string with a comma delimiter
                    phone_numbers_str = ', '.join(valid_phone_numbers)

                    # Initialize empty list to store addresses
                    addresses = []

                    # Search for addresses using re
                    for address_pattern_re in address_patterns_re:
                        address_matches_re = address_pattern_re.findall(response.text)
                        addresses.extend(address_matches_re)

                    data.append((domain_name, title, phone_numbers_str, addresses))
                    total_fetched_results += 1

                    pbar.update(1)  # Update the progress bar
        except Exception as e:
            print(f"An error occurred while processing {result}: {e}")

# Calculate and display the time spent
end_time = time.time()
time_elapsed = end_time - start_time
print(f"Time elapsed: {time_elapsed:.2f} seconds")

csv_filename = "website_data.csv"
with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(['Domain Name', 'Title', 'Phone Numbers', 'Addresses'])
    csv_writer.writerows(data)

print(f"Data saved to {csv_filename}")
