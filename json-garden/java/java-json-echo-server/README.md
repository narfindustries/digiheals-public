The server built by this applet parses and echos json back to the
client.  By default it runs at port 8080 (but it runs on 8181 if
started via docker compose)

There are 3 endpoints, each accepts a POST request w/ the body
containing parsable json. It's response body contains the parsed json
re-encoded into a string.

The 3 endpoints are:

/ibmecho -- parses w/ the json library used by IBM's EHR
/hapiecho -- parses w/ underlying json library used by HAPI
/hapiechoresource -- parses w/ a higher level HAPI json parser, which strips out unknown keys
/openmrsecho -- parser for openmrs (which is the same parser as hapi)