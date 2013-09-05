#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='django-fancypages',
    version=":versiontools:oscar_mws:",
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
        'django-oscar>=0.5',
        'boto>=2.10.0',
        'lxml>=3.2.3',
        'beautifulsoup>=3.2.1',
        'python-dateutil>=2.1',
    ],
    setup_requires=[
        'versiontools>=1.8',
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
