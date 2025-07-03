# This script is used to extract all the types from the FHIR R4 specification

require 'csv'
require_relative 'r4-spec/r4.rb'
require_relative 'r4-spec/model.rb'
require_relative 'r4-spec/hashable.rb'
require_relative 'r4-spec/xml.rb'
require_relative 'r4-spec/json.rb'
require_relative 'r4-spec/commonstructuredefinition.rb'
require_relative 'r4-spec/commonelementdefinition.rb'
Dir["r4-spec/resources/*.rb"].each {|file| require_relative file }
Dir["r4-spec/types/*.rb"].each {|file| require_relative file }

def list_all_resources
  # Lists all FHIR R4 resources and writes their metadata to CSV files.
  # For each resource, it retrieves the metadata and writes the key and type
  # to a CSV file named after the resource.
  # The CSV files are saved in the "output" directory.
  FHIR::R4::RESOURCES.each do |resource|
    # We need an eval here because it comes from the resource itself
    type_list = eval("FHIR::R4::#{resource}::METADATA")
    CSV.open("output/resource/#{resource}.csv", "w") do |csv|
      puts "Resource: #{resource}"
      for key, definition in type_list
        profiles = []
        if definition["type"] == "Reference" and definition["type_profiles"]
          puts definition
          definition["type_profiles"].each do |profile|
            profiles.push profile.split("/").last
          end
        end
        csv << [key, definition["type"], definition["path"], definition["valid_codes"], definition["min"], definition["max"], profiles]
      end # loop through type_list
    end # CSV open
  end # loop through resource types

  FHIR::R4::TYPES.each do |resource|
    # We need an eval here because it comes from the resource itself
    type_list = eval("FHIR::R4::#{resource}::METADATA")
    CSV.open("output/types/#{resource}.csv", "w") do |csv|
      puts "Type: #{resource}"
      for key, definition in type_list
        profiles = []
        if definition["type"] == "Reference" and definition["type_profiles"]
          definition["type_profiles"].each do |profile|
            profiles.push profile.split("/").last
          end
        end
        csv << [key, definition["type"], definition["path"], definition["valid_codes"], definition["min"], definition["max"], profiles]
      end # loop through type_list
    end # CSV open
  end # loop through resource types
end

def list_all_types
  defined_types = []
  FHIR::R4::TYPES.each do |type|
    # We need an eval here because it comes from the resource itself
    eval("FHIR::R4::#{type}::METADATA").each do |key, definition|
      if not FHIR::R4::PRIMITIVES.key?(definition["type"]) and not defined_types.include?(definition["type"])
        defined_types.push key
        puts "#{key}, #{definition["type"]}, #{defined_types}"
      end
    end
  end
end

def list_all_primitives
  FHIR::R4::PRIMITIVES
end

list_all_resources
