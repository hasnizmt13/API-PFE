import re
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .utils import create_data_model
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

@require_http_methods(["GET"])  # Décorez la vue pour n'accepter que les requêtes GET
def calculate_distance(request):
    addresses_str = request.GET.get('addresses', '')
    addresses = re.split(r',(?=\S)', addresses_str)
    num_vehicles = int(request.GET.get('num_vehicles', 1))
    vehicle_id = request.GET.get('vehicle_id', None)  # Récupérer l'ID du véhicule de la requête
    if vehicle_id is not None:
        vehicle_id = int(vehicle_id)  # Convertir en entier si présent

    # Création des données pour le problème de routage
    data =create_data_model(addresses, num_vehicles)


    # Création du gestionnaire d'index de routage et du modèle de routage
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), data["num_vehicles"], data["depot"])
    routing = pywrapcp.RoutingModel(manager)

    # Création et enregistrement d'un callback de transit pour le calcul des distances
    def distance_callback(from_index, to_index):
        """Renvoie la distance entre deux nœuds."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Ajout de la contrainte de distance
    dimension_name = "Time"
    routing.AddDimension(
        transit_callback_index,
        0,  # slack
        6000,  # Duree maximale de parcours pour un véhicule
        True,  # cumul de temps à zéro au départ
        dimension_name
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Configuration de l'heuristique de la première solution
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Activation de la recherche locale guidée
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )

    # Temps limite raisonnable pour la recherche (10 secondes ici)
    search_parameters.time_limit.FromSeconds(10)

    # Résolution du problème de routage
    solution = routing.SolveWithParameters(search_parameters)
    if solution:
        return JsonResponse({
            'status': 'success',
            'data': extract_solution(data, manager, routing, solution, vehicle_id)
        })
    else:
        return JsonResponse({'status': 'failure', 'error': 'No solution found'}, status=400)

def extract_solution(data, manager, routing, solution, vehicle_id):
    """Extrait et formate la solution du problème de routage pour la réponse JSON."""
    total_distance = 0
    routes = []
    for vid in range(data["num_vehicles"]):
        if vehicle_id is not None and vehicle_id != vid:
            continue  # Ignorer les véhicules non demandés
        index = routing.Start(vid)
        route = {'vehicle_id': vid, 'route': []}
        route_distance = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            next_node_index = manager.IndexToNode(solution.Value(routing.NextVar(index)))
            route['route'].append({
                'from': data['addresses'][node_index],
                'to': data['addresses'][next_node_index],
                'duree': routing.GetArcCostForVehicle(index, solution.Value(routing.NextVar(index)), vid)
            })
            route_distance += routing.GetArcCostForVehicle(index, solution.Value(routing.NextVar(index)), vid)
            index = solution.Value(routing.NextVar(index))
        route['total_duree'] = route_distance
        total_distance += route_distance
        routes.append(route)
    return {'routes': routes, 'total_duree': total_distance}
