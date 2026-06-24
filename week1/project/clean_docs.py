import re
from pathlib import Path
from bs4 import BeautifulSoup

RAW_DIR = Path("raw_docs")
CLEAN_DIR = Path("clean_docs")
CLEAN_DIR.mkdir(exist_ok=True)

html_files = list(RAW_DIR.glob("*.html"))

def clean_sphinx_element(element):
    """
    Processes structural HTML elements individually to clean up artifacts 
    and maintain formatting (markdown-style layout).
    """
    tag_name = element.name
    
    # 1. Handle Code Blocks cleanly (Preserve internal formatting & whitespace)
    if tag_name == "pre":
        code_text = element.get_text(strip=False)
        # Avoid empty blocks
        if not code_text.strip():
            return ""
        return f"```python\n{code_text.strip()}\n```"
    
    # Get text and purge bad character sets/pilcrows
    text = element.get_text(strip=True)
    text = text.replace("Â¶", "").replace("¶", "")
    # Clean up multiple consecutive internal spaces
    text = re.sub(r' +', ' ', text)
    
    if not text:
        return ""
    
    # 2. Convert Headers into Markdown equivalents to give chunk splitters structural hints
    if tag_name in ["h1", "h2", "h3", "h4"]:
        level = int(tag_name[1])
        return f"\n{'#' * level} {text}"
    
    # 3. Format Bullet Lists gracefully
    if tag_name == "li":
        return f"* {text}"
    
    return text

for file_path in html_files:
    print(f"Analyzing and cleaning: {file_path.name}")
    html = file_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    # Target standard Sphinx documentation containers exclusively
    main_content = (
        soup.find("div", role="main")
        or soup.find("div", class_="body")
        or soup.find("main")
        or soup.find("article")
    )
    
    if not main_content:
        # Emergency backup if document structure varies
        main_content = soup.find("body")

    if not main_content:
        print(f"⚠️ Warning: Could not locate core content for {file_path.name}")
        continue

    # Unconditionally drop standard web platform layout noise inside the target space
    for noise in main_content.find_all(["nav", "footer", "header", "script", "style", "form"]):
        noise.decompose()

    # Walk through the top-level structural layout blocks (avoids nested duplication)
    structural_blocks = main_content.find_all(["h1", "h2", "h3", "h4", "p", "pre", "ul", "ol"])
    
    clean_text_blocks = []
    
    for block in structural_blocks:
        if block.name in ["ul", "ol"]:
            # Process inner list items sequentially to preserve list groups
            for li in block.find_all("li", recursive=False):
                cleaned_li = clean_sphinx_element(li)
                if cleaned_li:
                    clean_text_blocks.append(cleaned_li)
        else:
            cleaned_block = clean_sphinx_element(block)
            if cleaned_block:
                clean_text_blocks.append(cleaned_block)

    # Join with clean paragraph double spacing
    final_text = "\n\n".join(clean_text_blocks)
    
    # Safeguard: Remove any accidental over-stacking of newline sequences
    final_text = re.sub(r'\n{3,}', '\n\n', final_text)

    # Export clean knowledge base document
    output_file = CLEAN_DIR / f"{file_path.stem}.txt"
    output_file.write_text(final_text, encoding="utf-8")

    print(f"✅ Processed and Saved: {output_file.name} ({len(final_text)} characters)\n")