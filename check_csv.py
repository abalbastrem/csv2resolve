import csv
import os
import sys

CSV_FILE = "../timeline.csv"

REQUIRED_COLUMNS = [
    "GID",
    "LID",
    "ID VIDEO",
    "CHECK",
    "PRIORITY",
    "TOPIC",
    "TAGS",
    "SPEAKER",
    "SRC IN",
    "SRC OUT",
    "DUR",
    "TL IN",
    "TL OUT",
    "DURACC",
    "C",
    "QUOTE",
    "LACKS SOURCE?",
    "SOURCES",
    "COMMENTS",
    "fSRC_IN",
    "fSRC_OUT",
    "fDUR",
    "fTL_IN",
    "fTL_OUT",
]


def validate_csv_columns(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)

        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError("CSV is empty.")

    missing_columns = []

    for col in REQUIRED_COLUMNS:
        if col not in headers:
            missing_columns.append(col)

    if missing_columns:
        error_msg = (
            "CSV is missing the following required columns:\n"
            + "\n".join(f" - {col}" for col in missing_columns)
        )
        raise ValueError(error_msg)

    print("CSV file has all meaningful columns")
    return True

def validate_chk_error(csv_path):
    """
    Validates that all CHK_ERROR values are 'OK'.
    Lists all rows where the value is different.
    """

    invalid_rows = []

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        if "CHK_ERROR" not in reader.fieldnames:
            raise ValueError("CSV is missing required column: CHK_ERROR")

        for row_number, row in enumerate(reader, start=2):
            check = row["CHECK"].strip()
            value = row["CHK_ERROR"].strip()

            if check != 1:
                continue
            if value != "OK":
                invalid_rows.append(
                    f"Row {row_number}: CHK_ERROR='{value}'"
                )

    if invalid_rows:
        error_msg = (
            "Invalid CHK_ERROR values found:\n"
            + "\n".join(invalid_rows)
        )
        raise ValueError(error_msg)

    print("CSV has no value errors")
    return True


if not os.path.isfile(CSV_FILE):
    print(f"PANIC: CSV FILE NOT FOUND: {CSV_FILE}")
    sys.exit(1)

validate_csv_columns(CSV_FILE)
validate_chk_error(CSV_FILE)
print("SUCCESS")