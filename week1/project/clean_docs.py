
import re
from pathlib import Path
from bs4 import BeautifulSoup

RAW_DIR = Path("raw_docs")
CLEAN_DIR = Path("clean_docs_v2")

CLEAN_DIR.mkdir(exist_ok=True)

html_files = list(RAW_DIR.glob("*.html"))


# ==========================================================
# Helpers
# ==========================================================

def clean_text(text: str) -> str:
    """
    Normalize whitespace and remove common encoding artifacts.
    """

    if not text:
        return ""

    text = (
        text.replace("Â¶", "")
        .replace("¶", "")
        .replace("\xa0", " ")
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def format_code_block(element):
    """
    Preserve code blocks.
    """

    code = element.get_text(strip=False)

    if not code.strip():
        return ""

    return f"\n```python\n{code.strip()}\n```\n"


# ==========================================================
# Extract Sphinx Definition Blocks
# ==========================================================

def extract_definition_block(dl):
    """
    Converts:

    <dl class="py function">
        <dt>json.dumps(obj)</dt>
        <dd>Serialize object...</dd>
    </dl>

    into structured text.
    """

    classes = dl.get("class", [])

    object_type = "OBJECT"

    if "function" in classes:
        object_type = "FUNCTION"

    elif "method" in classes:
        object_type = "METHOD"

    elif "class" in classes:
        object_type = "CLASS"

    elif "attribute" in classes:
        object_type = "ATTRIBUTE"

    elif "exception" in classes:
        object_type = "EXCEPTION"

    dt = dl.find("dt")

    dd = dl.find("dd")

    if not dt or not dd:
        return ""

    signature = clean_text(
        dt.get_text(" ", strip=True)
    )

    description_parts = []

    for child in dd.find_all(
        ["p", "pre", "ul", "ol"],
        recursive=True
    ):

        if child.name == "pre":
            description_parts.append(
                format_code_block(child)
            )

        elif child.name in ["ul", "ol"]:

            for li in child.find_all("li"):
                item = clean_text(
                    li.get_text(" ", strip=True)
                )

                if item:
                    description_parts.append(
                        f"- {item}"
                    )

        else:

            text = clean_text(
                child.get_text(" ", strip=True)
            )

            if text:
                description_parts.append(text)

    description = "\n".join(
        description_parts
    )

    block = f"""
{object_type}: {signature}

DESCRIPTION:
{description}
"""

    return block.strip()


# ==========================================================
# Extract Standard Content
# ==========================================================

def extract_standard_content(main_content):

    blocks = []

    for element in main_content.find_all(
        ["h1", "h2", "h3", "h4", "p", "pre"],
        recursive=True
    ):

        if element.find_parent("dl"):
            continue

        tag = element.name

        if tag.startswith("h"):

            level = int(tag[1])

            text = clean_text(
                element.get_text(" ", strip=True)
            )

            if text:
                blocks.append(
                    f"\n{'#' * level} {text}\n"
                )

        elif tag == "pre":

            blocks.append(
                format_code_block(element)
            )

        else:

            text = clean_text(
                element.get_text(" ", strip=True)
            )

            if text:
                blocks.append(text)

    return blocks


# ==========================================================
# Main Processing Loop
# ==========================================================

for file_path in html_files:

    print(
        f"\nProcessing: {file_path.name}"
    )

    html = file_path.read_text(
        encoding="utf-8",
        errors="replace"
    )

    soup = BeautifulSoup(
        html,
        "lxml"
    )

    main_content = (
        soup.find("div", role="main")
        or soup.find("div", class_="body")
        or soup.find("main")
        or soup.find("article")
        or soup.find("body")
    )

    if not main_content:

        print(
            f"Skipping {file_path.name}"
        )

        continue

    for noise in main_content.find_all(
        [
            "nav",
            "footer",
            "header",
            "script",
            "style",
            "form"
        ]
    ):
        noise.decompose()

    final_blocks = []

    # ------------------------------------
    # Standard Content
    # ------------------------------------

    final_blocks.extend(
        extract_standard_content(
            main_content
        )
    )

    # ------------------------------------
    # Definition Blocks
    # ------------------------------------

    definition_blocks = main_content.find_all(
        "dl"
    )

    for dl in definition_blocks:

        extracted = extract_definition_block(
            dl
        )

        if extracted:
            final_blocks.append(
                extracted
            )

    final_text = "\n\n".join(
        block.strip()
        for block in final_blocks
        if block.strip()
    )

    final_text = re.sub(
        r"\n{3,}",
        "\n\n",
        final_text
    )

    output_file = (
        CLEAN_DIR /
        f"{file_path.stem}.txt"
    )

    output_file.write_text(
        final_text,
        encoding="utf-8"
    )

    print(
        f"Saved: {output_file.name}"
    )

print("\nDone.")

