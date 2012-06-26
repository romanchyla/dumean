"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

import os
import time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

if 'SECRET_KEY' in os.environ:
    app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
else:
    app.config['SECRET_KEY'] = 'this_should_be_configured'


###
# Routing for your application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html')


###
# The functions below should be applicable to all Flask apps.
###

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=600'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404

@app.route('/<path:path>')
def site(path):
    print "serving, " , path
    return app.send_static_file('/static/' + path)


_applications = {}
import dumean

@app.route('/suggest/<name>')
def suggest_ui(name):
    """Send your auto-suggest file."""
    file_dot_html = 'au-' + name + '.html'
    return render_template(file_dot_html), 200


@app.route('/suggest/<app_name>.py', methods=["GET","POST"])
def suggest(app_name):
    worker = None
    if app_name not in _applications:
        module = __import__("dumean.apps.%s" % app_name, globals=globals(), locals=locals())
        if module is None or not hasattr(module.apps, app_name):
            raise Exception("There is no handler for: %s" % app_name)
        get_worker = getattr(getattr(module.apps, app_name), 'get_worker')
        _applications[app_name] = get_worker()

    worker = _applications[app_name]
    
    dumean.start_jvm()
    dumean.attach()
    
    query = None
    if request.args['term']:
        query = request.args
    else:
        return render_template('404.html'), 404
    
    start = time.time()
    if 'term' in query and len(query['term']):
        if 'data' in query: # 2nd level lookup
            data = worker.get_similar(query['term'], data=query['data'])
        else:
            data = worker.get_suggestions(query['term'])
    else:
        data = []

    if data:
        t = '<%.6f s>' % (time.time() - start)
        data.append({'label': t, 'value': t})

    return worker.format(data), 200
    
    


if __name__ == '__main__':
    app.run(debug=True)
