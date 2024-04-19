# 	# --end-node [name]
# --get-http-statuses
# --get-db-logs
# --get-instrumented-code-logs
# --get-agent-logs
# --get-apache-logs
# --get-ccda-file [patient-name]
# --get-all-ccda-files

import click


@click.command()
@click.option(
    "--end-node", default="OpenEMR", help="The name of the node you want to export from"
)
@click.option("--get-http-statuses", default=True, help="Export http statuses")
@click.option("--get-db-logs", default=True, help="Export database logs")
@click.option(
    "--get-instrumented-logs", default=True, help="Export instrumentation logs"
)
@click.option("--get-agent-logs", default=True, help="Export agent logs")
@click.option("--get-apache-logs", default=True, help="Export Apache logs")
@click.option("--get-all-ccda-files", default=True, help="Export all CCDA files")
@click.option(
    "--get-ccda-file", default="Joe Smith", help="Export one patient's CCDA file"
)
def main(
    end_node,
    get_http_statuses,
    get_db_logs,
    get_instrumented_logs,
    get_agent_logs,
    get_apache_logs,
    get_all_ccda_files,
    get_ccda_file,
):
    print(
        end_node,
        get_http_statuses,
        get_db_logs,
        get_instrumented_logs,
        get_agent_logs,
        get_apache_logs,
        get_all_ccda_files,
        get_ccda_file,
    )


if __name__ == "__main__":
    main()
