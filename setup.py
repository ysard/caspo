#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Caspo
# Copyright (c) 2014-2016, Santiago Videla
#
# This file is part of caspo.
#
# caspo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# caspo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with caspo.  If not, see <http://www.gnu.org/licenses/>.
"""Installation module for Caspo program."""

from setuptools import setup, find_packages
import caspo

def load_requirements():
    """Load requirements.txt file and return a list of lines in this file"""
    with open('requirements.txt') as f_d:
        return [line.rstrip() for line in f_d]

setup(
    name=caspo.__package__,
    version=caspo.__version__,
    description=caspo.__description__,
    author=caspo.__author__,
    author_email=caspo.__email__,
    url=caspo.__url__,
    long_description=open("README.md").read(),
    classifiers=[
        "Intended Audience :: Science/Research",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='logical signaling networks systems biology answer set programming',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': ['caspo=caspo.console.main:run'],
    },
    install_requires=load_requirements(),
)
