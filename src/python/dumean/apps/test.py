import sysprint sys.pathimport simplejsondata =  [['invenio_', 'kw:invenio', 0.87],          ['inveniam', 'kw:alas', 0.8444444444444],          ['inveniemus', 'kw:inveniemus', 0.777777],          ['inpenio latin', 'kw:(inpenio latin)', 0.66666666666],          ['inventions', 'kw:inventions', 0.23535],          ['invenio technology', 'text:"invenio technology"', 0.23000000000],          ['invenit', 'kw:invenit', 0.12123232],          ['invenio therapeutics', 'kw:(invenio therapeutics)', 0.2000005],          ['invenire', 'kw:invenire', 0.056565],          ['invenio media', 'kw:(invenio media)', 0.001214]]def application(environ, start_response):    status = '200 OK'    output = '[["invenio_", "kw:invenio", 0.87], ["inveniam", "kw:alas", 0.84444444444440003], ["inveniemus", "kw:inveniemus", 0.77777700000000005], ["inpenio latin", "kw:(inpenio latin)", 0.66666666665999996], ["inventions", "kw:inventions", 0.23535], ["invenio technology", "text:\"invenio technology\"", 0.23000000000000001], ["invenit", "kw:invenit", 0.12123232], ["invenio therapeutics", "kw:(invenio therapeutics)", 0.2000005], ["invenire", "kw:invenire", 0.056564999999999997], ["invenio media", "kw:(invenio media)", 0.001214]]'    response_headers = [('Content-type', 'text/plain'),                        ]    start_response(status, response_headers)    data = map(lambda x: {'label': x[0], 'value':x[1], 'i':x[2]}, data)    return [simplejson.dumps(data)]class Test():    def get_suggestions(self, *args):        return data    def format(self, data):        return simplejson.dumps(data)    def get_worker():    return Test()   """LogLevel infoLoadModule wsgi_module modules/mod_wsgi.soWSGIScriptAliasMatch ^/du/([^/]+).py c:/dev/workspace/newseman/tmp/$1.py<IfModule alias_module>    Alias /du "c:/dev/workspace/newseman/tmp/dumean"    <Directory "c:/dev/workspace/newseman/tmp/dumean">        <IfModule php5_module>            php_admin_flag safe_mode off        </IfModule>        Order deny,allow        Deny from all        Allow from localhost        Options All        AllowOverride All        AddHandler wsgi-script .py    </Directory></IfModule><IfModule mime_module>    AddHandler cgi-script .cgi .pl .asp .py    ScriptInterpreterSource registry    PassEnv PYTHONPATH    SetEnv PYTHONUNBUFFERED 1</IfModule>"""if __name__ == '__main__':    w = get_worker()    d = w.get_suggestions()    print w.format(d)