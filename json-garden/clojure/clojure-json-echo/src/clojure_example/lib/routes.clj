(ns clojure-example.lib.routes
  (:require
   [compojure.core :refer :all]
   [compojure.route :as route]
   [clojure.pprint :as pp]
   [clojure.string :as str]
   [clojure.data.json :as json]
   [clojure-example.lib.api :as api]
   [jsonista.core :as j])                
  (:import
   [com.fasterxml.jackson.core JsonFactory StreamReadConstraints]
   [com.fasterxml.jackson.databind DeserializationFeature ObjectMapper ObjectWriter])
  (:gen-class))
(def ^:private stream-read-constraints
  (-> (StreamReadConstraints/builder)
      (.maxStringLength 5e7)
      (.build)))

(def ^:private json-factory
  (-> (JsonFactory/builder)
      (.streamReadConstraints stream-read-constraints)
      (.build)))

(def ^:private json-object-mapper
  (doto (ObjectMapper. json-factory)
    (.enable DeserializationFeature/USE_BIG_DECIMAL_FOR_FLOATS)
    (.enable DeserializationFeature/FAIL_ON_TRAILING_TOKENS)))


(defn blazeecho-route
        "Decode then echo back the json"
  [req]
        {:status 200
         :headers {"Content-Type" "text/plain"}
         :body (-> (j/write-value-as-string (j/read-value (String. (.bytes (req :body))) json-object-mapper)))})
