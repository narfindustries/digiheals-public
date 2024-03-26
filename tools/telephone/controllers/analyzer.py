# 	# --validate-ccda [run_id] [optional: doc_id]
	# --analyze-logs [run_id] [db, code, apache, agent, all]
	# --analyze-http-statuses [run_id]
	# --analyze-data-structures [run_id]
	# --list-run-ids

import click


@click.command()
@click.option("--validate-ccda", default="123", help="The run_id to CCDA validate")
@click.option("--analyze-logs", default="all", help="Analyze logs from [http, ds, db, code, apache, agent, all]")
@click.option("--analyze-run-id", default="123", help="The run_id to analyze")
@click.option("--list-run-ids", default=False, help="List the available run_ids")
def main(validate_ccda, analyze_logs, analyze_run_id, list_run_ids):
    print(validate_ccda, analyze_logs, analyze_run_id, list_run_ids)

if __name__ == "__main__":
    main()