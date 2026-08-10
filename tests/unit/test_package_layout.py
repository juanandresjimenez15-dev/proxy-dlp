import pytest


@pytest.mark.unit
def test_el_paquete_app_se_puede_importar():
    import app  # noqa: F401
