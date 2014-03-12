pyraml-parser - Python parser to RAML, the RESTful API Modeling Language.


Introduction
============

Implementation of a RAML parser for Python based on PyYAML. It is compliant with RAML 0.8


Installation
============

The pyraml package can be installed with ``pip`` or ``easy_install`` from GIT repository or from tarball.

    $ pip install https://github.com/an2deg/pyraml-parser/archive/master.zip


Developing pyraml-paser
-----------------------

You may need to install package ``nosetests`` for running pyraml-parser tests. The project provides helper script
``run-tests.py`` which executes all tests inside directory tests and it supports all ``nosetests`` parameters.

Typical installation process for developing purposes:

    $ git clone git@github.com:an2deg/pyraml-parser.git
    $ cd pyraml-parser
    $ pip install nosetests
    $ python setup.py develop


Using pyraml-parser
===================

An instance of the ``RamlRoot`` object can be obtained by calling the ``pyraml.parser.load``
function:

    import pyraml.parser

    p = pyraml.parser.load('schema.raml')

    print p


MIT LICENSE
---

Copyright (c) 2011-2013 Jason Huck, Simon Georget
http://opensource.org/licenses/MIT

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
