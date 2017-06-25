import json
import os
import sys

from jinja2 import Environment, FileSystemLoader

# Look for Jinja templates in 'templates/'.
env = Environment(loader=FileSystemLoader('templates'))

# This should be able to be specified by a command-line argument.
build_dir = 'build/'
if not os.path.exists(build_dir):
    os.makedirs(build_dir)

routes_fn = 'mosspark-routes.json'
routes = []
with open(routes_fn, 'r') as f:
    routes_d = json.loads(f.read())
    routes = routes_d['routes']
print json.dumps(routes_d, indent=2)
    
for route in routes:
    loader = env.get_template(route['template'])
    content = loader.render(route.get('data', {}))
    path = route['path']
    with open(build_dir + path, 'w') as f:
        f.write(content)

for route in routes:
    continue
    path, template = route[:2]
    content = render_template(template)
    loader = env.get_template(template)
    content = loader.render({1: 2})
    with open(build_dir + path, 'w') as f:
        f.write(content)
    
