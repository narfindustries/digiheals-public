""" Traverse all paths and find max depth for each resource type"""

import os
import csv
import networkx as nx
import plotly.graph_objects as go
import plotly.io as pio

RESOURCES_FOLDER = "output/resource"
TYPES_FOLDER = "output/types"


def parse_fhir_spec_csv(file_path):
    """Parse csv file to extract all fields and their types"""
    metadata = {}
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 2:
                field, field_type = row
                metadata[field] = {"type": field_type}
    return metadata


def find_max_depth(spec_file, depth, visited_files_per_path, chain_path):
    """
    Recursively find the chain with the maximum depth.
    """
    if spec_file in visited_files_per_path:
        return (
            depth - 1,
            chain_path[:-1],
        )  # Prevent infinite recursion and recursion in loop, we do depth-1, to exclude the file already visited

    visited_files_per_path.add(spec_file)
    metadata = parse_fhir_spec_csv(spec_file)
    max_depth = depth
    max_depth_chain = chain_path

    for _, details in metadata.items():
        if (
            "type" in details and details["type"][0].isupper()
        ):  # Check if type is a nested type
            nested_type = details["type"]

            # Find the folder the nested file belongs to
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
                new_chain_path = chain_path + [nested_type]
                nested_depth, nested_chain = find_max_depth(
                    nested_spec_file,
                    depth + 1,
                    visited_files_per_path.copy(),
                    new_chain_path,
                )
                # Check recursive output from child with parent depth and chain and replace max_depth
                if nested_depth > max_depth:
                    max_depth = nested_depth
                    max_depth_chain = nested_chain

    return max_depth, max_depth_chain


def traverse_all_paths(
    spec_file, visited_files_per_path, graph, edges_set, node_styles
):
    """Recursively traverse all possible paths"""
    if (
        spec_file in visited_files_per_path
    ):  # To avoid same file from being visited again
        return

    visited_files_per_path.add(spec_file)
    metadata = parse_fhir_spec_csv(spec_file)

    current_node = os.path.basename(spec_file).split(".")[0]

    if current_node == "Patient":
        node_styles[current_node] = {
            "color": "#e6add8",
            "shape": "square",
            "size": 15,
        }
    elif current_node == "Extension":
        node_styles[current_node] = {"color": "#d8e6ad", "shape": "cross", "size": 15}
    elif spec_file.startswith(RESOURCES_FOLDER):
        node_styles[current_node] = {
            "color": "#e6bbad",
            "shape": "star-triangle-up",
            "size": 10,
        }
    elif spec_file.startswith(TYPES_FOLDER):
        node_styles[current_node] = {
            "color": "#add8e6",
            "shape": "circle",
            "size": 10,
        }

    for _, details in metadata.items():
        if (
            "type" in details and details["type"][0].isupper()
        ):  # Check if type is a nested type
            nested_type = details["type"]

            # Determine which folder the nested file belongs to
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
                edge = (current_node, nested_type)  # Create edge

                # Check if edge exists in set before creating edge, if not add to set
                if edge not in edges_set:
                    graph.add_edge(current_node, nested_type)
                    edges_set.add(edge)

                traverse_all_paths(
                    nested_spec_file,
                    visited_files_per_path.copy(),
                    graph,
                    edges_set,
                    node_styles,
                )


def traverse_patient_paths(
    spec_file, visited_files_per_path, graph, edges_set, node_styles
):
    """Recursively traverse 1st level paths for Patient.csv"""
    if (
        spec_file in visited_files_per_path
    ):  # To avoid same file from being visited again
        return

    visited_files_per_path.add(spec_file)
    metadata = parse_fhir_spec_csv(spec_file)

    current_node = os.path.basename(spec_file).split(".")[0]

    if current_node == "Patient":
        node_styles[current_node] = {
            "color": "#e6add8",
            "shape": "square",
            "size": 15,
        }
    elif spec_file.startswith(TYPES_FOLDER):
        node_styles[current_node] = {
            "color": "#e6bbad",
            "shape": "circle",
            "size": 10,
        }

    for _, details in metadata.items():
        if (
            "type" in details and details["type"][0].isupper()
        ):  # Check if type is a nested type
            nested_type = details["type"]

            # Determine which folder the nested file belongs to
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
                edge = (current_node, nested_type)  # Create edge

                # Check if edge exists in set before creating edge, if not add to set
                if edge not in edges_set:
                    graph.add_edge(current_node, nested_type)
                    edges_set.add(edge)


def list_files_in_folder(folder_path):
    """List all file paths in the given folder."""
    file_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths


# Process all resource files
resource_files = list_files_in_folder(RESOURCES_FOLDER)

# CODE TO FIND MAX DEPTH ACROSS RESOURCES AND TYPES
# max_depth_across_resources = 0
# max_depth_dict = {}

# for resource_file in resource_files:
#     print(f"Processing: {resource_file}")

#     # Set depth=1, empty set for visited files in path, and initial chain path
#     max_depth, max_depth_chain = find_max_depth(resource_file, 1, set(), [os.path.basename(resource_file).split(".")[0]])

#     max_depth_across_resources = max(max_depth, max_depth_across_resources)
#     max_depth_dict[os.path.basename(resource_file).split(".")[0]] = {"max_depth":max_depth, "max_depth_chain":max_depth_chain}

#     # Print chain with max depth for this file
#     print(f"{resource_file}: Max Depth = {max_depth}")
#     print(" -> ".join(max_depth_chain), "\n")

# print(f"Max depth across all resources: {max_depth_across_resources}")

# with open('max_depth_resources.json', 'w', encoding='utf-8') as f:
#     json.dump(max_depth_dict, f, ensure_ascii=False, indent=4)


# CODE TO FIND ALL POSSIBLE PATHS ACROSS RESOURCES AND TYPES + VIZ
# Initialize NetworkX graph
graph = nx.DiGraph()  # Directed graph
edges_set = set()
node_styles = {}

for resource_file in resource_files:
    print(f"Processing: {resource_file}")
    resource_name = os.path.basename(resource_file).split(".")[0]

    # Start traversal with root node
    graph.add_node(resource_name)
    traverse_all_paths(resource_file, set(), graph, edges_set, node_styles)

# """ Create Struct for Patient Resource type"""
# resource_file = 'output/resource/Patient.csv'
# print(f"Processing: {resource_file}")
# resource_name = os.path.basename(resource_file).split(".")[0]

# # Start traversal with root node
# graph.add_node(resource_name)
# traverse_patient_paths(resource_file, set(), graph, edges_set, node_styles)


# Plot graph using Plotly
pos = nx.spring_layout(graph, k=0.8, seed=42)

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
        node, {"color": "#e6bbad", "shape": "star-triangle-up"}
    )
    node_color_list.append(node_style["color"])
    node_symbol.append(node_style["shape"])
    node_size.append(node_style["size"])
    node_text.append(node)

node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers",
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

pio.write_image(fig, "figs/resource_graph_all.pdf", format="pdf", scale=5)
# pio.write_image(fig, "resource_graph_all.eps", format="eps", scale=3) Throwing PDF to EPS conversion failed error
# Display the figure
# fig.show()


# # Plot Patient figure using Plotly
# pos = nx.spring_layout(graph, k=0.5, seed=42)

# node_trace = go.Scatter(
#     x=node_x,
#     y=node_y,
#     mode="markers+text",
#     hoverinfo="text",
#     text=node_text,
#     textposition="middle center",
#     marker=dict(
#         size=150,
#         symbol=node_symbol,
#         color=node_color_list,
#         line=dict(width=1, color="black"),
#     ),
#     textfont=dict(size=14, color="black", family="Arial Black")
# )

# pio.write_image(fig, "figs/patient_struct.pdf", format="pdf", scale=5)
