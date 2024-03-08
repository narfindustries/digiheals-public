# CONOPS Of Using the Telephone Driver Tool (TDT)

## Steps
0. Configuration (e.g., selection of length of game of telephone, which EHR's, which data generators, number of files to generate)
1. Produce a test document (e.g., Call to Synthea or other data generator to produce File A)
2. Pass file A to the Validator
3. If A passes, send it to the first hop (e.g., OpenEMR) for ingest via (FHIR API or Web upload)
4. Observe HTTP response code for that uploaded XML file
5. Read or monitor the httpd / apache2 log file for any errors 
6. (Assuming instrumentation is in place); observe 'front half' of the EHR.Reader's behavior e.g., SQL queries
7. 


## Details

### Step 0

### Step 1

### Step 2

### Step 3

- observe the HTTP response code (e.g., Error 500)

### Step 4 

snapshot of a per-record view of an important data structure or the SQL query content as it goes from Reader to DB

### Step 5

Have a server-resident component that is looking at the log file

### Step 6

Alternatives:
  - observer data structure content
  - server-resident piece of code to monitor the mysql transaction log

### Step 7

modify / instrument the EHR.Reader code to directly observe which SQL queries it is generating

### Step 8
