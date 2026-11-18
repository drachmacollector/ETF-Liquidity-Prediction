"""P05: both bhavcopy schemas parse to identical canonical columns; two-digit-year legacy dates."""

import io
import zipfile
from pathlib import Path

from esw.ingest.parsers import BHAV_COLUMNS, parse_nse_bhavcopy

FX = Path(__file__).resolve().parents[1] / "fixtures"


def test_schema_boundary_identical_columns():
    legacy = parse_nse_bhavcopy((FX / "in_bhav_legacy" / "cm19MAR2020bhav_trimmed.csv.zip").read_bytes())
    udiff = parse_nse_bhavcopy(
        (FX / "in_bhav_udiff" / "BhavCopy_NSE_CM_20251009_trimmed.csv.zip").read_bytes()
    )
    assert list(legacy.columns) == list(udiff.columns) == BHAV_COLUMNS
    assert set(legacy["source_schema"]) == {"legacy"} and set(udiff["source_schema"]) == {"udiff"}


def test_two_digit_year_and_missing_isin():
    csv = b"SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,\nGOLDBEES,EQ,1,1,1,1,1,1,10,10,13-Jul-20,\n"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x.csv", csv)
    df = parse_nse_bhavcopy(buf.getvalue())
    assert str(df["date"].iloc[0].date()) == "2020-07-13" and df["isin"].isna().all()
