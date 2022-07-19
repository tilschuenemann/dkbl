from dkbl.dkbl import create_ledger
import pathlib
import pytest

# empty ledger is supplied
def test_empty_export(tmp_path):
    d = tmp_path / "output"
    d.mkdir()

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        create_ledger(
            "tests/dkb_export_empty.csv",
            d,
            "dkb",
        )
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == "import is empty"

    history = d / "history.csv"
    ledger = d / "ledger.csv"
    maptab = d / "maptab.csv"

    assert pathlib.Path(history).exists() is False
    assert pathlib.Path(ledger).exists() is False
    assert pathlib.Path(maptab).exists() is False


# check for successful ledger creation
def test_success(tmp_path):
    d = tmp_path / "output"
    d.mkdir()

    df = create_ledger(
        "tests/dkb_export_2rows.csv",
        d,
        "dkb",
    )

    history = d / "history.csv"
    ledger = d / "ledger.csv"
    maptab = d / "maptab.csv"

    assert pathlib.Path(history).exists()
    assert pathlib.Path(ledger).exists()
    assert pathlib.Path(maptab).exists()
