#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='django-oscar-mws',
    version="0.1.0",
    url='https://github.com/tangentlabs/django-oscar-mws',
    author="Sebastian Vetter",
    author_email="sebastian.vetter@tangentsnowball.com.au",
    description="Integrating Oscar with Amazon MWS",
    long_description='\n\n'.join([
        open('README.rst').read(),
        open('CHANGELOG.rst').read(),
    ]),
    keywords="django, Oscar, django-oscar, Amazon, MWS, fulfilment",
    license='BSD',
    platforms=['linux'],
    packages=find_packages(exclude=["sandbox*", "tests*"]),
    include_package_data=True,
    install_requires=[
        'django-oscar',
        'xmltodict',
        'beautifulsoup>=3.2.1',
        'python-dateutil>=2.1',
    ],
    # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python',
    ]
)
