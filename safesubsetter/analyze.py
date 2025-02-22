import json
import pandas as pd

# import matplotlib.pyplot as plt


def read_json_file(filename):
    """Read the JSON file"""
    with open(filename, "r") as f:
        return json.load(f)


def generate_latex_table(count: int = -1):
    """Convert to DataFrame and sort by max_depth"""
    input_file = "max_depth_resources.json"
    output_file = f"max_depth_table_{count}.tex"

    data = read_json_file(input_file)
    if count == -1:
        count = len(data.keys())
    df = pd.DataFrame(
        [
            (k, v["max_depth"], (" $\\rightarrow$ ").join(v["max_depth_chain"]))
            for k, v in data.items()
        ],
        columns=["Resource", "MaxDepth", "Chain"],
    )
    df = df.sort_values("MaxDepth", ascending=True).head(count)

    # Generate LaTeX table
    latex_table = df.to_latex(
        index=False, float_format=lambda x: "%.0f" % x, longtable=True
    )
    save_latex_table(latex_table, output_file)
    print(f"LaTeX table has been generated in {output_file}")


def save_latex_table(latex_table, output_file):
    with open(output_file, "w") as f:
        f.write(latex_table)


# def generate_depth_frequency_chart():
#     """
#     Reads a JSON file containing {filename: max_depth}
#     Finds the frequency of each depth and plots a bar chart with Depths in the X axis
#     and their frequency in the Y axis
#     """
#     data = read_json_file("json_file_name")
#     depths = data.values()

#     df = pd.DataFrame(depths, columns=["depth"])
#     freq = df["depth"].value_counts().sort_index()

#     ax = freq.plot(kind="bar")
#     ax.set_xlabel("Maximum Depth")
#     ax.set_ylabel("Frequency")
#     ax.set_title("Distribution of Maximum Depths")

#     plt.tight_layout()
#     plt.savefig("depth_frequency.png")
#     plt.close()


def main():
    generate_latex_table(10)
    generate_latex_table()


if __name__ == "__main__":
    main()
