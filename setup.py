#!/usr/bin/env python

from distutils.core import setup

setup(
    name='SRFax',
    version='0.1.1',
    description='SRFax (www.srfax.com) API library',
    long_description=open('README.rst').read(),
    author='Andjelko Horvat',
    author_email='comel@vingd.com',
    url='https://github.com/vingd/srfax-api-python',
    packages=['srfax'],
    install_requires=[i.strip() for i in open('requirements.txt').readlines()],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Internet',
        'Topic :: Communications :: Fax',
        'Topic :: Software Development :: Libraries :: Python Modules',
    )
)
