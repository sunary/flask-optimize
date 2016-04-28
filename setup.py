__author__ = 'sunary'


import os
from setuptools import setup, find_packages
from pip.req import parse_requirements


def __path(filename):
    return os.path.join(os.path.dirname(__file__), filename)

build = 0
if os.path.exists(__path('build.info')):
    build = open(__path('build.info')).read().strip()

with open('README.md') as fo:
    readme = fo.read()

with open('LICENSE') as fo:
    license = fo.read()

with open('CHANGES.md') as fo:
    changes = fo.read()

version = '0.1.{0}'.format(build)

install_reqs = parse_requirements('requirements.txt', session=False)
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='flask-optimize',
    version=version,
    author='Sunary [Nhat Vo Van]',
    author_email='v2nhat@gmail.com',
    maintainer='Sunary [Nhat Vo Van]',
    maintainer_email='v2nhat@gmail.com',
    description='Flask optimization: cache, minify html and gzip response',
    license='MIT',
    keywords='flask, optimize, cache, minify html, gzip',
    url='https://github.com/sunary/flask-optimize',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=reqs,
    entry_points={},
)