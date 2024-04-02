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


def construct_url(params):
    """
    Construct the URL for a given set of query parameters.
    """
    query_string = "&".join([f"{key}={params[key]}" for key in params if key != 'base'])
    return f"{params['base']}?{query_string}"


def crawl_acm_digital_library():
    """
    Scrape data from ACM Digital Library.
    """
    # Setting the request headers to mimic a browser request.
    headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/105.0.0.0 Safari/537.36 "
    }

    # Initializing variables to store statistics.
    total_queries = 0
    total_results = 0
    total_pdf_links = 0
    queries_data = []

    # Load queries from the specified JSON file.
    try:
        queries = load_json("acm_queries.json")
    except Exception as e:
        print(f"Error loading queries: {e}")
        return

    # Loop through each query to fetch and process data.
    for query in queries:
        total_results_query = 0
        total_pdf_links_query = 0
        max_items = query["max_items"]
        current_page = query["params"]["startPage"]

        # Create data structure to store results for each query.
        query_data = {
            "query_metadata": query,
            "query_link_statistics": {},
            "query_results": [],
        }

        # Set up parameters for the ACM query URL.
        params = query["params"].copy()

        # Fetch and parse data until the maximum items limit is reached.
        while total_results_query < max_items:
            url = construct_url(params)
            # Make an HTTP request to Google Scholar using the python library requests
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "lxml")

            # Check if the end of search results is reached.
            no_result_element = soup.select_one(".search-result__no-result")
            if no_result_element and "Your search did not return any results." in no_result_element.text:
                print("No more results for this query.")
                break

            # Extract relevant data from each search result.
            for result in soup.select(".issue-item__content-right"):
                if total_results_query >= max_items:
                    break

                title_element = result.select_one(".issue-item__title a")
                title = title_element.text if title_element else "No Title"
                title_link = f"https://dl.acm.org{title_element['href']}" if title_element else None

                publication_info_element = result.select_one(".issue-item__detail")
                publication_info = publication_info_element.text if publication_info_element else "No Publication Info"

                pdf_link_element = result.select_one("a[aria-label='PDF']")
                full_pdf_link = f"https://dl.acm.org{pdf_link_element['href']}" if pdf_link_element and 'href' in pdf_link_element.attrs else None

                authors = []
                for author in result.select("ul.rlist--inline li a[title]"):
                    if "/profile/" in author.get('href', ''):
                        authors.append(author.get('title'))

                if full_pdf_link:
                    total_pdf_links += 1
                    total_pdf_links_query += 1

                total_results += 1
                total_results_query += 1

                # Store extracted data.
                result_data = {
                    "title": title,
                    "title_link": title_link,
                    "publication_info": publication_info,
                    "authors": authors,
                    "doc_link": full_pdf_link
                }

                query_data["query_results"].append(result_data)
                print(f"Document recorded: {result_data['title']}")

            # Break out of the loop if maximum item limit is hit.
            if total_results_query >= max_items:
                break

            current_page += 1
            params["startPage"] = current_page
            # Wait inbetween requests to reduce the load on the server.
            sleep(1)

        # Store statistics for the current query.
        query_data["query_link_statistics"] = {
            'total_results_query': total_results_query,
            'total_pdf_links_query': total_pdf_links_query,
        }
        queries_data.append(query_data)
        total_queries += 1

    # Save  collected data to a JSON file.
    try:
        json_file_path = "acm_search_results.json"
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
    crawl_acm_digital_library()
