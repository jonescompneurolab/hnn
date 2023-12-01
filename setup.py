#! /usr/bin/env python

from setuptools import setup, find_packages

descr = """Human Neocortical Neurosolver"""

DISTNAME = 'hnn'
DESCRIPTION = descr
MAINTAINER = 'Blake Caldwell'
MAINTAINER_EMAIL = 'blake_caldwell@brown.edu'
URL = ''
LICENSE = 'Brown CS License'
DOWNLOAD_URL = 'http://github.com/jonescompneurolab/hnn'
VERSION = '1.4.0'

if __name__ == "__main__":
    setup(name=DISTNAME,
          maintainer=MAINTAINER,
          maintainer_email=MAINTAINER_EMAIL,
          description=DESCRIPTION,
          license=LICENSE,
          url=URL,
          version=VERSION,
          download_url=DOWNLOAD_URL,
          long_description=open('README.md').read(),
          classifiers=[
              'Intended Audience :: Science/Research',
              'License :: OSI Approved',
              'Programming Language :: Python',
              'Topic :: Scientific/Engineering',
              'Operating System :: Microsoft :: Windows',
              'Operating System :: POSIX',
              'Operating System :: Unix',
              'Operating System :: MacOS',
          ],
          platforms='any',
          packages=find_packages(),
          package_data={'hnn':
                        ['../param/*.param']},
          install_requires=['nlopt',
                            'psutil',
                            'pyqt5']
          )
