require 'json'
require 'fhir_models'

SYNTHEA_FOLDER = ARGV[0] # Get command line argument from user

def all_files
  Dir[SYNTHEA_FOLDER+"*.json"]
end

valid_files = 0
all_files.each do |file|
  data = File.read(file)
  # Test the fhir_models FHIR parser on the data
  patient = FHIR.from_contents(data)
  if not patient.valid?
    exit
  else
    valid_files = valid_files + 1
    puts "Valid files so far #{valid_files}"
  end
  parsed_data = JSON.parse(data)
  parsed_data["entry"].each do |value|
    # fullUrl, resource, request are the only three keys allowed here. Do we have more?
    value["resource"].each do |k, v|
      puts "#{k},#{v}"
    end
  end
end
