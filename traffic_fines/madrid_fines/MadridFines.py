"""
This module contains the class responsible for analysis of the published data of Madrid traffic fines
 by the Madrid Townhall at https://datos.madrid.es/
"""

import pandas as pd, io
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from ..cache.CacheUrl import CacheUrl
from bs4 import BeautifulSoup
import re
import numpy as np
import logging

# No need to use separate raiz as it is always included in the urls we use
MADRID_FINES_URL = "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/downloads"
MONTHS = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre"
}

class MadridError(Exception):
    """Madrid Fines base exception"""
    pass

def get_url(year: int, month: int) -> str:
    """
    It finds specific download url of a csv file that provides all madrid fines for a specific year and month
    based on public data from datos.madrid.es
    :param year: The year the fines were filed
    :param month: The month the fines were filed
    :return: a String with the url of a csv containing madrid traffic fines for a given year and month
    """
    response = requests.get(MADRID_FINES_URL)
    if response.status_code != 200:
        raise MadridError(f"There was an error with status: {response.status_code} while connecting to the url: {MADRID_FINES_URL}")

    soup = BeautifulSoup(response.text, 'html.parser')
    links = list()
    # pattern = re.compile(f"^Multas de circulación: detalle. {year} {MONTHS[month]}. Detalle")
    pattern = re.compile(f"Detalle. {MONTHS[month]} {year}")
    for a in soup.find_all('a', title=pattern):
        links.append(a['href'])

    if len(links) == 0:
        raise MadridError(f"No madrid fines file found for year: {year} and month: {month}")

    url = build_download_csv_url(links[0])
    return url

def build_download_csv_url(href: str) -> str:
    """
    Gets a traffic fines download csv url for a specific month and year
    :param href: traffic fines details url for specific month and year
    :return: the download url for the traffic fines csv file

    Examples
    ---------
    >>> build_download_csv_url("dataset/210104-0-multas-circulacion-detalle/resource/file-name-csv")
    'https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/file-name-csv/download/file-name-csv.csv'
    """
    # Get the csv file name, since it is the last part of the url
    file_name = str.split(href, "/")[-1]
    # build missing part of the csv file
    url = f"https://datos.madrid.es{href}/download/{file_name}.csv"
    return url


class MadridFines:
    """
    Manages traffic fines from Madrid Townhall coming from public data.
    Automates the fine's analysis: downloads, processing, summaries and statistical graphs generation
    """
    def __init__(self, app_name: str, obsolescence: int) -> None:
        """
        Initializes a MadridFines instance
        :param app_name: used to initialize cache_url app_name
        :param obsolescence: used to initialize cache_url obsolescence
        """
        if not app_name:
            raise MadridError("app_name cannot be empty")
        if not obsolescence:
            raise MadridError("obsolescence cannot be empty")

        self.__cache_url = CacheUrl(app_name, obsolescence)
        self.__data = pd.DataFrame()
        self.__loaded = list()

    @property
    def cache_url(self) -> CacheUrl:
        """Getter for cache_url property"""
        return self.__cache_url

    @property
    def data(self) -> pd.DataFrame:
        """Getter for data property"""
        return self.__data

    @property
    def loaded(self) -> list:
        """Getter for loaded property"""
        return self.__loaded

    @staticmethod
    def __load(year: int, month: int, cache_url) -> pd.DataFrame:
        """
        Generates a new dataframe fetching the fines data from cache_url for the specified year and month.
        :param year: Year of the fines to be fetched
        :param month: Month of the fines to be fetched
        :param cache_url: url to fetch the data
        :return: a new dataframe with the new fines data
        """
        year_month_url = get_url(year, month)
        content = cache_url.get(year_month_url)
        io_content = io.StringIO(content)
        fines = pd.read_csv(io_content, sep=None, engine="python", encoding='latin1')
        return fines

    @staticmethod
    def __clean(df: pd.DataFrame) -> None:
        """
        It takes a dataframe, cleans the column names removing unnecessary white spaces.
        Also fixes and converts values its proper datatype.
        Finally, it also adds a new column Fecha which contains a datetime created from existing separate columns
        as MES, ANIO and HORA, and using DAY=1
        :param df: Dataframe where the cleaning and updates will be done.
        :return: Does not return anything as the changes are done within the given dataframe.
        """

        # Fix whitespaces within column names
        # To avoid problems with columns that sometimes use "-" and other times use "_"
        # we will use only "_" from now on, replacing existing dashes and replacing
        # we are also preventing from null byte errors that I found out while testing different files
        df.rename(columns=lambda val: val.replace("\x00", "").strip().replace("-", "_"), inplace=True)

        # Convert speed values to int, assign Nan if conversion not possible.
        df["VEL_LIMITE"] = pd.to_numeric(df["VEL_LIMITE"], errors="coerce", downcast="integer")
        df["VEL_CIRCULA"] = pd.to_numeric(df["VEL_CIRCULA"], errors="coerce", downcast="integer")

        # Convert coordinates values to float, assign Nan if conversion not possible.
        df["COORDENADA_X"] = pd.to_numeric(df["COORDENADA_X"], errors="coerce", downcast="float")
        df["COORDENADA_Y"] = pd.to_numeric(df["COORDENADA_Y"], errors="coerce", downcast="float")

        # Create a new column Fecha of dtype datetime which combines existing columns Mes and ANIO and use constant Day as 1.
        df["FECHA"] = df.apply(
            lambda row: datetime(
                row.ANIO, # Year
                row.MES, # Month
                1, # Day
                int(row.HORA), # Hour
                int((row.HORA - int(row.HORA)) * 100) # Minutes
            ), axis=1
        )

    def add(self, year: int, month: int|None) -> None:
        """
        Adds traffic Fines information to data, from specific month and year of for all months in a specific year when month is not provided
        It also adds the (year, month) tuple into loaded.
        :param year: Year of the fines to be added
        :param month: Month of the fines to be added
        :return: Returns None, change are done within the instance data
        """
        if month is None:
                for mon in range(1, 13):
                    try:
                        self.__add_month_year(year, mon)
                    except MadridError as err:
                        # Log the issue when a month is missing and move to the next one
                        logging.warning(f"Could not add the data for year: {year} and month: {mon}. Error: {err}")
        else:
            self.__add_month_year(year, month)

    def __add_month_year(self, year: int, month: int) -> None:
        """
        Helper for the `add` method that adds traffic fines information for a specific month and year to the data property.
        :param year: int
        :param month: string
        :return: None
        """
        new_fines = MadridFines.__load(year, month, self.cache_url)
        MadridFines.__clean(new_fines)
        if self.data.empty:
            self.__data = new_fines
            self.__loaded.append((year, month))
            return None

        existing_data = ((self.data["MES"] == month) & (self.data["ANIO"] == year)).any()
        if not existing_data:
            self.__data = pd.concat([self.data, new_fines])
            # We need to reset the index to avoid duplicated index
            self.__data.reset_index(inplace=True, drop=True)
            self.__loaded.append((year, month))
        return None

    def fines_hour(self, fig_name: str) -> None:
        """
        Generates a line graph that shows the evolution of fines through the day by hours.
        When multiple months loaded it draws a line per month.
        It also stores the graph as a new file taking the fig_name to name it (fig_name.png)
        :param fig_name: Name as a string that will be used to store the image with the graph
        :return: Stores the generated graph in a new file fig_name.png, in the project's root
        """
        # rename column to display it correctly in the graph
        fines_by_hour = self.data.rename(columns={"ANIO": "AÑO"})
        # group by Mes, Año, and Hora. Use only the integer part of Hora to group by hour and discard the minutes
        fines_by_hour = fines_by_hour.groupby(["MES", "AÑO", fines_by_hour["HORA"].astype(int)]).size().unstack([0, 1])
        fines_by_hour.plot(title="Multas a lo largo del dia por mes y año")
        plt.savefig(f"{fig_name}.png")

    def fines_qualification(self) -> pd.DataFrame:
        """
        Analyses traffic fines levels by month and year.
        :return: Returns a new dataframe containing the number of fines of a certain qualification by month and year
        """
        # I used unstack() to have qualification levels as columns
        df = self.__data.groupby(["MES", "ANIO", "CALIFICACION"]).CALIFICACION.size().unstack()
        df.rename(columns=lambda val: val.strip(), inplace=True)
        return df

    def total_payment(self) -> pd.DataFrame:
        """
        Generates a summary with the maximum (considering discounts have been applied) and the minimum (considering none discounts applied) total fine charges within a month and year.
        :return: returns a new dataframe containing the max and min fine payments for each month and year.
        """
        self.__data["IMP_BOL_MIN"] = np.where(
            self.data["DESCUENTO"] == "SI",
            self.data["IMP_BOL"] / 2,
            self.data["IMP_BOL"]
        )

        return self.data.groupby(["MES", "ANIO"]).agg(
            MAX_IMPORT=("IMP_BOL", "sum"),
            MIN_IMPORT=("IMP_BOL_MIN", "sum")
        )

    def clear_cache(self) -> None:
        """It clears the cached data"""
        self.cache_url.clear()

    def __str__(self):
        """
        Provides information about the data stored in the instance
        :return: string
        """
        return (
            f"Loaded months: {self.loaded} \n"
            f"Data has the next columns: {self.data.columns} \n"
            f"Data has a shape of: {self.data.shape} \n"
            "Below you can see a sneak peak of the loaded data: \n"
            f"{self.data.head()} \n"
        )

