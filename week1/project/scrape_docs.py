
from urllib import response

import requests

from pathlib import Path

RAW_DIR = Path("raw_docs")

RAW_DIR.mkdir(
    exist_ok=True
)

DOC_URLS = [

    "https://docs.python.org/3/tutorial/classes.html",

    "https://docs.python.org/3/tutorial/modules.html",

    "https://docs.python.org/3/tutorial/datastructures.html",

    "https://docs.python.org/3/tutorial/inputoutput.html",

    "https://docs.python.org/3/library/pathlib.html",

    "https://docs.python.org/3/library/json.html",

    "https://docs.python.org/3/library/os.html",

    "https://docs.python.org/3/library/datetime.html",

    "https://docs.python.org/3/library/functions.html",

    "https://docs.python.org/3/library/stdtypes.html"
]


def download_page(url):

    try:

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        html = response.content.decode(
            "utf-8",
            errors="replace"
        )

        return html

    except Exception as error:

        print(f"\nFailed: {url}")
        print(error)

        return None


for url in DOC_URLS:

    filename = url.split("/")[-1]

    filepath = (
        RAW_DIR / filename
    )

    if filepath.exists():

        print(
            f"Skipping {filename}"
        )

        continue

    print(
        f"Downloading {filename}"
    )

    html = download_page(url)

    if html is None:
        continue

    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(html)

    print(
        f"Saved {filename}"
    )