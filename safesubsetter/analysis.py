from db_analysis import Database
import matplotlib.pyplot as plt


list_of_tablenames = [
    "safe_subset_latest_vista",
    "safe_subset_latest_hapi",
    "safe_subset_latest_ibm",
    "safe_subset_latest_blaze",
    "safe_subset_latest_iris",
]

# list_of_tablenames = [
#     "safe_subset_records_vista_latest",
#     "safe_subset_records_hapi_latest",
#     "safe_subset_records_ibm_latest",
#     "safe_subset_records_blaze_latest",
#     "safe_subset_records_iris_latest",
# ]

server_names = ["ibm", "iris", "hapi", "vista", "blaze"]


def rejected_records():
    """
    This function retrieves the number of rejected records from each server's table
    and generates a bar chart to visualize the results.
    """
    db = Database("safe_subset_latest.db")
    rejected = {}

    for tablename in list_of_tablenames:
        all_records = db.get_all_records(tablename)
        accepted_count = 0
        for record in all_records:
            if record.response_status:
                accepted_count += 1

        rejected[tablename] = len(all_records) - accepted_count

    # Simplify table names
    simplified_names = [name.split("_")[-1] for name in rejected.keys()]

    # Create the bar chart with different colors
    colors = ["#6C91BF", "#A0C1B8", "#F6D186", "#F19292", "#C4B7CB"]
    bars = plt.bar(simplified_names, rejected.values(), color=colors)

    # Add percentage labels on top of each bar
    total_records = 166862
    for bar in bars:
        height = bar.get_height()
        percentage = (height / total_records) * 100
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{percentage:.1f}%",
            ha="center",
            va="bottom",
        )

    plt.xticks(rotation=45, ha="right")
    plt.title("Percentage of Mutated Files Rejected by FHIR Servers")
    plt.xlabel("Server Name")
    plt.ylabel("# of Mutated files")
    plt.tight_layout()
    plt.savefig("mew-rejected_records-2.png")


def accepted_files_missing_keys():
    """
    This function retrieves the number of rejected records from each server's table
    and generates a bar chart to visualize the results.
    """

    db = Database("safe_subset_latest.db")

    rejected = {}

    for tablename in list_of_tablenames:
        count = db.count_accepted_with_missing(tablename)
        rejected[tablename] = count

    print(rejected)

    # Simplify table names
    simplified_names = [name.split("_")[-1] for name in rejected.keys()]

    # Create the bar chart with different colors
    colors = ["#6C91BF", "#A0C1B8", "#F6D186", "#F19292", "#C4B7CB"]
    bars = plt.bar(simplified_names, rejected.values(), color=colors)

    # Add percentage labels on top of each bar
    total_records = 166862
    for bar in bars:
        height = bar.get_height()
        percentage = (height / total_records) * 100
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{percentage:.1f}%",
            ha="center",
            va="bottom",
        )

    plt.xticks(rotation=45, ha="right")
    plt.title("Accepted Files with Missing Mutated Values")
    plt.xlabel("Server Name")
    plt.ylabel("# of Mutated Files")
    plt.tight_layout()
    plt.savefig("mew-accepted_records_missing_value-2.png")


def compare_resp_out_values():
    """
    This function retrieves the number of rejected records from each server's table
    and generates a bar chart to visualize the results.
    """

    db = Database("safe_subset_latest.db")

    rejected = {}

    for tablename in list_of_tablenames:
        val = db.count_output_resp_diff(tablename)

        rejected[tablename] = val
    print(rejected)
    import matplotlib.pyplot as plt

    # Simplify table names
    simplified_names = [name.split("_")[-1] for name in rejected.keys()]

    # Create the bar chart with different colors
    colors = ["#6C91BF", "#A0C1B8", "#F6D186", "#F19292", "#C4B7CB"]
    bars = plt.bar(simplified_names, rejected.values(), color=colors)

    # Add percentage labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        percentage = height / 166862 * 100  # Assuming total records is 2794
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{percentage:.1f}%",
            ha="center",
            va="bottom",
        )

    plt.xticks(rotation=45, ha="right")
    plt.title("Percentage of Outputs with Incorrect Field Values Returned by Server")
    plt.xlabel("Server Name")
    plt.ylabel("# of Mutated Files")
    plt.tight_layout()
    plt.savefig("mew-compare_old_resp-2.png")


rejected_records()
# accepted_files_missing_keys()
# compare_resp_out_values()
