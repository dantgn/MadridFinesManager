import doctest
import pytest
from pathlib import Path
from traffic_fines.madrid_fines import *

def test_build_download_csv_url_doctest():
    doctest.run_docstring_examples(build_download_csv_url, globals(), verbose=True)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.mark.parametrize(
    "year, month, expected_url",
    [
        (2024, 12, "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv.csv"),
        (2024, 5, "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-339-multas-circulacion-detalle-csv/download/210104-339-multas-circulacion-detalle-csv.csv"),
    ]
)
def test_get_url(requests_mock, year, month, expected_url):
    url_html = (FIXTURES_DIR / "madrid_multas.html").read_text()
    requests_mock.get(MADRID_FINES_URL, text=url_html, status_code=200)

    download_url = get_url(year, month)
    assert download_url == expected_url


@pytest.mark.parametrize(
    "year, month",
    [
        (2022, 1),
        (1999, 2),
    ]
)
def test_get_url_date_error(requests_mock, year, month):
    with pytest.raises(MadridError):
        url_html = (FIXTURES_DIR / "madrid_multas.html").read_text()
        requests_mock.get(MADRID_FINES_URL, text=url_html, status_code=200)
        get_url(year, month)

@pytest.mark.parametrize(
    "year, month",
    [
        (2024, 12),
        (2024, 5)
    ]
)
def test_get_url_web_response_error(requests_mock, year, month):
    with pytest.raises(MadridError):
        requests_mock.get(MADRID_FINES_URL, text=None, status_code=500)
        get_url(year, month)

def test_initialize():
    mf = MadridFines(app_name="test_app", obsolescence=10)

    assert mf.cache_url.app_name == "test_app"
    assert mf.cache_url.obsolescence == 10
    assert mf.data.size == 0
    assert mf.loaded == list()

@pytest.mark.parametrize(
    "app_name,obsolescence",
    [
        (None, 10),
        ("test_app", None)
    ]
)
def test_initialize_errors(app_name, obsolescence):
    with pytest.raises(MadridError):
        MadridFines(app_name, obsolescence)

@pytest.mark.parametrize(
    "year, month, place, time, rows, columns, initially_empty, expected_leaded",
    [
        (2024, 12, "CL CLARA DEL REY 36", 20.23, 29, 15, True, [(2024, 12)]),
        (2024, 5, "CL BRAVO MURILLO 16", 16.50, 34, 15, False, [(2024, 12), (2024, 5)]),
    ]
)
def test_add_by_months(requests_mock, year, month, place, time, rows, columns, initially_empty, expected_leaded):
    mf = MadridFines(app_name="test_app", obsolescence=10)
    assert mf.data.shape == (0, 0)
    assert len(mf.loaded) == 0

    initialize_get_url_mocks(requests_mock)

    if not initially_empty:
        mf.add(2024, 12)

    mf.add(year, month)

    assert mf.data.shape == (rows, columns)
    assert mf.loaded == expected_leaded
    assert set(mf.data.keys()) == {
        'CALIFICACION', 'LUGAR', 'MES', 'ANIO', 'HORA', 'IMP_BOL', 'DESCUENTO',
        'PUNTOS', 'DENUNCIANTE', 'HECHO_BOL', 'VEL_LIMITE', 'VEL_CIRCULA',
        'COORDENADA_X', 'COORDENADA_Y', 'FECHA'
    }
    if initially_empty:
        assert mf.data["LUGAR"].iloc[0] == place
        assert mf.data["HORA"].iloc[0] == time
    else:
        assert mf.data["LUGAR"].iloc[-1] == place
        assert mf.data["HORA"].iloc[-1] == time


@pytest.mark.parametrize(
    "year, place, time, rows, columns, expected_leaded",
    [
        (2024, "CL CLARA DEL REY 36", 20.23, 34, 15, [(2024, 5), (2024, 12)]),
    ]
)
def test_add_by_year(requests_mock, year, place, time, rows, columns, expected_leaded):
    mf = MadridFines(app_name="test_app", obsolescence=10)
    assert mf.data.shape == (0, 0)
    assert len(mf.loaded) == 0

    initialize_get_url_mocks(requests_mock)
    mf.add(year, None)

    assert mf.data.shape == (rows, columns)
    assert mf.loaded == expected_leaded

def test_fines_hour(requests_mock):
    mf = MadridFines(app_name="test_app", obsolescence=10)
    initialize_get_url_mocks(requests_mock)

    mf.add(2024, 12)
    mf.fines_hour("fig_name")

    # we will test that the file has been created
    created_file = Path(__file__).parent.parent.joinpath("fig_name.png")
    assert created_file.exists()
    # delete the test file after test passed
    created_file.unlink()

def test_fines_qualification(requests_mock):
    mf = MadridFines(app_name="test_app", obsolescence=10)
    initialize_get_url_mocks(requests_mock)
    mf.add(2024, 12)

    fines_qualification = mf.fines_qualification()

    assert fines_qualification.shape == (1,2)
    assert set(fines_qualification.keys()) == { 'GRAVE', 'LEVE' }
    assert fines_qualification.loc[(12, 2024), "LEVE"] == 26
    assert fines_qualification.loc[(12, 2024), "GRAVE"] == 3

def test_total_payments(requests_mock):
    mf = MadridFines(app_name="test_app", obsolescence=10)
    initialize_get_url_mocks(requests_mock)

    mf.add(2024, 12)
    df_payments = mf.total_payment()

    assert df_payments.loc[(12, 2024), "MAX_IMPORT"] == 4320.0
    assert df_payments.loc[(12, 2024), "MIN_IMPORT"] == 3160.0

def test_clear_cache():
    mf = MadridFines('test_app', obsolescence=10)

    # simulate we already have files cached
    file_path1 = mf.cache_url.cache_dir / "file1"
    file_path2 = mf.cache_url.cache_dir / "file2"
    file_path1.touch()
    file_path2.touch()

    assert file_path1.exists() == True
    assert file_path2.exists() == True

    mf.clear_cache()

    assert file_path1.exists() == False
    assert file_path2.exists() == False


def test_str(requests_mock):
    mf = MadridFines('test_app', obsolescence=10)
    assert str(mf) ==  (
        'Loaded months: [] \n'
        'Data has the next columns: RangeIndex(start=0, stop=0, step=1) \n'
        'Data has a shape of: (0, 0) \n'
        'Below you can see a sneak peak of the loaded data: \n'
        'Empty DataFrame\nColumns: []\nIndex: [] \n'
    )

def initialize_get_url_mocks(requests_mock) -> None:
    """
    Function that helps us mock a dataframe with correct madrid fines data
    when the class tries to get the data through a real http request

    :param requests_mock:
    :return:
    """
    # Mock Madrid Fines url
    url_html = (FIXTURES_DIR / "madrid_multas.html").read_text()
    requests_mock.get(MADRID_FINES_URL, text=url_html, status_code=200)

    # Mock year month csv file url fpr 12/2024
    month_year_csv = "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-15-multas-circulacion-detalle-csv/download/210104-15-multas-circulacion-detalle-csv.csv"
    csv_file = FIXTURES_DIR / "210104-15-multas-circulacion-detalle-csv.csv"
    requests_mock.get(month_year_csv, text=csv_file.read_text(encoding="latin1"), status_code=200)

    # Mock year month csv file url fpr 5/2024
    month_year_csv = "https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/resource/210104-339-multas-circulacion-detalle-csv/download/210104-339-multas-circulacion-detalle-csv.csv"
    csv_file = FIXTURES_DIR / "210104-339-multas-circulacion-detalle-csv.csv"
    requests_mock.get(month_year_csv, text=csv_file.read_text(encoding="latin1"), status_code=200)