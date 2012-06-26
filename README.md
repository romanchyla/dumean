dumean
======

Did you mean autocomplete/autosuggest service


This is a toy-application that uses Lucene to provide fast and smart
autosuggest service and Python to pull all parts together quickly.



You will need:

Python (>= v2.5)
pylucene (>= v3.1)  - see: http://lucene.apache.org/pylucene/
jcc (>=2.8)
Java (>= v1.6)

ConfigParser (sudo pip install ConfigParser)
Flask



INSTALLATION

First make sure you have lucene and JCC installed properly. Then do:

$ git clone https://github.com/romanchyla/dumean.git
$ ant build-unpack
$ export PYTHONPATH=./src/python:./build/dist
$ python reindex.py all
$ python app.py

Go to localhost:5000/suggest/all and test


Disclaimer: put together one July day, tested with Lucene 3.1 and JCC (2.8)

License: Apache 



NOTES:

to run the java manually:

java -jar build/dist/dumean-standalone.jar newseman.lucene.whisperer.IndexDictionary ./indices/random ./indices/random.seman

Flask is based on: github.com/zachwill/flask_heroku


