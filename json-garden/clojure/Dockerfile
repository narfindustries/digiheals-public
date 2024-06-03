FROM clojure:temurin-8-lein-alpine

COPY clojure-json-echo /clojure-json-echo/

WORKDIR /clojure-json-echo

RUN lein uberjar

CMD lein run server