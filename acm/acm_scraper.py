import requests
import os
import re
import json


def load_json(json_file_path):
    """
    Load data from a JSON file.
    This function opens a JSON file, reads its content, and returns the loaded data.
    """
    with open(json_file_path, "r", encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        print(f"Importing successful. Imported queries:\n{json_data}")
        return json_data


def write_json(json_file_path, data):
    """
    Write data to a JSON file.
    This function takes data and writes it into a JSON file at the specified path.
    """
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)


def scrape_acm():
    """
    Scrape and download PDFs from links stored in a JSON file.
    The function handles file size limits, and retries for failed downloads.
    """
    # Set timeout and file size limits.
    timeout_in_s = 20
    max_file_size = 20 * 1024 * 1024  # 20 MB

    # Initialize counters.
    pdfs_amount = 0

    # Load search queries from a JSON file.
    try:
        queries = load_json("acm_search_results.json")
    except Exception as e:
        print(f"Error loading queries results: {e}")
        return

    # Set up directories for saving downloaded PDFs.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    pdfs_directory_name = "pdfs"
    acm_pdfs_directory_name = "acm_pdfs"
    pdfs_directory_path = os.path.join(parent_dir, pdfs_directory_name)
    acm_pdfs_directory_path = os.path.join(pdfs_directory_path, acm_pdfs_directory_name)

    # Create PDFs and acm_pdfs directories if they don't exist.
    if not os.path.exists(pdfs_directory_path):
        os.makedirs(pdfs_directory_path)
    if not os.path.exists(acm_pdfs_directory_path):
        os.makedirs(acm_pdfs_directory_path)

    try:
        # Iterate through each query and its results.
        for i, query in enumerate(queries["queries_data"], start=1):
            query_directory_name = f"query_{i}"
            query_directory_path = os.path.join(acm_pdfs_directory_path, query_directory_name)

            # Create query directory if it doesn't exist.
            if not os.path.exists(query_directory_path):
                os.makedirs(query_directory_path)

            downloaded_pdfs_count_query = 0

            for query_result in query["query_results"]:
                query_result['file_saved'] = False
                if query_result["doc_link"]:
                    doc_link = query_result["doc_link"]

                    # Attempt to download the PDF up to 3 times.
                    for attempt in range(3):
                        try:
                            # Set request headers.
                            headers = {'User-Agent': 'Mozilla/5.0'}
                            # Make the request.
                            response = requests.get(doc_link, timeout=timeout_in_s, headers=headers)

                            # Check for successful response and if file size is within limit.
                            if response.status_code == 200 and len(response.content) <= max_file_size:
                                original_filename = query_result["title"]
                                invalid_chars_pattern = re.compile(r'[\\/:*?"<>|]')
                                valid_filename = re.sub(invalid_chars_pattern, '_', original_filename)
                                valid_filename = valid_filename.strip()
                                filename = f'{valid_filename}.pdf'
                                filepath = os.path.join(query_directory_path, filename)

                                # Save file if it doesn't already exist.
                                if not os.path.exists(filepath):
                                    with open(filepath, 'wb') as f:
                                        f.write(response.content)
                                    query_result['file_saved'] = True
                                    pdfs_amount += 1
                                    downloaded_pdfs_count_query += 1
                                    print(f"Downloaded and saved: {filename}")
                                    break
                        except requests.exceptions.Timeout:
                            print(f"Request timed out for {doc_link}.")
                        except Exception as e:
                            print(f"Could not fetch PDF document from {doc_link}: {e}")
                            continue

            # Record statistics for each query.
            query["query_link_statistics"]["downloaded_pdfs_count_query"] = downloaded_pdfs_count_query
    except Exception as e:
        print(f"Error handling query results: {e}")
        return

    # Construct and save the final results.
    result_data = {
        "total_queries": queries["total_queries"],
        "total_results": queries["total_results"],
        "total_pdf_links": queries["total_pdf_links"],
        "total_downloaded_pdfs": pdfs_amount,
        "queries_data": queries["queries_data"]
    }

    json_file_path = "acm_search_results_updated.json"
    write_json(json_file_path, result_data)
    print(f"The updated query results have been saved to {json_file_path}.")


if __name__ == "__main__":
    scrape_acm()
