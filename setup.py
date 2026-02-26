__author__ = 'sunary'


import os
import re
from setuptools import setup, find_packages

# Read VERSION without importing the package (avoids dependency resolution during build)
def _get_version():
    for base in (os.path.dirname(os.path.abspath(__file__)), os.getcwd()):
        init_py = os.path.join(base, 'flask_optimize', '__init__.py')
        if os.path.exists(init_py):
            with open(init_py) as f:
                match = re.search(r"VERSION\s*=\s*['\"]([^'\"]*)['\"]", f.read())
                if match:
                    return match.group(1)
    return '0.0.0'

VERSION = _get_version()


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
    python_requires='>=3.9',
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
    install_requires=['Flask>=3.1.3',
                      'minify-html>=0.11.0'],
    extras_require={
        'test': ['pytest>=7.0', 'black>=24.0'],
    },
)