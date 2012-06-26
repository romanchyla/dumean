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



INSTALLATION

$ git clone https://github.com/romanchyla/dumean.git
$ ant build-unpack
$ export PYTHONPATH=./src/python:./build/dist
$ python reindex.py all
$ python app.py

go to localhost:5000 and test



NOTES:

to run the java manually:

java -jar build/dist/dumean-standalone.jar newseman.lucene.whisperer.IndexDictionary ./indices/random ./indices/random.seman

