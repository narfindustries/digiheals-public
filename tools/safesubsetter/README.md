# SafeSubsetter

SafeSubsetter is a tool designed to help derive a stricter FHIR R4 specification..

## Usage

To run the `extract_types.rb` script, follow these steps:

1. Ensure you are in the `tools/safesubsetter` directory:
    ```sh
    cd tools/safesubsetter
    ```
2. Run the script with the required arguments:
    ```sh
    ruby extract_types.rb
    ```

## Output Files

The `output` folder contains CSV files of the form (fieldname, type). These types need not be fundamental, could be other Resources or Types defined separately in another folder. The function `list_all_types` in `extract_types.rb` can list all the types from the specification. 

## Acknowledgment

The machine-readable specification we have used in this repository was derived from the [FHIR Crucible model](https://github.com/fhir-crucible/fhir_models).