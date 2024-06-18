(defproject clojure_example "0.1.0-SNAPSHOT"
  :description "An example project demonstrating how to build a REST API in Clojure"
  :url "https://innovationgroup.tech"
  :license {:name "MIT"
    :url "https://github.com/kenreilly/clojure-example/blob/master/LICENSE"}
  :dependencies [
                 [org.clojure/clojure "1.10.0"]
                 [org.clojure/data.json "0.2.6"]
                 [ring/ring-defaults "0.3.2"]
                 [ring/ring-devel "1.6.3"]
                 [ring/ring-json "0.5.0"]
                 [compojure "1.6.1"]
                 [http-kit "2.3.0"]
                 [com.fasterxml.jackson.datatype/jackson-datatype-jsr310 "2.17.1"]
                 [metosin/jsonista "0.3.8"]
                 [lynxeyes/dotenv "1.0.2"]]
  :main ^:skip-aot clojure-example.core
  :target-path "target/%s"
  :profiles {:uberjar {:aot :all} :dev {:main clojure-example.core/-dev-main}})
