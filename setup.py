from setuptools import setup

setup(
    name='pyraml-parser',
    version='0.0.5',
    author='Andrii Degtiarov',
    author_email='andrew.degtiariov@gmail.com',
    packages=['pyraml'],
    url='https://github.com/an2deg/pyraml-parser',
    license='MIT',
    description='Python parser for RAML.',
    long_description=open('README.md').read(),
    install_requires=[
        'setuptools',
        'PyYAML>=3.10',
        'importhelpers>=0.2'
    ],
    tests_require=['nose>=1.3.0'],
    zip_safe=True,
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
)
