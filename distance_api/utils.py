import json
from urllib.parse import urlencode

import requests
import os
from decouple import config

key=config('API_key')
print(key)
def create_data(addresses, num_vehicles):
    
    """Creates the data for the routing problem."""
    data = {
        'API_key': key,
        'addresses': addresses,
        'num_vehicles': num_vehicles
    }
    print(data)
    return data

def create_distance_matrix(data):
    """Creates a distance matrix from the addresses in the data dictionary."""
    print(data)
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
        row_list = [element['duration']['value'] if 'duration' in element else float('inf') for element in row['elements']]
        distance_matrix.append(row_list)
    return distance_matrix


def create_data_model(addresses, num_vehicles):
    """Stores the data for the problem."""
    data = create_data(addresses, num_vehicles)
    distance_matrix = create_distance_matrix(data)
    data["distance_matrix"] = distance_matrix
    data["num_vehicles"] = num_vehicles
    data["depot"] = 0
    return data
