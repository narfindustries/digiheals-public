import click


@click.command()
@click.option(
    "--routes-file",
    default="../routes.json",
    help="The filepath for the routes.json file",
)
@click.option(
    "--skip-validation", default=False, help="Skips post generation CCDA checking"
)
@click.option("--generate-ccda", default=True, help="Use the CCDA generator")
@click.option("--ccda-generator", default="Synthea", help="The CCDA generator to use")
@click.option(
    "--ccda-doc-count", default="1", help="The number of CCDA documents to generate"
)
@click.option(
    "--ccda-generator-output-path",
    default="../output",
    help="The folder to output the generated CCDA files",
)
@click.option(
    "--run-from-db",
    default=False,
    help="Skip generation and importing. Use data in the db already",
)
@click.option(
    "--db-run-id",
    default="1",
    help="If run-from-db is true, use this run_id for analysis",
)
@click.option(
    "--db-run-doc-id", default="1", help="If run-from-db is true, use this doc_id"
)
@click.option(
    "--use-ccda-corpus",
    default=False,
    help="Skip generating CCDA files and use the corpus",
)
@click.option(
    "--ccda-corpus-path",
    default="../ccda-corpus",
    help="The filepath for the CCDA corpus",
)
@click.option("--validator-name", default="HL7", help="The CCDA validator to use")
@click.option(
    "--autogen-path-depth",
    default=2,
    help="The number of nodes to include the routes.json configuration",
)
@click.option(
    "--db-validate-ccda-doc",
    default=1,
    help="The doc_id number to validate from the database",
)
def main(
    routes_file,
    skip_validation,
    generate_ccda,
    ccda_doc_count,
    run_from_db,
    db_run_id,
    db_run_doc_id,
    use_ccda_corpus,
    ccda_corpus_path,
    validator_name,
    autogen_path_depth,
    db_validate_ccda_doc,
    ccda_generator,
    ccda_generator_output_path,
):
    print(
        routes_file,
        skip_validation,
        generate_ccda,
        ccda_doc_count,
        run_from_db,
        db_run_id,
        db_run_doc_id,
        use_ccda_corpus,
        ccda_corpus_path,
        validator_name,
        autogen_path_depth,
        db_validate_ccda_doc,
        ccda_generator,
        ccda_generator_output_path,
    )


if __name__ == "__main__":
    main()
