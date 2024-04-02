import requests
from bs4 import BeautifulSoup
from time import sleep
import json


def load_json(json_file_path):
    """
    Import data from a JSON file.
    """
    with open(json_file_path, "r", encoding='utf-8') as json_file:
        return json.load(json_file)


def write_json(json_file_path, data):
    """
    Write data to a JSON file.
    """
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)


def crawl_google_scholar():
    """
    Record data from Google Scholar based on queries and write the results to a JSON file
    """
    # An HTTP request header is being set to mimic a request sent by a browser.
    headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/105.0.0.0 Safari/537.36 "
    }

    # Initialize counting variables for the statistics.
    total_queries = 0
    total_results = 0
    total_links = 0
    total_pdf_links = 0
    queries_data = []

    # Load the queries from a JSON file.
    try:
        queries = load_json("gs_queries.json")
    except Exception as e:
        print(f"Error loading queries: {e}")
        return

    # Iterate over queries and perform actions for each query.
    for query in queries:
        total_results_query = 0
        total_links_query = 0
        max_items = query["max_items"]

        # Set up the data structure to store query results.
        query_data = {
            "query_metadata": query,
            "query_link_statistics": {},
            "query_results": [],
        }

        params = query["params"]

        # Fetch data until the maximum of recorded items is reached.
        while total_results_query < max_items:
            try:
                # Add a timeout parameter to the request
                response = requests.get(params["base"], headers=headers, params=params, timeout=10)
                response.raise_for_status()
                html = response.text
                soup = BeautifulSoup(html, "lxml")

                # Parse HTML content using BeautifulSoup and extract relevant data.
                for result in soup.select(".gs_r.gs_or.gs_scl"):
                    if total_results_query >= max_items:
                        break

                    # Try to record relevant data such as title, title link and publication information.
                    try:
                        title = result.select_one(".gs_rt").text
                        # Remove specific prefixes from the title and trim whitespace.
                        prefixes = ["[CITAT][C]", "[PDF][PDF]", "[BOK][B]", "[HTML][HTML]"]
                        for prefix in prefixes:
                            if title.startswith(prefix):
                                title = title[len(prefix):].strip()
                                break
                    except TypeError:
                        title = None

                    try:
                        title_link = result.select_one(".gs_rt a")["href"]
                    except TypeError:
                        title_link = None

                    try:
                        publication_info = result.select_one(".gs_a").text
                    except TypeError:
                        publication_info = None

                    try:
                        snippet = result.select_one(".gs_rs").text
                    except TypeError:
                        snippet = None

                    try:
                        cited_by = result.select_one("#gs_res_ccl_mid .gs_nph+ a")["href"]
                    except TypeError:
                        cited_by = None

                    try:
                        doc_type = result.select_one(".gs_ctg2").text.strip("[]")
                        if doc_type == "PDF":
                            total_links += 1
                            total_links_query += 1
                            total_pdf_links += 1
                    except AttributeError:
                        doc_type = None
                    try:
                        doc_link = result.select_one(".gs_or_ggsm a:nth-child(1)")["href"]
                    except TypeError:
                        doc_link = None

                    total_results += 1
                    total_results_query += 1

                    # Construct the data structure to record extracted data.
                    result_data = {
                        "title": title,
                        "title_link": title_link,
                        "publication_info": publication_info,
                        "snippet": snippet,
                        "cited_by": f"https://scholar.google.com{cited_by}" if cited_by else None,
                        "page": params["start"] // 10,
                        "doc_type": doc_type,
                        "doc_link": doc_link
                    }

                    query_data["query_results"].append(result_data)

                    # Print the title of each recorded document.
                    print(f"Document recorded: {result_data['title']}")

                if total_results_query >= max_items:
                    break

                params["start"] += 10

                # Wait inbetween requests to lessen the load on the server.
                sleep(3)

            except requests.exceptions.ConnectTimeout:
                print("Connection timed out. Trying again...")
                sleep(5)  # Increase sleep time if necessary
                continue
            except requests.exceptions.HTTPError as e:
                print(f"HTTP error occurred: {e}")
                break
            except requests.exceptions.RequestException as e:
                print(f"Error during requests to {params['base']}: {e}")
                break

        # Store link statistics.
        query_data["query_link_statistics"] = {
            'total_results_query': total_results_query,
            'total_pdf_links_query': total_links_query,
        }
        queries_data.append(query_data)
        total_queries += 1

    # Compile query results and save them to a JSON file.
    try:
        json_file_path = "gs_search_results.json"
        queries_results = {
            "total_queries": total_queries,
            "total_results": total_results,
            "total_pdf_links": total_pdf_links,
            "queries_data": queries_data
        }

        write_json(json_file_path, queries_results)
        print(f"The query results have been saved to {json_file_path}.")
    except Exception as e:
        print(f"Error saving query results: {e}")


if __name__ == "__main__":
    crawl_google_scholar()
