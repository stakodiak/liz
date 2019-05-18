#!/usr/bin/python
"""usage: liz <command> [<args>]

commands:
    init <name>  Creates a standard web project
    build  Generates templates according to liz config
"""
import json
import os
import getopt
import sys


SAMPLE_STYLES_SCSS = """
/* resets */
html, body, h1, h2, h3, h4, h5, h6 {
  margin: 0;
  padding: 0;
}

/* SASS stuff */
@mixin bg-image-2x($path, $ext: "png") {
  $at1x_path: "#{$path}.#{$ext}";
  $at2x_path: "#{$path}@2x.#{$ext}";
  background-image: url("#{$at1x_path}");

  @media all and (-webkit-min-device-pixel-ratio : 1.5),
         all and (-o-min-device-pixel-ratio: 3/2),
         all and (min--moz-device-pixel-ratio: 1.5),
         all and (min-device-pixel-ratio: 1.5) {
    background-image: url("#{$at2x_path}");
  }
}

/* typography */
html, body {
  font-kerning: normal;
  font-feature-settings: "kern";
  -webkit-font-feature-settings: "kern";
  font-smoothing: antialiased;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
"""

# TODO:  give this puppy a port lookup. these project absolutely should
# be stateless.
SAMPLE_MAKEFILE = """
s3_bucket_name = www.cedriceats.com
deploy:
	s3put -b $(s3_bucket_name) --header "Content-Type=text/html" -p "`pwd`/build" build/*
	s3put -b $(s3_bucket_name) -p "`pwd`" assets/css/
deploy-assets:
	s3put -b $(s3_bucket_name) -p "`pwd`" assets/*
clean:
	rm -fr build/
port = 8809
run:
	open -a 'Google Chrome' "http://localhost:$(port)"
	python -m SimpleHTTPServer $(port)
"""

SAMPLE_BASE_TEMPLATE = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<!-- jQuery -->
<script src="https://code.jquery.com/jquery-3.1.1.min.js" ></script>

<!-- Bootstrap CSS -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

<!-- Bootstrap JS -->
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>

<title>{% block title %}{% endblock %}</title>
<link rel="stylesheet" href="/assets/css/styles.css">

<body>
  {% block content %}
  {% endblock %}
</body>
"""

SAMPLE_HOME_TEMPLATE = """
{% extends "base.html" %}

{% block title %}Home{% endblock title %}
{% block content %}

{% endblock content %}
"""

SAMPLE_ROUTES = """
{
  "routes": [
    {
      "path": "index.html",
      "template": "home.html",
      "data": {
        "fish": "sticks"
      }
    }
  ]
}
"""
config_fn = '.liz.config'

SAMPLE_CONFIG = """
{
  "routes": "routes.json",
  "templates": "templates",
  "build": "build/"
}
"""

IS_VERBOSE = True

def _pprint(data):
    import json
    print json.dumps(data, indent=2)

def _fatal(msg):
    print("fatal: " + msg)
    sys.exit(1)

def init(opts, args):
    """Initialize empty liz project.

    This creates the required file hierarchy:
        .liz.config
        /templates
        routes.json

    This can be used as a starting point for developing a static site.
    You can create a Makefile to handle deployments once the build is
    finished. Another good idea is to create an assets/ directory to
    handle static files like JS, SCSS and images. The Makefile can
    deploy each of these separately.
    """
    if os.path.exists(config_fn):
        _fatal("project already initialized.")
    with open(config_fn, 'w') as f:
        f.write(SAMPLE_CONFIG)
    ## TODO: put build dir, templates dir in liz config
    # Make sure you don't overwrite this file, ya dingus.
    default_routes_fn = 'routes.json'
    with open(default_routes_fn, 'w') as f:
        f.write(SAMPLE_ROUTES)

    # Make sure the project has a Makefile.
    with open('Makefile', 'w') as f:
        f.write(SAMPLE_MAKEFILE)

    # Start the project off with a SCSS snippet.
    styles_dir = 'assets/css'
    try:
        os.makedirs(styles_dir)
    except OSError:
        if not os.path.isdir(styles_dir):
            raise
    sample_styles_fn = 'styles.scss'
    with open(os.path.join(styles_dir, sample_styles_fn), 'w') as f:
        f.write(SAMPLE_STYLES_SCSS)

    # Write starter templates so you can get running.
    templates_dir = json.loads(SAMPLE_CONFIG)['templates']
    try:
        os.makedirs(templates_dir)
    except OSError:
        if not os.path.isdir(templates_dir):
            raise

    sample_base = 'base.html'
    with open(os.path.join(templates_dir, sample_base), 'w') as f:
        f.write(SAMPLE_BASE_TEMPLATE)

    sample_home_template = 'home.html'
    with open(os.path.join(templates_dir, sample_home_template), 'w') as f:
        f.write(SAMPLE_HOME_TEMPLATE)

def build(opts=None, args=None):
    """Build a liz project.
    Args:
        `opts` Global options passed to liz.
        `args` Options supplied after command.
    """
    import getopt
    import json
    import os
    import sys
    from jinja2 import Environment, FileSystemLoader

    # Make sure we're in a liz project and it's properly configured.
    if not os.path.exists(config_fn):
        print "fatal: not a liz project."
        sys.exit(1)
    config = None
    with open(config_fn, 'r') as f:
        content = f.read()
        data = json.loads(content)
        config = data
    if not config:
        _fatal("couldn't parse project config.")

    # Parse command arguments.
    try:
        nopts, nargs = getopt.getopt(args,
            "vhs:", ["verbose', help", "path-suffix="])
        if nargs:
            _fatal("'build' doesn't accept any arguments.")
    except getopt.GetoptError:
        print __doc__
        sys.exit(1)
    options = sum([opts + nopts], [])
    for opt, arg in options:
        if opt in ('-h', '--help'):
            print __doc__
            sys.exit()
        elif opt in ('-s', '--path-suffix'):
            config['path-suffix'] = arg
        elif opt in ('-v', '--verbose'):
            pass
    print options
    if IS_VERBOSE:
        print 'build config =>'
        print options

    # Look for Jinja templates in 'templates/'.
    if IS_VERBOSE:
        print 'liz config =>'
        print json.dumps(config, indent=2)
    templates_dir = config.get('templates')
    if not templates_dir:
        _fatal("malformed project config.")
    env = Environment(loader=FileSystemLoader(templates_dir))

    #TODO: This should be able to be specified by a command-line
    # argument.
    build_dir = config.get('build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)


    # Figure out which routes file to load from config.
    routes_fn = config.get('routes')
    routes = []
    with open(routes_fn, 'r') as f:
        routes_d = json.loads(f.read())
    if IS_VERBOSE:
        print "\nloaded routes =>"
        print json.dumps(routes_d, indent=2)

    # Build list of routes.
    urls = {}  # for finding routes in the template
    env.globals['url'] = lambda name: urls[name]

    def get_path(route):
        path = route.get('path') or path.get('name')
        if 'path-suffix' in config:
            suffix = config['path-suffix']
            if not path.endswith(suffix) and not '://' in path:
                path += suffix
        return path
    try:
        # By default, the list of routes is an attribute called
        # "routes".
        routes = routes_d["routes"]
        for route in routes:
            if 'name' in route:
                name = route['name']
                urls[name] = get_path(route)
    except KeyError:
        _fatal("routes '%s' not in '%s'." % (route, routes_fn))
    if IS_VERBOSE:
        print "URLs =>"
        _pprint(urls)

    # Build project and render each route.
    for route in routes:
        template = route.get('template')
        # Some routes are for external routing.
        if not template:
            continue
        loader = env.get_template(template)
        content = loader.render(route.get('data', {}))
        path = get_path(route)
        with open(build_dir + path, 'w') as f:
            content = content.encode('utf8')
            f.write(content)

def main():
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv,
            "vhr:", ["verbose", "help", "routes="])
    except getopt.GetoptError:
        print __doc__
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print __doc__
            sys.exit()
        elif opt in ('-v', '--verbose'):
            IS_VERBOSE = True
            print 'opts ->'
            print opts
            print 'args ->'
            print args

    # Figure out which command to call.
    try:
        command = args.pop(0)
    except IndexError:
        print __doc__
        sys.exit()
    if command == 'init':
        init(opts, args)
    elif command == 'build':
        build(opts, args)
    else:
        _fatal("unknown command: " + command)

