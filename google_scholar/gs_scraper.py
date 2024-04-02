import requests
import os
import re
import json


def load_json(json_file_path):
    """
    Load data from a JSON file.
    """
    with open(json_file_path, "r", encoding='utf-8') as json_file:
        json_data = json.load(json_file)
        print(f"Importing successful. Imported queries:\n{json_data}")
        return json_data


def write_json(json_file_path, data):
    """
    Write data to a JSON file.
    """
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)


def scrape_gs():
    """
    Scrape and download PDFs from links stored in a JSON file.
    The function handles file size limits, and retries for failed downloads.
    """
    # Set timeout and file size limits.
    timeout_in_s = 20
    max_file_size = 20 * 1024 * 1024

    # Initialize counters.
    pdfs_amount = 0

    # Load search queries from a JSON file.
    try:
        queries = load_json("gs_search_results.json")
    except Exception as e:
        print(f"Error loading queries results: {e}")
        return

    # Set up directories for saving downloaded PDFs.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    base_directory_name = "pdfs"
    gs_pdfs_directory_name = "gs_pdfs"
    base_directory_path = os.path.join(parent_dir, base_directory_name)
    gs_pdfs_directory_path = os.path.join(base_directory_path, gs_pdfs_directory_name)

    # Create base PDF directory if it doesn't exist.
    if not os.path.exists(base_directory_path):
        os.makedirs(base_directory_path)

    # Create gs_pdfs directory if it doesn't exist.
    if not os.path.exists(gs_pdfs_directory_path):
        os.makedirs(gs_pdfs_directory_path)

    try:
        # Iterate through each query.
        for i, query in enumerate(queries["queries_data"], start=1):
            query_directory_name = f"query_{i}"
            query_directory_path = os.path.join(gs_pdfs_directory_path, query_directory_name)

            # Create directory for the query if it doesn't exist.
            if not os.path.exists(query_directory_path):
                os.makedirs(query_directory_path)

            downloaded_pdfs_count_query = 0  # Counter for downloaded PDFs per query

            # Iterate through each query result.
            for query_result in query["query_results"]:
                query_result['file_saved'] = False
                if query_result["doc_type"] == "PDF":
                    doc_link = query_result["doc_link"]

                    # Try downloading the PDF up to 3 times.
                    for attempt in range(3):
                        try:
                            # Set request headers.
                            headers = {
                                "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                                              "like Gecko) Chrome/105.0.0.0 Safari/537.36 "
                            }
                            # Make the request.
                            r = requests.get(doc_link, timeout=timeout_in_s, headers=headers)

                            # Check for successful response and if file size is within limit.
                            if r.status_code == 200 and len(r.content) <= max_file_size:
                                original_filename = query_result["title"]
                                invalid_chars_pattern = re.compile(r'[\\/:*?"<>|]')
                                valid_filename = re.sub(invalid_chars_pattern, '_', original_filename)
                                valid_filename = valid_filename.strip()
                                filename = valid_filename
                                filepath = os.path.join(query_directory_path, f'{filename}.pdf')

                                # Save file if it doesn't already exist.
                                if not os.path.exists(filepath):
                                    with open(filepath, 'wb') as f:
                                        f.write(r.content)
                                    query_result['file_saved'] = True
                                    pdfs_amount += 1
                                    downloaded_pdfs_count_query += 1
                                    break
                        except requests.exceptions.Timeout:
                            if attempt == 2:
                                print("Request timed out while fetching PDF document.")
                        except Exception as e:
                            if attempt == 2:
                                print(f"Could not fetch PDF document: {e}")
                            continue

            # Record statistics for each query.
            query["query_link_statistics"]["downloaded_pdfs_count_query"] = downloaded_pdfs_count_query
    except Exception as e:
        print(f"Error handling query results: {e}")
        return

    # Construct a dictionary and save the final results.
    result_data = {
        "total_queries": queries["total_queries"],
        "total_results": queries["total_results"],
        "total_pdf_links": queries["total_pdf_links"],
        "total_downloaded_pdfs": pdfs_amount,
        "queries_data": queries["queries_data"]
    }

    # Write the final results to a JSON file.
    json_file_path = "gs_search_results_updated.json"
    write_json(json_file_path, result_data)


if __name__ == "__main__":
    scrape_gs()
