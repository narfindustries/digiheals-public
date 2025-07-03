import matplotlib.pyplot as plt
import matplotlib
from db import Database
import numpy as np

# Mapping tablename suffixes to display names
table_display_names = {
    "blaze": "Blaze",
    "vista": "VistA",
    "iris": "IRIS",
    "hapi": "HAPI",
    "ibm": "IBM",
}
# list_of_tablenames = [
#     "safe_subset_records_vista_latest",
#     "safe_subset_records_hapi_latest",
#     "safe_subset_records_ibm_latest",
#     "safe_subset_records_blaze_latest",
#     "safe_subset_records_iris_latest",
# ]
list_of_tablenames = [
    "safe_subset_latest_blaze",
    "safe_subset_latest_vista",
    "safe_subset_latest_iris",
    "safe_subset_latest_hapi",
    "safe_subset_latest_ibm",
]

""" Graph 1"""


def plot_accepted_vs_rejected(list_of_tablenames):
    db = Database("safe_subset.db")
    # db = Database("safe_subset_latest.db")
    accepted_counts = {}
    rejected_counts = {}

    for tablename in list_of_tablenames:
        all_records = db.get_all_records(tablename)
        accepted = sum(1 for record in all_records if record.response_status)
        rejected = len(all_records) - accepted
        server_key = tablename.split("_")[3]  # e.g., "blaze"
        display_name = table_display_names.get(server_key, server_key.capitalize())
        accepted_counts[display_name] = accepted
        rejected_counts[display_name] = rejected

    # Ensure servers appear in desired order
    sorted_servers = ["Blaze", "HAPI", "IBM", "IRIS", "VistA"]
    accepted = [accepted_counts.get(server, 0) for server in sorted_servers]
    rejected = [rejected_counts.get(server, 0) for server in sorted_servers]

    # Plot stacked bars
    plt.figure(figsize=(8, 5))
    plt.bar(sorted_servers, accepted, label="Accepted", color="#4C78A8")
    plt.bar(
        sorted_servers, rejected, bottom=accepted, label="Rejected", color="firebrick"
    )

    # Add percentage text inside bars
    total = [a + r for a, r in zip(accepted, rejected)]
    for i in range(len(sorted_servers)):
        if total[i] == 0:
            continue
        plt.text(
            i,
            accepted[i] / 2,
            f"{(accepted[i] / total[i]) * 100:.1f}%",
            ha="center",
            va="center",
            color="white",
            fontsize=10,
        )
        plt.text(
            i,
            accepted[i] + rejected[i] / 2,
            f"{(rejected[i] / total[i]) * 100:.1f}%",
            ha="center",
            va="center",
            color="white",
            fontsize=10,
        )

    plt.title("Mutated File Acceptance vs Rejection per Server (Total = 2794)")
    plt.xlabel("FHIR Server")
    plt.ylabel("Number of Mutated Files")
    plt.legend()
    plt.tight_layout()
    plt.savefig("1-mutation_acceptance_vs_rejection.pdf")
    plt.show()


def plot_accepted_vs_missing(list_of_tablenames):
    db = Database("safe_subset.db")
    # db = Database("safe_subset_latest.db")
    server_label_map = {
        "blaze": "Blaze",
        "hapi": "HAPI",
        "ibm": "IBM",
        "iris": "IRIS",
        "vista": "VistA",
    }

    accepted_counts_map = {}
    missing_counts_map = {}

    for tablename in list_of_tablenames:
        server_key = tablename.split("_")[3].lower()
        server_label = server_label_map.get(server_key)
        if not server_label:
            continue  # skip if unknown

        accepted = db.count_accepted(tablename)
        missing = db.count_accepted_with_missing(tablename)

        accepted_counts_map[server_label] = accepted
        missing_counts_map[server_label] = missing

    sorted_servers = ["Blaze", "HAPI", "IBM", "IRIS", "VistA"]
    accepted_counts = [accepted_counts_map.get(server, 0) for server in sorted_servers]
    missing_counts = [missing_counts_map.get(server, 0) for server in sorted_servers]

    x = np.arange(len(sorted_servers))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.bar(
        x - width / 2, accepted_counts, width, label="Accepted Files", color="#4682B4"
    )
    bars2 = ax.bar(
        x + width / 2,
        missing_counts,
        width,
        label="Missing Mutated Fields",
        color="#FFA500",
    )

    for i in range(len(missing_counts)):
        if accepted_counts[i] > 0:
            percentage = (missing_counts[i] / accepted_counts[i]) * 100
        else:
            percentage = 0
        ax.text(
            x[i] + width / 2,
            missing_counts[i],
            f"{percentage:.1f}%",
            ha="center",
            va="bottom",
        )

    ax.set_xlabel("Server")
    ax.set_ylabel("Number of Mutated Files")
    ax.set_title("Accepted Files vs Files Missing Mutated Values per Server")
    ax.set_xticks(x)
    ax.set_xticklabels(sorted_servers)
    ax.legend()

    fig.tight_layout()
    plt.savefig("1-accepted_vs_missing.pdf")


# plot_accepted_vs_rejected(list_of_tablenames)
# plot_accepted_vs_missing(list_of_tablenames)


def plot_mutation_acceptance_rejection_percentages(list_of_tablenames):
    db = Database("safe_subset_latest.db")

    # Normalize server names
    server_label_map = {
        "blaze": "Blaze",
        "hapi": "HAPI",
        "ibm": "IBM",
        "iris": "IRIS",
        "vista": "VistA",
    }

    accepted_counts_map = {}
    rejected_counts_map = {}

    for tablename in list_of_tablenames:
        server_key = tablename.split("_")[3].lower()
        server_label = server_label_map.get(server_key)
        if not server_label:
            continue

        accepted = db.count_accepted(tablename)
        total = db.get_all_records(tablename)
        rejected = int(len(total)) - int(accepted)

        accepted_counts_map[server_label] = accepted
        rejected_counts_map[server_label] = rejected

    sorted_servers = ["VistA", "IRIS", "IBM", "HAPI", "Blaze"]
    accepted_vals = [accepted_counts_map.get(s, 0) for s in sorted_servers]
    rejected_vals = [rejected_counts_map.get(s, 0) for s in sorted_servers]

    totals = [a + r for a, r in zip(accepted_vals, rejected_vals)]
    accepted_perc = [a / t * 100 if t > 0 else 0 for a, t in zip(accepted_vals, totals)]
    rejected_perc = [r / t * 100 if t > 0 else 0 for r, t in zip(rejected_vals, totals)]

    y = np.arange(len(sorted_servers))
    height = 0.75

    fig, ax = plt.subplots(figsize=(8, 5))
    bars1 = ax.barh(y, accepted_perc, height, label="Accepted (%)", color="#4C78A8")
    bars2 = ax.barh(
        y,
        rejected_perc,
        height,
        left=accepted_perc,
        label="Rejected (%)",
        color="firebrick",
    )

    for i in range(len(y)):
        if accepted_perc[i] > 0:
            ax.text(
                accepted_perc[i] / 2,
                y[i],
                f"{accepted_perc[i]:.1f}%",
                va="center",
                ha="center",
                color="white",
            )
        if rejected_perc[i] > 0:
            ax.text(
                accepted_perc[i] + rejected_perc[i] / 2,
                y[i],
                f"{rejected_perc[i]:.1f}%",
                va="center",
                ha="center",
                color="white",
            )

    ax.set_yticks(y)
    ax.set_yticklabels(sorted_servers)
    ax.set_xlabel("Percentage of Mutated Files")
    ax.set_title("Mutation Acceptance and Rejection Rates per Server")
    ax.legend(loc="upper right")
    ax.set_xlim(0, 100)

    plt.tight_layout()
    plt.savefig("analysis_3.pdf")


plot_mutation_acceptance_rejection_percentages(list_of_tablenames)
