from .DataBlock import DataBlock
from pathlib import Path

if __name__ == "__main__":
    for testfile in (
        "mocopi_raw-01.bin",
        "mocopi_raw-02.bin",
    ):
        rawData = None
        with open(Path(__file__).parent / testfile, "rb") as f:
            rawData = f.read()

        data = DataBlock(size=len(rawData), type="RAW", data=rawData)
        data._parseData()
        data._dumpData()
