from setuptools import setup

setup(
    name='pyraml-parser',
    version='0.0.1',
    author='Andrii Degtiarov',
    author_email='andrew.degtiariov@gmail.com',
    packages=['pyraml-parser'],
    url='https://github.com/an2deg/pyraml-parser',
    license='MIT',
    description='Python parser for RAML.',
    long_description=open('README').read(),
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
)
