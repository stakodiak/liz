#!/usr/local/bin/python3
"""usage: liz <command> [<args>]

commands:
    init <name>  Creates a standard web project
    build  Generates templates according to liz config

options:
    -h  Print this message
    -v  Print project info when building

docs: https://github.com/stakodiak/liz
"""
import json
import os
import getopt
import sys

from typing import Optional, Any, Dict

import yaml


import os
import yaml

class EnvYAMLTag(yaml.YAMLObject):
    yaml_tag = u'!env'
    def __init__(self, env_var):
        value = os.environ.get(env_var)
        self.value = value

    def __repr__(self):
        return self.value

    @classmethod
    def from_yaml(cls, loader, node):
        return EnvYAMLTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class ShellYAMLTag(yaml.YAMLObject):
    yaml_tag = u'!sh'
    def __init__(self, cmd_unsafe):
        import subprocess
        import shlex
        cmd = shlex.split(cmd_unsafe)
        output = subprocess.run(cmd, capture_output=True)
        self.value = output.stdout

    def __repr__(self):
        return self.value.decode('utf-8')

    @classmethod
    def from_yaml(cls, loader, node):
        return ShellYAMLTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class FileYAMLTag(yaml.YAMLObject):
    yaml_tag = u'!file'
    def __init__(self, filename):
        content = open(filename).read()
        self.value = content

    def __repr__(self):
        return self.value

    @classmethod
    def from_yaml(cls, loader, node):
        return FileYAMLTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class YAMLDocTag(yaml.YAMLObject):
    """
    Shapes structured and unstructured data into YAML object:
    
    """
    yaml_tag = u'!data-doc'
    def __init__(self, filename):
        content = open(filename).read()
        data, doc = (lambda args: args[0], ''.join(args[1:]))(content.split('==='))
        self.value = yaml.load(data)
        self.value['doc'] = doc

    def __repr__(self):
        return self.value

    @classmethod
    def from_yaml(cls, loader, node):
        return FileYAMLTag(node.value)

    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)



SAMPLE_STYLES_SCSS = """
/* resets */
* {
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

# TODO:  give this puppy a port lookup
SAMPLE_MAKEFILE = """
s3_bucket_name = # S3 bucket?
deploy:
	aws s3 sync build/ s3://$(s3_bucket_name) --cache-control no-cache
clean:
	rm -fr build/
port = 10101
run:
	open -a 'Google Chrome' "http://localhost:$(port)"
	python3 -m http.server $(port)
"""

SAMPLE_BASE_TEMPLATE = """
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

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

config_fn = 'liz.yml'

SAMPLE_CONFIG = """
templates: templates
build: build/
routes:
  - path: index.html
    template: "home.html"
    data:
      dish: sticks
"""

IS_VERBOSE = True

def _pprint(data):
    import json
    print(json.dumps(data, indent=2, default=str))

def _fatal(msg):
    print("fatal: " + msg)
    sys.exit(1)

def init(opts, args):
    """Initialize empty liz project.

    This creates the required file hierarchy:
        /templates
        liz.yml

    This can be used as a starting point for developing a
    static site.  You can create a Makefile to handle
    deployments once the build is finished. Another good
    idea is to create an assets/ directory to handle static
    files like JS, SCSS and images. The Makefile can deploy
    each of these separately.
    """
    if os.path.exists(config_fn):
        _fatal("project already initialized.")
    with open(config_fn, 'w') as f:
        f.write(SAMPLE_CONFIG)

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
    templates_dir = "templates"
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

def load_file(filename: str, filetype: Optional[str] = None) -> Dict[Any, Any]:
    data = None
    if not filetype:
        if filename.endswith('json'):
            filetype = "json"
        elif filename.endswith('yml') or filename.endswith('yaml'):
            filetype = "yaml"
    with open(filename, 'r') as f:
        content = f.read()
        if filetype == 'json':
            data = json.loads(content)
        elif filetype == 'yaml':
            data = yaml.load(content)
    return data

def build(opts=None, args=None) -> None:
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
        print("fatal: not a liz project.")
        sys.exit(1)

    # TODO Convert liz.config to yaml format
    config = load_file(config_fn, "yaml")
    if not config:
        _fatal("couldn't parse project config.")

    # Parse command arguments.
    try:
        nopts, nargs = getopt.getopt(args,
            "vhs:", ["verbose', help", "path-suffix="])
        if nargs:
            _fatal("'build' doesn't accept any arguments.")
    except getopt.GetoptError:
        print(__doc__)
        sys.exit(1)
    options = sum([opts + nopts], [])
    for opt, arg in options:
        if opt in ('-h', '--help'):
            print(__doc__)
            sys.exit()
        elif opt in ('-s', '--path-suffix'):
            config['path-suffix'] = arg
        elif opt in ('-v', '--verbose'):
            pass
    print(options)
    if IS_VERBOSE:
        print('build config =>')
        print(options)

    # Look for Jinja templates in 'templates/'.
    if IS_VERBOSE:
        print('liz config =>')
        _pprint(config)
    templates_dir = config.get('templates')
    if not templates_dir:
        templates_dir = "."
    env = Environment(loader=FileSystemLoader(templates_dir))

    # TODO This should be able to be specified by a
    # command-line argument.
    build_dir = config.get('build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    # Figure out which routes file to load from config.
    routes_fn = config.get('routes')
    routes = []
    if type(routes_fn) is str:
        routes_d = load_file(routes_fn)
    else:
        routes_d = routes_fn

    if IS_VERBOSE:
        print("\nloaded routes =>")
        _pprint(routes_d)

    # Build list of routes.
    urls = {}  # for finding routes in the template
    env.globals['url'] = lambda name: urls[name]
    global_data = config.get("data", {})
    env.globals['data'] = global_data

    template_globals = config.get("config")
    if template_globals:
        for k, v in template_globals.items():
            env.globals[k] = v

    def get_path(route):
        if 'page' in route:
            path = route.get('page')
        else:
            path = route.get('path') or route.get('name')
        if 'path-suffix' in config:
            suffix = config['path-suffix']
            if path.startswith('/'):
                path = path[1:]
            if not path.endswith(suffix) and not '://' in path:
                path += suffix
            if path.endswith("index.html"):
                path = path[:-len('index.html')]
        return path
    try:
        # By default, the list of routes is an attribute
        # called "routes".
        routes = routes_d
        for route in routes:
            if 'name' in route or 'page' in route:
                name = route.get('name') or route.get('page')
                urls[name] = get_path(route)
                is_absolute_url = '://' in get_path(route)
                if not is_absolute_url:
                    urls[name] = '/' + get_path(route)
            elif 'path' in route:
                urls[route['path']] = route['template']
    except KeyError:
        _fatal("routes '%s' not in '%s'." % (route, routes_fn))
    if IS_VERBOSE:
        print("URLs =>")
        _pprint(urls)

    # Build project and render each route.
    for route in routes:
        template = route.get('template')
        # Some routes are for external routing.
        if not template:
            continue
        #
        loader = env.get_template(template)
        data = global_data
        if route.get('data'):
            data.update(**route.get('data'))
            if IS_VERBOSE:
                _pprint(data)
        content = loader.render(data)

        path = os.path.join(build_dir, get_path(route))
        head, tail = os.path.split(path)
        os.makedirs(head, exist_ok=True)
        try:
            with open(path, 'wb') as f:
                content = content.encode('utf8')
                f.write(content)
        except IsADirectoryError:
            with open(path + 'index.html', 'wb') as f:
                content = content.encode('utf8')
                f.write(content)

def main() -> None:
    argv = sys.argv[1:]
    try:
        opts, args = getopt.getopt(argv,
            "vhr:", ["verbose", "help", "routes="])
    except getopt.GetoptError:
        print(__doc__)
        sys.exit(1)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print(__doc__)
            sys.exit()
        elif opt in ('-v', '--verbose'):
            IS_VERBOSE = True
            print('opts ->')
            print(opts)
            print('args ->')
            print(args)

    # Figure out which command to call.
    try:
        command = args.pop(0)
    except IndexError:
        print(__doc__)
        sys.exit()
    if command == 'init':
        init(opts, args)
    elif command == 'build':
        build(opts, args)
    else:
        _fatal("unknown command: " + command)


if __name__ == '__main__':
    main()

