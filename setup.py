__author__ = 'sunary'


import os
from setuptools import setup, find_packages
from flask_optimize import VERSION


def __path(filename):
    return os.path.join(os.path.dirname(__file__), filename)


with open('README.md') as fo:
    readme = fo.read()

with open('LICENSE') as fo:
    license = fo.read()

with open('CHANGES.md') as fo:
    changes = fo.read()


setup(
    name='flask-optimize',
    version=VERSION,
    author='Sunary [Nhat Vo Van]',
    author_email='v2nhat@gmail.com',
    maintainer='Sunary [Nhat Vo Van]',
    maintainer_email='v2nhat@gmail.com',
    platforms='any',
    description='Flask optimization using cache, minify html and compress response',
    long_description='Flask optimization using cache, minify html and compress response\n',
    license=license,
    keywords='flask, optimize, cache, minify html, compress, gzip',
    url='https://github.com/sunary/flask-optimize',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=['Flask>=0.10.1',
                      'htmlmin>=0.1.10'],
)