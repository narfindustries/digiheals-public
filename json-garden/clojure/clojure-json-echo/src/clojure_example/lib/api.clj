(ns clojure-example.lib.api
  (:require 
    [compojure.core :refer :all]
    [compojure.route :as route]
    [clojure.pprint :as pp]
    [clojure.string :as str]
    [clojure.data.json :as cjson])
  (:gen-class))

