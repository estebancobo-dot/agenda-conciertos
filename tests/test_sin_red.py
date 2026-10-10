"""La protección de tests/conftest.py: una prueba que intente salir a internet falla en el acto."""
import pytest
import requests

from tests.conftest import RedEnPruebas


def test_las_pruebas_no_salen_a_internet():
    with pytest.raises((RedEnPruebas, requests.exceptions.ConnectionError)):
        requests.get("https://example.com/", timeout=2)
