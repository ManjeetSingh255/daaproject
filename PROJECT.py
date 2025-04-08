import heapq
import requests
import gradio as gr
from collections import defaultdict

#  Google Maps API key (replace with yours)
GOOGLE_MAPS_API_KEY = "AIzaSyAkhFPCsPNFK1oO3N5upoLyynhGQfV93Gw"

#  Get coordinates using Google Geocoding API
def get_coordinates(city_name):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city_name}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        lat = data["results"][0]["geometry"]["location"]["lat"]
        lng = data["results"][0]["geometry"]["location"]["lng"]
        return f"{lat},{lng}"
    else:
        return None

#  Get distance using Google Directions API
def get_distance_between(city1, city2):
    coord1 = get_coordinates(city1)
    coord2 = get_coordinates(city2)

    if not coord1 or not coord2:
        return None

    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={coord1}&destination={coord2}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK" and data["routes"]:
        distance = data["routes"][0]["legs"][0]["distance"]["value"]
        return distance // 1000
    else:
        return None  #  No drivable route

# Graph and Dijkstra implementation
class Graph:
    def __init__(self):
        self.graph = defaultdict(list)

    def add_edge(self, city1, city2, distance):
        self.graph[city1].append((city2, distance))
        self.graph[city2].append((city1, distance))

    def dijkstra(self, start, end):
        distances = {city: float('inf') for city in self.graph}
        distances[start] = 0
        pq = [(0, start)]
        predecessors = {start: None}

        while pq:
            current_distance, current_city = heapq.heappop(pq)
            if current_city == end:
                break

            for neighbor, weight in self.graph[current_city]:
                new_distance = current_distance + weight
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = current_city
                    heapq.heappush(pq, (new_distance, neighbor))

        return distances, predecessors

    def reconstruct_path(self, predecessors, start, end):
        path = []
        while end is not None:
            path.insert(0, end)
            end = predecessors[end]
        if path and path[0] == start:
            return path
        return []

graph = Graph()

#  Add road between cities
def add_road(city1, city2):
    distance = get_distance_between(city1, city2)
    if distance is None:
        return f" No drivable road found between {city1} and {city2}. You may need to travel by air."

    graph.add_edge(city1, city2, distance)
    return f" Road added between {city1} and {city2} ({distance} km)."

#  Find shortest path
def find_shortest_path(city1, city2):
    if city1 not in graph.graph or city2 not in graph.graph:
        return f" One or both cities are not in the network. Please add roads first.", ""

    distances, predecessors = graph.dijkstra(city1, city2)
    path = graph.reconstruct_path(predecessors, city1, city2)
    total_distance = distances[city2]

    if not path:
        return f" No path found between {city1} and {city2}.", ""

    path_str = " → ".join(path)
    
    # Create Google Maps link using cached coordinates
    coords = [get_coordinates(city) for city in path]
    if None in coords:
        return f" Path: {path_str} ({total_distance} km)\n But failed to generate map link.", ""
    map_url = f"https://www.google.com/maps/dir/" + "/".join(coords)

    return f"Shortest path from {city1} to {city2}:\n{path_str} ({total_distance} km)", f"[🔗 View Route on Google Maps]({map_url})"

#  Gradio UI
with gr.Blocks() as app:
    gr.HTML("""
    <div style="text-align:center; padding:20px; background:#4facfe; color:white; border-radius:15px;">
        <h1> Dijkstra's Shortest Path Finder</h1>
        <p>Build your custom city network and find the shortest road path between them using Google Maps!</p>
    </div>
    """)

    with gr.Tab("Add Road"):
        with gr.Row():
            city1 = gr.Textbox(label="City 1")
            city2 = gr.Textbox(label="City 2")
        add_button = gr.Button("Add Road")
        road_output = gr.Textbox(label="Status")
        add_button.click(add_road, inputs=[city1, city2], outputs=road_output)

    with gr.Tab("Find Shortest Path"):
        with gr.Row():
            source = gr.Textbox(label="Source City")
            destination = gr.Textbox(label="Destination City")
        find_button = gr.Button("Find Path")
        path_output = gr.Textbox(label="Path Info")
        map_markdown = gr.Markdown()
        find_button.click(find_shortest_path, inputs=[source, destination], outputs=[path_output, map_markdown])

#  Launch app
app.launch()
