import json
import requests
from bs4 import BeautifulSoup
from time import sleep


def get_query_url(query):
    """
    Construct the query URL for CORE based on the given query parameters.
    """
    base_url = query["params"]["base"]
    search_query = query["params"]["q"]
    page_number = query["params"]["page"]
    return f"{base_url}?q={search_query}&page={page_number}"


def parse_html(html, current_page):
    """
    Parse the HTML content of a CORE search results page and extract relevant information.
    """
    # Parse the HTML data and look for specific classes within the HTML.
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find_all('div', {'class': 'styles_search-results__2AZDM'})

    results = []

    # Iterate over the contents of the parsed HTML data.
    for article in articles:
        title = article.find('h3', {'class': 'styles-title-1k6Ib'}).get_text(strip=True)
        author_elements = article.find_all('span', {'itemprop': 'name'})
        authors = [author.get_text(strip=True) for author in author_elements]
        publication_date = article.find('dd', {'itemprop': 'datePublished'}).get_text(strip=True)
        pdf_link_tag = article.find('figure', {'class': 'styles-thumbnail-1xurx'}).find('a', href=True)
        pdf_link = pdf_link_tag['href'] if pdf_link_tag else "No PDF link found"

        result_data = {
            'title': title,
            'authors': authors,
            'publication_date': publication_date,
            'pdf_link': pdf_link,
            'page': current_page
        }
        results.append(result_data)

        # Print the title of each recorded document.
        print(f"Document recorded: {result_data['title']}")

    return results


def crawl_queries(file_path):
    """
    Crawl the CORE website based on queries loaded from a JSON file and save the results.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3'
    }

    # Load queries from a JSON file.
    try:
        with open(file_path, 'r') as file:
            queries = json.load(file)
    except Exception as e:
        print(f"Error loading queries: {e}")
        return

    all_queries_data = []
    total_queries = len(queries)
    total_results = 0
    total_pdf_links = 0

    # Iterate over the queries and perform actions for each query.
    for query in queries:
        max_items = query["max_items"]
        total_items_query = 0
        page = 0

        # Construct the data structure to store the results of each query.
        query_data = {
            "query_metadata": query,
            "query_link_statistics": {},
            "query_results": []
        }

        # Fetch data until the maximum number of results is obtained.
        while total_items_query < max_items:
            query["params"]["page"] = page + 1
            url = get_query_url(query)
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                page_results = parse_html(response.text, page)
                results_to_add = page_results[:max_items - total_items_query]
                query_data["query_results"].extend(results_to_add)
                total_items_query += len(results_to_add)
                total_pdf_links += sum(
                    1 for result in results_to_add if 'pdf_link' in result and result['pdf_link'] != "No PDF link found"
                )
                if total_items_query >= max_items:
                    break
            else:
                print(f"Failed to retrieve data from {url}")
                print("Status code:", response.status_code)
                print("Response text:", response.text)
            page += 1

            # Wait between requests in order to lessen the load on the server.
            sleep(1)

        # Calculate the link statistics.
        query_data["query_link_statistics"] = {
            'total_results_query': len(query_data["query_results"]),
            'total_pdf_links_query': sum(
                1 for result in query_data["query_results"] if 'pdf_link' in result
                and result['pdf_link'] != "No PDF link found"
            )
        }
        total_results += len(query_data["query_results"])
        all_queries_data.append(query_data)

    # Construct the data structure for the final result.
    result_data = {
        "total_queries": total_queries,
        "total_results": total_results,
        "total_pdf_links": total_pdf_links,
        "queries_data": all_queries_data
    }

    # Save the results to a JSON file.
    try:
        with open('core_search_results.json', 'w') as outfile:
            json.dump(result_data, outfile, indent=4)
        print("The query results have been saved to core_search_results.json.")
    except Exception as e:
        print(f"Error saving query results: {e}")


if __name__ == "__main__":
    crawl_queries('core_queries.json')
