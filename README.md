# Madrid Fines Manager

### Author: Daniel Alvarez Navarro

## What this project is about:

This project helps manage and analyze public traffic fine data provided by the Madrid City Council through its website https://datos.madrid.es/

The information is detailed by month and year, including as much detail as possible about each fine, in compliance with data protection regulations.

The Python package includes:
  - traffic_fines: This package includes two sub-packages:
    - madrid_fines: This consists of the MadridFines.py class. This class helps manage fines using pandas DataFrames. 
    - cache: This consists of two classes:
      - Cache.py: This class helps manage data by storing it temporarily for faster access once it has been retrieved at least once.
      - CacheUrl: This class inherits from Cache.py and is specifically designed to efficiently handle URLs.

## Documentation and tests

Each method in each class has been documented so that its functionality can be understood.
In some cases, examples and tests are included within the method definition itself.
If a test is not included in the method definition, it can be found in the tests/ folder.

The /tests/ folder contains tests for each of the implemented classes:
- test_cache.py
- test_cache_url.py
- test_madrid_fines.py

In this folder we will also find the FIXTURES directory, which contains the content used to mock web requests to the Madrid City Council website.
Thus, whenever the MadridFines class attempts to access a Madrid City Council URL, a mocked response is returned to avoid external requests during testing.

It is also worth mentioning that in the tests, I used pytest fixtures: requests_mock and tmp_path, to handle request mocking and temporary test file creation.

The tests can be executed as follows:

```
# run all tests at once and see coverage

$ pytest tests --cov=traffic_fines --cov-report=term-missing

# run tests separately

$ pytest tests/test_madrid_fines.py
```

## Technical decisions

- To minimize errors and properly normalize the data, I decided to replace hyphens "-" in column names with underscores "_".
- I decided to implement the Cache class with the option to initialize it by defining the base cache directory, to provide greater flexibility. However, it is not necessary to pass this argument, and by default it will initialize to Path.home() / ".my_cache". 
- To define class private attributes, I implemented them as strict private attributes, with getters to allow reading values both inside and outside the class, but without setters, so that values can only be modified from within the class. 
- In the Add method of the MadridFines class, when no month is specified and we attempt to add all months present in a given year, if an error occurs, we catch the exception, log a warning, and continue adding the next month.

## How it works

To understand how it works, please check the Jupyter notebook [how_it_works.ipynb](how_it_works.ipynb), where the creation and usage of the `Cache`, `CacheUrl`, and `MadridFines` classes are detailed with multiple examples.

Please Note that you might need to install jupyter package
```
python3 -m pip install jupyter
```
