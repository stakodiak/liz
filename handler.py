#!/usr/bin/python
"""usage: liz <command> [<args>]"""
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
            path += config['path-suffix']
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
        loader = env.get_template(route['template'])
        content = loader.render(route.get('data', {}))
        path = get_path(route)
        with open(build_dir + path, 'w') as f:
            content = content.encode('utf8')
            f.write(content)

def main(argv):
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

if __name__ == '__main__':
    main(sys.argv[1:])
