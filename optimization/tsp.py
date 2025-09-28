from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math

class RouteOptimizer:
    def __init__(self):
        self.manager = None
        self.routing = None
        self.solution = None
    
    def calculate_distance(self, coord1, coord2):
        """Calculate distance between two coordinates using Haversine formula"""
        lat1, lon1 = coord1['latitude'], coord1['longitude']
        lat2, lon2 = coord2['latitude'], coord2['longitude']
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        return c * r
    
    def create_distance_matrix(self, coordinates, start_coord=None):
        """Create distance matrix for all coordinates"""
        if start_coord:
            all_coords = [start_coord] + coordinates
        else:
            all_coords = coordinates
        
        n = len(all_coords)
        distance_matrix = []
        
        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append(0)
                else:
                    distance = self.calculate_distance(all_coords[i], all_coords[j])
                    # Convert to integer for OR-Tools (multiply by 100 for precision)
                    row.append(int(distance * 100))
            distance_matrix.append(row)
        
        return distance_matrix, all_coords
    
    def optimize_route(self, coordinates, start_coord=None):
        """Optimize route using Google OR-Tools TSP solver"""
        try:
            # Create distance matrix
            distance_matrix, all_coords = self.create_distance_matrix(coordinates, start_coord)
            
            # Create routing model
            self.manager = pywrapcp.RoutingIndexManager(
                len(distance_matrix), 1, 0  # num_nodes, num_vehicles, depot
            )
            self.routing = pywrapcp.RoutingModel(self.manager)
            
            def distance_callback(from_index, to_index):
                from_node = self.manager.IndexToNode(from_index)
                to_node = self.manager.IndexToNode(to_index)
                return distance_matrix[from_node][to_node]
            
            transit_callback_index = self.routing.RegisterTransitCallback(distance_callback)
            self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
            # Set search parameters
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
            search_parameters.local_search_metaheuristic = (
                routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            )
            search_parameters.time_limit.seconds = 30
            
            # Solve the problem
            self.solution = self.routing.SolveWithParameters(search_parameters)
            
            if self.solution:
                return self._extract_route(all_coords, start_coord is not None)
            else:
                # Fallback: return original order if optimization fails
                return coordinates
                
        except Exception as e:
            print(f"Route optimization error: {e}")
            # Fallback: return original order
            return coordinates
    
    def _extract_route(self, all_coords, has_start):
        """Extract optimized route from solution"""
        route = []
        index = self.routing.Start(0)
        
        while not self.routing.IsEnd(index):
            node_index = self.manager.IndexToNode(index)
            
            if has_start and node_index == 0:
                # Skip start location in the route
                pass
            else:
                coord_index = node_index - (1 if has_start else 0)
                if coord_index < len(all_coords) - (1 if has_start else 0):
                    route.append(all_coords[coord_index + (1 if has_start else 0)])
            
            index = self.solution.Value(self.routing.NextVar(index))
        
        return route
    
    def calculate_total_distance(self, route):
        """Calculate total distance for the optimized route"""
        if len(route) < 2:
            return 0
        
        total_distance = 0
        for i in range(len(route) - 1):
            distance = self.calculate_distance(route[i], route[i + 1])
            total_distance += distance
        
        return round(total_distance, 2)
    
    def estimate_delivery_time(self, total_distance, num_stops):
        """Estimate delivery time based on distance and number of stops"""
        # Average speed: 25 km/h in urban areas
        # Average time per stop: 5 minutes
        travel_time = (total_distance / 25) * 60  # Convert to minutes
        stop_time = num_stops * 5  # 5 minutes per stop
        
        total_time = travel_time + stop_time
        return round(total_time, 2)  # Return in minutes
