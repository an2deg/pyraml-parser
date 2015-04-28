import os
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''


setup(
    name='pyraml-parser',
    version='0.1.2',
    author='Andrii Degtiarov',
    author_email='andrew.degtiariov@gmail.com',
    packages=['pyraml'],
    url='https://github.com/an2deg/pyraml-parser',
    license='MIT',
    description='Python parser for RAML.',
    long_description=README + '\n\n' + CHANGES,
    install_requires=[
        'setuptools',
        'PyYAML>=3.10',
        'importhelpers>=0.2'
    ],
    tests_require=['nose>=1.3.0'],
    zip_safe=True,
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
)
