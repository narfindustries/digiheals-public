This implements a clojure server that uses blaze's json parser and
echos back the json as a string

To run: `make run`

Then send a POST request with json in the body to
`http://localhost:3000/blazeecho` (or
`http://localhost:8282/blazeecho` if running from docker).

`curl -X POST -d '{"resourceType": "Parameters", "foo": {"resource": "sdf"}}' http://localhost:8282/blazeecho`
