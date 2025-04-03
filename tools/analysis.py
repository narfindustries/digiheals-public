from db_mut import Database

list_of_tablenames = [
    "safe_subset_records_vista_latest",
    "safe_subset_records_blaze_latest",
    "safe_subset_records_iris_latest",
    "safe_subset_records_ibm_latest",
    "safe_subset_records_hapi_latest",
]


def rejected_records():
    """
    This function retrieves the number of rejected records from each server's table
    and generates a bar chart to visualize the results.
    """

    rejected = {}

    for tablename in list_of_tablenames:
        db = Database("safe_subset.db", tablename)
        all_records = db.get_all_records()
        accepted_count = 0
        for record in db.get_all_records():
            if record.response_status:
                accepted_count += 1

        rejected[tablename] = len(all_records) - accepted_count

    import matplotlib.pyplot as plt

    # Simplify table names
    simplified_names = [name.split("_")[3] for name in rejected.keys()]

    # Create the bar chart with different colors
    colors = ["#FF9999", "#66B2FF", "#99FF99", "#FFCC99", "#FF99CC"]
    bars = plt.bar(simplified_names, rejected.values(), color=colors)

    # Add percentage labels on top of each bar
    total_records = 3193
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
    plt.title("Rejected Records by Server")
    plt.xlabel("Server Name")
    plt.ylabel("Number of Rejected Records")
    plt.tight_layout()
    plt.savefig("rejected_records.png")


def accepted_files_missing_keys():
    """
    This function retrieves the number of rejected records from each server's table
    and generates a bar chart to visualize the results.
    """

    rejected = {}

    for tablename in list_of_tablenames:
        db = Database("safe_subset.db", tablename)
        all_records = db.get_all_records()
        accepted_count = 0
        for record in db.get_all_records():
            if record.response_status:
                if "missing" in record.resp_value:
                    accepted_count += 1

        rejected[tablename] = accepted_count
    print(rejected)
    import matplotlib.pyplot as plt

    # Simplify table names
    simplified_names = [name.split("_")[3] for name in rejected.keys()]

    # Create the bar chart with different colors
    colors = ["#FF9999", "#66B2FF", "#99FF99", "#FFCC99", "#FF99CC"]
    bars = plt.bar(simplified_names, rejected.values(), color=colors)

    # Add percentage labels on top of each bar
    total_records = 3193
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
    plt.title("Accepted Records with Missing Mutated Values by Server")
    plt.xlabel("Server Name")
    plt.ylabel("Number of Missing Mutated Values")
    plt.tight_layout()
    plt.savefig("accepted_records_missing_value.png")


def compare_resp_out_values():
    """
    This function retrieves the number of rejected records from each server's table
    and generates a bar chart to visualize the results.
    """

    rejected = {}

    for tablename in list_of_tablenames:
        db = Database("safe_subset.db", tablename)
        all_records = db.get_all_records()
        accepted_count = 0
        total_count = 0.0
        for record in db.get_all_records():
            if record.response_status:
                total_count += 1
                if (
                    "missing" not in record.resp_value
                    and record.resp_value != record.new_value
                ):
                    accepted_count += 1
                    print(
                        record.leaf_node_path,
                        repr(record.resp_value),
                        repr(record.new_value),
                        tablename,
                    )

        rejected[tablename] = (accepted_count / total_count) * 100
    print(rejected)
    import matplotlib.pyplot as plt

    # Simplify table names
    simplified_names = [name.split("_")[3] for name in rejected.keys()]

    # Create the bar chart with different colors
    colors = ["#FF9999", "#66B2FF", "#99FF99", "#FFCC99", "#FF99CC"]
    bars = plt.bar(simplified_names, rejected.values(), color=colors)

    # Add percentage labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        percentage = height
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{percentage:.1f}%",
            ha="center",
            va="bottom",
        )

    plt.xticks(rotation=45, ha="right")
    plt.title("Cases where output from server had incorrect field value")
    plt.xlabel("Server Name")
    plt.ylabel("Percentage of Incorrect Values")
    plt.tight_layout()
    plt.savefig("compare_old_resp.png")


# rejected_records()
# accepted_files_missing_keys()
compare_resp_out_values()
