dumean
======

Did you mean autocomplete/autosuggest service


This is a toy-application that uses Lucene to provide fast and smart
autosuggest service and Python to pull all parts together quickly.

Based on: 

github.com/zachwill/flask_heroku





You will need:

Python (>= v2.5)
jcc 
pylucene (>= v3.1)
Java (>= v1.6)

ConfigParser (sudo pip install ConfigParser)


1. build the dictionary that is used for autocompletion/suggestions

cd ./indices
python generate_random_data.py demo


2. index the dictionary (create a special spellchecking index)

java -jar newseman.lucene.whisperer.IndexDictionary ./indices/random ./indices/random.seman

