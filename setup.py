__author__ = 'sunary'


import os
from setuptools import setup, find_packages


def __path(filename):
    return os.path.join(os.path.dirname(__file__), filename)

with open('README.md') as fo:
    readme = fo.read()

with open('LICENSE') as fo:
    license = fo.read()

with open('CHANGES.md') as fo:
    changes = fo.read()

build = 11
version = '0.1.{0}'.format(build)

setup(
    name='flask-optimize',
    version=version,
    author='Sunary [Nhat Vo Van]',
    author_email='v2nhat@gmail.com',
    maintainer='Sunary [Nhat Vo Van]',
    maintainer_email='v2nhat@gmail.com',
    platforms='any',
    description='Flask optimization: cache, minify html and gzip response',
    license='MIT',
    keywords='flask, optimize, cache, minify html, gzip',
    url='https://github.com/sunary/flask-optimize',
    packages=find_packages(exclude=['docs', 'tests*']),
    install_requires=['Flask>=0.10.1',
                      'htmlmin>=0.1.10'],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)