#!/usr/bin/python
"""
    testing some dope shit
"""
## TODO:
# 
import os
import getopt
import sys

SAMPLE_ROUTES = """
{
  "routes": [
    {
      "path": "index.html", 
      "data": {
        "fish": [
            "sticks"
        ]
      }, 
      "template": "home.html"
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

IS_VERBOSE = False

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

def _fatal_error(msg):
    import sys
    print "fatal: " + msg
    sys.exit(1)

def build(opts=None, args=None):
    import json
    import os
    import sys
    if not os.path.exists(config_fn):
        print "fatal: not a liz project."
        sys.exit(1)
    config = None
    with open(config_fn, 'r') as f:
        content = f.read()
        data = json.loads(content)
        config = data
    if not config:
        _fatal_error("couldn't parse project config.")

    from jinja2 import Environment, FileSystemLoader

    # Look for Jinja templates in 'templates/'.
    print config
    templates_dir = config.get('templates')
    if not templates_dir:
        _fatal_error("malformed project config.")
        
    env = Environment(loader=FileSystemLoader(templates_dir))

    # This should be able to be specified by a command-line argument.
    build_dir = config.get('build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    # By default, the list of routes is an attribute called
    # "routes". This can be overridden by supplying a `--routes`
    # option to the build.
    route = 'routes'
    for flag, value in opts:
        if flag == '--routes':
            route = value

    # Figure out which routes file to load from config.
    routes_fn = config.get('routes')
    routes = []
    with open(routes_fn, 'r') as f:
        routes_d = json.loads(f.read())

    # Build list of routes.
    try:
        routes = routes_d[route]
    except KeyError:
        _fatal("routes '%s' not in '%s'." % (route, routes_fn))
    print json.dumps(routes_d, indent=2)
    
    for route in routes:
        loader = env.get_template(route['template'])
        content = loader.render(route.get('data', {}))
        path = route['path']
        with open(build_dir + path, 'w') as f:
            content = content.encode('utf8')
            f.write(content)

def main(argv):
    try:
        opts, args = getopt.getopt(argv, 
            "vhr:", ["verbose', help", "routes="])
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
    if not args:
        build(opts)
    elif len(args) > 1:
        _fatal("too many commands supplied: " + str(args))
    else:
        command = args[0]
        if command == 'init':
            init(opts, args)
        elif command == 'build':
            build(opts, args)
        else:
            _fatal("unknown command: " + command)

if __name__ == '__main__':
    main(sys.argv[1:])
