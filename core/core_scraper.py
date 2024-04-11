import requests
import json
import os
import re


def load_json(file_path):
    """
    Load data from a JSON file.
    """
    with open(file_path, 'r') as file:
        return json.load(file)


def write_json(file_path, data):
    """
    Write data to a JSON file.
    """
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def scrape_core():
    """
    Scrape and download PDFs from links stored in a JSON file.
    The function handles file size limits, duplicates and retries for failed downloads.
    """
    # Set timeout and file size limits.
    timeout_in_s = 20
    max_file_size = 20 * 1024 * 1024

    # Define request headers.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3'}

    # Load search results from a JSON file.
    try:
        data = load_json("core_search_results.json")
    except Exception as e:
        print(f"Error loading search results: {e}")
        return

    # Set up directories for saving downloaded PDFs.
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_directory = os.path.join(parent_dir, "pdfs")
    core_pdfs_directory = os.path.join(pdf_directory, "core_pdfs")

    # Create PDF and core_pdfs directories, if they don't exist.
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)
    if not os.path.exists(core_pdfs_directory):
        os.makedirs(core_pdfs_directory)

    # Counter for all successfully downloaded PDFs.
    total_pdfs_downloaded_count = 0

    # Iterate through each query data in the JSON file.
    for i, query_data in enumerate(data['queries_data'], start=1):
        query_pdfs_downloaded_count = 0  # Counter for successfully downloaded PDFs per query
        query_directory = os.path.join(core_pdfs_directory, f"query_{i}")

        # Create directory for each query, if it doesn't exist.
        if not os.path.exists(query_directory):
            os.makedirs(query_directory)

        # Iterate through each article in the query results.
        for article in query_data['query_results']:
            pdf_link = article.get('pdf_link')
            # Check if the PDF link is valid.
            if pdf_link and pdf_link.startswith('http'):
                try:
                    # Make the request to download the PDF.
                    response = requests.get(pdf_link, headers=headers, timeout=timeout_in_s)
                    # Check if the response is successful and within file size limit.
                    if response.status_code == 200 and len(response.content) <= max_file_size:
                        # Generate a valid filename.
                        filename = re.sub(r'[\\/:*?"<>|]', '_', article['title']).strip() + '.pdf'
                        filepath = os.path.join(query_directory, filename)

                        # Save file if it doesn't already exist.
                        if not os.path.exists(filepath):
                            with open(filepath, 'wb') as file:
                                file.write(response.content)
                            article['pdf_downloaded'] = True
                            query_pdfs_downloaded_count += 1
                            total_pdfs_downloaded_count += 1
                        else:
                            print(f"Duplicate file skipped: {filename}")
                            article['pdf_downloaded'] = False
                    else:
                        print(f"Failed to download PDF from {pdf_link}. Status Code: {response.status_code}")
                        article['pdf_downloaded'] = False
                except requests.exceptions.Timeout:
                    print(f"Request timed out for {pdf_link}")
                    article['pdf_downloaded'] = False
                except Exception as e:
                    print(f"Error downloading {pdf_link}: {e}")
                    article['pdf_downloaded'] = False
            else:
                print(f"No valid PDF link for article: {article['title']}")
                article['pdf_downloaded'] = False

        # Add downloaded PDF count for each query.
        if 'query_link_statistics' in query_data:
            query_data['query_link_statistics']['downloaded_pdfs_count_query'] = query_pdfs_downloaded_count

    # Reconstruct the data with pdfs_amount in the desired order.
    updated_data = {
        'total_queries': data['total_queries'],
        'total_results': data['total_results'],
        'total_pdf_links': data['total_pdf_links'],
        'total_downloaded_pdfs': total_pdfs_downloaded_count,
        'queries_data': data['queries_data']
    }

    # Write the results to a JSON file.
    write_json("core_search_results_updated.json", updated_data)


if __name__ == "__main__":
    scrape_core()
