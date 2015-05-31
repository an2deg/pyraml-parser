pyraml-parser - Python parser to RAML, the RESTful API Modeling Language.


Introduction
============

Implementation of a RAML parser for Python based on PyYAML. It is compliant with RAML 0.8 http://raml.org/spec.html


Installation
============

The pyraml package can be installed with ``pip`` or ``easy_install`` from GIT repository or from tarball.

    $ pip install https://github.com/an2deg/pyraml-parser/archive/master.zip

For Python 2.6 packages ``ordereddict`` and 'lxml' should be installed:

    $ pip install ordereddict lxml


Developing pyraml-paser
-----------------------

You may need to install ``nose``, ``tox`` and ``mock`` packages to run pyraml-parser tests.

Typical installation process for developing purposes:

    $ git clone git@github.com:an2deg/pyraml-parser.git
    $ cd pyraml-parser
    $ pip install mock
    $ python setup.py develop

To run tests on all supported python versions:

    $ pip install tox
    $ tox

Or to run tests with ``nose``:

    $ pip install nose
    $ python -m nose

Or to run tests using ``unittest``:

    $ python setup.py test

Using pyraml-parser
===================

An instance of the ``RamlRoot`` object can be obtained by calling the ``pyraml.parser.load``
function:

    import pyraml.parser

    p = pyraml.parser.load('schema.raml')

    print p


MIT LICENSE
---

Copyright (c) 2011-2015 Jason Huck, Simon Georget
http://opensource.org/licenses/MIT

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
