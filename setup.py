from distutils.core import setup
setup(
  name = 'liz',
  packages = ['liz'],
  version = '0.931',
  description = 'A tool for creating websites',
  author = 'Alex Stachowiak',
  author_email = 'liz@infovomit.com',
  url = 'https://github.com/stakodiak/liz',
  keywords = ['static', 'site', 'generator'],
  install_requires = ['jinja2', 'PyYAML'],
  entry_points={
    'console_scripts': [
      'liz = liz.main:main',
    ],
  },
)
