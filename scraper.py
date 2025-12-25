import requests
from bs4 import BeautifulSoup

def fetch_pokemon_data(name: str):
    # Construct the URL for the Pokémon
    url = f"https://pokemondb.net/pokedex/{name}"

    # Send a GET request to fetch the page content
    response = requests.get(url)

    # If the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve data for {name}")
        return None

    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Storing html sections to skip past ones that have already been parsed
    attribute_tables = soup.find_all('table', {'class': 'vitals-table'})

    # Extracting types from the "Type" section
    types = []

    if attribute_tables:
        type_section = attribute_tables[0].find('th', string="Type")
        if type_section:
            type_section = type_section.find_next('td')
            if type_section:
                # Extract all <a> tags within the "Type" section, which represent the types
                type_links = type_section.find_all('a', class_='type-icon')
                types = [type_.text.strip() for type_ in type_links][:2]  # Get up to two types

    # Extracting Base Stats (HP, Attack, Defense, etc.)
    base_stats = {}

    if attribute_tables:
        stats_section = attribute_tables[3].find('tbody')
        if stats_section:
            for row in stats_section.find_all('tr'):
                stat_name = row.find('th').text.strip() if row.find('th') else None
                stat_value = row.find('td', class_='cell-num')
                if stat_name and stat_value:
                    stat_value = stat_value.text.strip()
                    base_stats[stat_name] = int(stat_value)

    # Extracting Total BST from the <tfoot> section
    bst = None
    bst_section = soup.find('tfoot')
    if bst_section:
        bst_td = bst_section.find('td', class_='cell-num cell-total')
        if bst_td:
            bst = int(bst_td.text.strip())

    # Print the extracted data for testing
    # print("Types:", types)
    # print("Base Stats:", base_stats)
    # print("BST:", bst)

    return {"types": types, "base_stats": base_stats, "bst": bst}

# Test the scraper for Tepig
# pokemon_data = fetch_pokemon_data('tepig')
