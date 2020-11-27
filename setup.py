from setuptools import setup, find_packages

setup(
    name='NOMADSExplorer',
    version='0.1',
    packages=find_packages(include=['NOMADSExplorer', 'NOMADSExplorer.*', 'explore', 'explore.*']),
    url='https://github.com/christophertubbs/NOMADSExplorer',
    license='GPL 3.0',
    author='Christopher Tubbs',
    author_email='',
    description='Library for looking through, discovering, and loading NetCDF data in the National '
                'Water Model NOMADS file structure ',
    install_requires=[
        'certifi>=2020.6.20',
        'chardet>=3.0.4',
        'idna>=2.10',
        'numpy>=1.19.1',
        'pandas>=1.1.0',
        'python-dateutil>=2.8.1',
        'pytz>=2020.1',
        'requests>=2.24.0',
        'scipy>=1.5.2',
        'six>=1.15.0',
        'urllib3>=1.25.10',
        'xarray>=0.16.0',
        'beautifulsoup4>=4.9.1'
    ]
)
