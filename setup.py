from distutils.core import setup
setup(
  name = 'liz',
  packages = ['liz'], # this must be the same as the name above
  version = '0.5',
  description = 'A tool for creating websites',
  author = 'Alex Stachowiak',
  author_email = 'liz@stachowiak.email',
  url = 'https://github.com/stakodiak/liz', # use the URL to the github repo
  download_url = 'https://github.com/stakodiak/liz/archive/v0.1.tar.gz', # I'll explain this in a second
  keywords = ['static', 'site', 'generator'], # arbitrary keywords
  classifiers = [],
  entry_points={
    'console_scripts': [
      'liz = liz.main:main',
    ],
  },
)
