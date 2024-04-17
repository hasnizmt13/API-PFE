import json
from urllib.parse import urlencode

import requests

def create_data():
    """Creates the data for the routing problem."""
    data = {
        'API_key': 'AIzaSyACNlnN4eWz6z4ExnKtNFPkSiAhu0R2YIg',
        'addresses': [
            '2+Rue+Alexis+de+Tocqueville,+78000+Versailles',
            'UVSQ+-+UFR+des+Sciences+-+Universite+Paris-Saclay,+45+Av.+des+Etats+Unis,+78000+Versailles',
            'Résidence+Ecla+Paris+Massy-Palaiseau',
            'Château+de+Versailles',
            '67+Av.+de+Saint-Cloud,+78000+Versailles',
            '21+Pl.+du+Grand+Ouest,+91300+Massy',
            '67+Av.+Pablo+Picasso,+92000+Nanterre'

        ]
    }
    return data

def create_distance_matrix(data):
    """Creates a distance matrix from the addresses in the data dictionary."""
    addresses = data["addresses"]
    API_key = data["API_key"]
    max_elements = 100
    num_addresses = len(addresses)
    max_rows = max_elements // num_addresses
    q, r = divmod(num_addresses, max_rows)
    distance_matrix = []
    
    for i in range(q):
        origin_addresses = addresses[i * max_rows: (i + 1) * max_rows]
        response = send_request(origin_addresses, addresses, API_key)
        distance_matrix += build_distance_matrix(response)
    
    if r > 0:
        origin_addresses = addresses[q * max_rows: q * max_rows + r]
        response = send_request(origin_addresses, addresses, API_key)
        distance_matrix += build_distance_matrix(response)
    return distance_matrix

def send_request(origin_addresses, destination_addresses, API_key):
    """Sends a request to the Google Maps Distance Matrix API."""
    def build_address_str(addresses):
        """Builds a string of addresses separated by '|'. Used for API request."""
        return '|'.join(addresses)

    endpoints = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    params = {
        'origins': build_address_str(origin_addresses),
        'destinations': build_address_str(destination_addresses),
        'key': API_key,
        'units': 'metric'
    }
    response = requests.get(endpoints, params=params)
    return response.json()

def build_distance_matrix(response):
    """Builds a matrix of distances from the JSON response."""
    distance_matrix = []
    for row in response['rows']:
        row_list = [element['distance']['value'] if 'distance' in element else float('inf') for element in row['elements']]
        distance_matrix.append(row_list)
    return distance_matrix


def create_data_model():
    """Stores the data for the problem."""
    data = create_data()
    distance_matrix = create_distance_matrix(data)
    data["distance_matrix"] = distance_matrix
    data["num_vehicles"] = 4
    data["depot"] = 0
    return data
