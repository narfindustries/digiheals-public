"""Find max depth for largest Patient file"""

import json
import os
import csv
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio

from utils import parse_fhir_spec_csv

RESOURCES_FOLDER = "output/resource"
TYPES_FOLDER = "output/types"


def traverse_all_paths(data_to_parse, spec_file, graph, node_styles):
    """Recursively traverse patient data and construct graph"""

    metadata = parse_fhir_spec_csv(spec_file)
    current_node = os.path.basename(spec_file).split(".")[0]

    for key, details in metadata.items():
        if (
            "type" in details and details["type"][0].isupper()
        ):  # Check if type is a nested type
            nested_type = details["type"]

            if key in data_to_parse:  # Check if this field exists in the patient data
                value = data_to_parse[key]

                resource_nested_spec_file = os.path.join(
                    RESOURCES_FOLDER, f"{nested_type}.csv"
                )
                type_nested_spec_file = os.path.join(TYPES_FOLDER, f"{nested_type}.csv")
                nested_spec_file = (
                    resource_nested_spec_file
                    if os.path.exists(resource_nested_spec_file)
                    else type_nested_spec_file
                )

                if os.path.exists(nested_spec_file):
                    graph.add_edge(current_node, nested_type)
                    node_styles[nested_type] = {
                        "color": "#add8e6",
                        "shape": "circle",
                        "size": 15,
                    }

                    if isinstance(
                        value, list
                    ):  # If its a list, use for loop to traverse through each element
                        for list_element in value:
                            if isinstance(list_element, dict):
                                traverse_all_paths(
                                    list_element, nested_spec_file, graph, node_styles
                                )
                    elif isinstance(value, dict):
                        traverse_all_paths(value, nested_spec_file, graph, node_styles)


# patient_file = "Akiko835_Wisozk929_6be3de83-b860-1fa6-5a7d-c20b8837ade7.json"
patient_file = "Benton624_Spinka232_ac997bea-73f7-a605-4826-7bf1205fb34b.json"

# Reading the first patient file
with open(patient_file, "r", encoding="utf-8") as f:
    data = json.load(f)

graph = nx.MultiDiGraph()
node_styles = {}

# Set patient file as the root node
current_node = (
    os.path.basename(patient_file).split("_")[0]
    + "_"
    + os.path.basename(patient_file).split("_")[1]
)
graph.add_node(current_node)
node_styles[current_node] = {"color": "seagreen", "size": 20, "shape": "diamond"}

# Start creating the graph
for entry in data.get("entry", []):
    resource = entry.get("resource", {})
    resource_type = resource.get("resourceType")

    if not resource_type:  # Ensure resourceType exists
        continue

    resource_spec_file = os.path.join(RESOURCES_FOLDER, f"{resource_type}.csv")
    if os.path.exists(resource_spec_file):
        graph.add_edge(current_node, resource_type)
        traverse_all_paths(resource, resource_spec_file, graph, node_styles)

print(graph.nodes())
print(len(graph.edges()))

# Plot graph using Plotly
pos = nx.spring_layout(graph, k=25, seed=42)

# Create edge traces
edge_x = []
edge_y = []

for edge in graph.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=0.5, color="#a6a6a6"),
    hoverinfo="none",
    mode="lines",
)

# Create node traces
node_x = []
node_y = []
node_color_list = []
node_text = []
node_symbol = []
node_size = []

for node in graph.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_style = node_styles.get(
        node, {"color": "#e6bbad", "shape": "star-triangle-up", "size": 15}
    )
    node_color_list.append(node_style["color"])
    node_symbol.append(node_style["shape"])
    node_size.append(node_style["size"])
    node_text.append(node)

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers+text",
    hoverinfo="text",
    text=node_text,
    textposition="bottom center",
    marker=dict(
        size=node_size,
        symbol=node_symbol,
        color=node_color_list,
        line=dict(width=1, color="black"),
    ),
)

# Create figure
fig = go.Figure(
    data=[edge_trace, node_trace],
    layout=go.Layout(
        # title="FHIR Resource Types",
        showlegend=False,
        hovermode="closest",
        margin=dict(b=0, l=0, r=0, t=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        width=1600,
        height=800,
    ),
)

pio.write_image(fig, "figs/123largest_patient_graph.pdf", format="pdf", scale=5)

# Display the figure
# fig.show()
