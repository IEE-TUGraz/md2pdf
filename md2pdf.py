"""
Markdown to PDF converter with GitHub styling.

Converts Markdown files to PDF preserving GitHub-flavored styling,
including support for GitHub-specific alerts (NOTE, TIP, IMPORTANT, WARNING, CAUTION).
"""

import argparse
import os
import re
import subprocess
import sys

# SVG icons for GitHub alerts
ALERT_ICONS: dict[str, str] = {
    "note": '<svg class="octicon" viewBox="0 0 16 16" width="16" height="16"><path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM6.5 7.75A.75.75 0 0 1 7.25 7h1a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-2a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75ZM8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"></path></svg>',
    "tip": '<svg class="octicon" viewBox="0 0 16 16" width="16" height="16"><path d="M8 1.5c-2.363 0-4 1.69-4 3.75 0 .984.424 1.625.984 2.304l.214.253c.223.264.47.556.673.848.284.411.537.896.621 1.49a.75.75 0 0 1-1.484.211c-.04-.282-.163-.547-.37-.847a8.456 8.456 0 0 0-.542-.68c-.084-.1-.173-.205-.268-.32C3.201 7.75 2.5 6.766 2.5 5.25 2.5 2.31 4.863 0 8 0s5.5 2.31 5.5 5.25c0 1.516-.701 2.5-1.328 3.259-.095.115-.184.22-.268.319-.207.245-.383.453-.541.681-.208.3-.33.565-.37.847a.751.751 0 0 1-1.485-.212c.084-.593.337-1.078.621-1.489.203-.292.45-.584.673-.848.075-.088.147-.173.213-.253.561-.679.985-1.32.985-2.304 0-2.06-1.637-3.75-4-3.75ZM5.75 12h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1 0-1.5ZM6 15.25a.75.75 0 0 1 .75-.75h2.5a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1-.75-.75Z"></path></svg>',
    "important": '<svg class="octicon" viewBox="0 0 16 16" width="16" height="16"><path d="M0 1.75C0 .784.784 0 1.75 0h12.5C15.216 0 16 .784 16 1.75v9.5A1.75 1.75 0 0 1 14.25 13H8.06l-2.573 2.573A1.458 1.458 0 0 1 3 14.543V13H1.75A1.75 1.75 0 0 1 0 11.25Zm1.75-.25a.25.25 0 0 0-.25.25v9.5c0 .138.112.25.25.25h2a.75.75 0 0 1 .75.75v2.19l2.72-2.72a.749.749 0 0 1 .53-.22h6.5a.25.25 0 0 0 .25-.25v-9.5a.25.25 0 0 0-.25-.25Zm7 2.25v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 9a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"></path></svg>',
    "warning": '<svg class="octicon" viewBox="0 0 16 16" width="16" height="16"><path d="M6.457 1.047c.659-1.234 2.427-1.234 3.086 0l6.082 11.378A1.75 1.75 0 0 1 14.082 15H1.918a1.75 1.75 0 0 1-1.543-2.575Zm1.763.707a.25.25 0 0 0-.44 0L1.698 13.132a.25.25 0 0 0 .22.368h12.164a.25.25 0 0 0 .22-.368Zm.53 3.996v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"></path></svg>',
    "caution": '<svg class="octicon" viewBox="0 0 16 16" width="16" height="16"><path d="M4.47.22A.749.749 0 0 1 5 0h6c.199 0 .389.079.53.22l4.25 4.25c.141.14.22.331.22.53v6a.749.749 0 0 1-.22.53l-4.25 4.25A.749.749 0 0 1 11 16H5a.749.749 0 0 1-.53-.22L.22 11.53A.749.749 0 0 1 0 11V5c0-.199.079-.389.22-.53Zm.84 1.28L1.5 5.31v5.38l3.81 3.81h5.38l3.81-3.81V5.31L10.69 1.5ZM8 4a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 4Zm0 8a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"></path></svg>',
}

ALERT_TITLES: dict[str, str] = {
    "note": "Note",
    "tip": "Tip",
    "important": "Important",
    "warning": "Warning",
    "caution": "Caution",
}


def install_dependencies() -> None:
    """Checks for required packages and installs them if missing."""
    print("Checking system dependencies...")
    packages = ["markdown", "playwright"]

    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing missing package: {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch()
    except Exception:
        print("Installing Playwright browsers...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])


def get_github_css() -> str:
    """Returns comprehensive CSS for GitHub-style rendering."""
    return """
        /* === BASE STYLES === */
        * {
            box-sizing: border-box;
        }

        html, body {
            margin: 0;
            padding: 0;
            background: #ffffff;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
            font-size: 16px;
            line-height: 1.5;
            color: #1f2328;
            padding: 45px;
            max-width: 900px;
        }

        /* === TYPOGRAPHY === */
        h1, h2, h3, h4, h5, h6 {
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            color: #1f2328;
        }

        h1:first-child, h2:first-child, h3:first-child {
            margin-top: 0;
        }

        h1 {
            font-size: 2em;
            border-bottom: 1px solid #d1d9e0;
            padding-bottom: 0.3em;
        }

        h2 {
            font-size: 1.5em;
            border-bottom: 1px solid #d1d9e0;
            padding-bottom: 0.3em;
        }

        h3 { font-size: 1.25em; }
        h4 { font-size: 1em; }
        h5 { font-size: 0.875em; }
        h6 { font-size: 0.85em; color: #656d76; }

        p {
            margin-top: 0;
            margin-bottom: 16px;
        }

        a {
            color: #0969da;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }
        
        a code, a tt {
            color: #0969da;
        }
        
        strong, b {
            font-weight: 600;
        }

        em, i {
            font-style: italic;
        }

        /* === CODE BLOCKS === */
        code, tt {
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
            font-size: 85%;
            padding: 0.2em 0.4em;
            margin: 0;
            background-color: #eff1f3;
            border-radius: 6px;
            color: #1f2328;
        }

        pre {
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
            font-size: 85%;
            padding: 16px;
            overflow: auto;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 6px;
            margin-top: 0;
            margin-bottom: 16px;
        }

        pre code, pre tt {
            display: inline;
            padding: 0;
            margin: 0;
            background-color: transparent;
            border: 0;
            font-size: 100%;
            line-height: inherit;
            word-wrap: normal;
        }

        /* === LISTS === */
        ul, ol {
            padding-left: 2em;
            margin-top: 0;
            margin-bottom: 16px;
        }

        ul {
            list-style-type: disc;
        }

        ol {
            list-style-type: decimal;
        }

        li {
            margin-top: 0.25em;
        }

        li + li {
            margin-top: 0.25em;
        }

        /* Nested lists */
        ul ul, ol ul {
            list-style-type: circle;
            margin-top: 0;
            margin-bottom: 0;
        }

        ul ol, ol ol {
            margin-top: 0;
            margin-bottom: 0;
        }

        li > p {
            margin-top: 16px;
        }

        li > p:first-child {
            margin-top: 0;
        }

        /* === BLOCKQUOTES === */
        blockquote {
            padding: 0 1em;
            color: #656d76;
            border-left: 0.25em solid #d0d7de;
            margin: 0 0 16px 0;
            background: transparent;
        }

        blockquote > :first-child {
            margin-top: 0;
        }

        blockquote > :last-child {
            margin-bottom: 0;
        }

        /* === TABLES === */
        table {
            border-spacing: 0;
            border-collapse: collapse;
            margin-top: 0;
            margin-bottom: 16px;
            display: block;
            width: max-content;
            max-width: 100%;
            overflow: auto;
        }

        th, td {
            padding: 6px 13px;
            border: 1px solid #d0d7de;
        }

        th {
            font-weight: 600;
            background-color: #f6f8fa;
        }

        tr {
            background-color: #ffffff;
        }

        tr:nth-child(2n) {
            background-color: #f6f8fa;
        }

        /* === HORIZONTAL RULE === */
        hr {
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: #d0d7de;
            border: 0;
        }

        /* === IMAGES === */
        img {
            max-width: 100%;
            box-sizing: content-box;
        }

        /* === GITHUB ALERTS === */
        .markdown-alert {
            padding: 8px 16px;
            margin-bottom: 16px;
            border-left-width: 4px;
            border-left-style: solid;
            border-radius: 0 6px 6px 0;
            display: block;
        }

        .markdown-alert > :first-child {
            margin-top: 0;
        }

        .markdown-alert > :last-child {
            margin-bottom: 0;
        }

        .markdown-alert p {
            margin-bottom: 8px;
        }

        .markdown-alert p:last-child {
            margin-bottom: 0;
        }

        .markdown-alert-title {
            display: flex;
            align-items: center;
            line-height: 1;
            font-weight: 600;
            margin-bottom: 4px;
        }

        .markdown-alert-title .octicon {
            margin-right: 8px;
            flex-shrink: 0;
            display: inline-block;
            vertical-align: text-bottom;
        }

        /* NOTE (Blue) */
        .markdown-alert-note {
            border-left-color: #0969da;
            background-color: #ddf4ff;
        }
        .markdown-alert-note .markdown-alert-title { color: #0969da; }
        .markdown-alert-note .octicon { fill: #0969da; }

        /* TIP (Green) */
        .markdown-alert-tip {
            border-left-color: #1a7f37;
            background-color: #dafbe1;
        }
        .markdown-alert-tip .markdown-alert-title { color: #1a7f37; }
        .markdown-alert-tip .octicon { fill: #1a7f37; }

        /* IMPORTANT (Purple) */
        .markdown-alert-important {
            border-left-color: #8250df;
            background-color: #fbefff;
        }
        .markdown-alert-important .markdown-alert-title { color: #8250df; }
        .markdown-alert-important .octicon { fill: #8250df; }

        /* WARNING (Yellow/Orange) */
        .markdown-alert-warning {
            border-left-color: #9a6700;
            background-color: #fff8c5;
        }
        .markdown-alert-warning .markdown-alert-title { color: #9a6700; }
        .markdown-alert-warning .octicon { fill: #9a6700; }

        /* CAUTION (Red) */
        .markdown-alert-caution {
            border-left-color: #cf222e;
            background-color: #ffebe9;
        }
        .markdown-alert-caution .markdown-alert-title { color: #cf222e; }
        .markdown-alert-caution .octicon { fill: #cf222e; }
    """


def preprocess_github_alerts(markdown_content: str) -> str:
    """
    Converts GitHub-style alerts to HTML placeholders before Markdown processing.

    Handles alerts like:
    > [!NOTE]
    > Content here

    Args:
        markdown_content: Raw Markdown text.

    Returns:
        Markdown with alerts converted to HTML divs.
    """
    alert_pattern = re.compile(
        r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:>.*(?:\n|$))*)",
        re.MULTILINE | re.IGNORECASE
    )

    def replace_alert(match: re.Match) -> str:
        alert_type = match.group(1).lower()
        content_block = match.group(2)

        # Remove the '>' prefix from each line and clean up
        clean_lines = []
        for line in content_block.split("\n"):
            # Remove leading '>' and optional space
            cleaned = re.sub(r"^>\s?", "", line)
            clean_lines.append(cleaned)

        # Join and strip trailing whitespace
        content = "\n".join(clean_lines).strip()

        icon = ALERT_ICONS.get(alert_type, "")
        title = ALERT_TITLES.get(alert_type, alert_type.capitalize())

        # Create HTML block - this will be preserved by the markdown parser
        return f"""
<div class="markdown-alert markdown-alert-{alert_type}">
<p class="markdown-alert-title">{icon}{title}</p>
<p>{content}</p>
</div>

"""

    return alert_pattern.sub(replace_alert, markdown_content)


def convert_markdown_to_html(markdown_content: str) -> str:
    """
    Converts Markdown to HTML using Python's Markdown library.

    Args:
        markdown_content: Preprocessed Markdown text.

    Returns:
        HTML content.
    """
    import markdown

    # Configure Markdown with GitHub-like extensions
    md = markdown.Markdown(
        extensions=[
            "fenced_code",  # ```code blocks```
            "tables",  # GitHub tables
            "toc",  # Table of contents
            "nl2br",  # Newlines to <br>
            "sane_lists",  # Better list handling
        ]
    )

    html_body = md.convert(markdown_content)

    return html_body


def create_html_document(body_content: str) -> str:
    """
    Wraps HTML body content in a complete HTML document with styling.

    Args:
        body_content: HTML body content.

    Returns:
        Complete HTML document.
    """
    css = get_github_css()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
    <style>
{css}
    </style>
</head>
<body>
{body_content}
</body>
</html>
"""


def convert_and_style(input_file: str, temp_html_file: str) -> None:
    """
    Converts Markdown to styled HTML.

    Args:
        input_file: Path to input Markdown file.
        temp_html_file: Path for temporary HTML output.
    """
    print(f"Converting '{input_file}' to HTML...")

    # Read the Markdown file
    with open(input_file, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # Preprocess GitHub alerts
    processed_markdown = preprocess_github_alerts(markdown_content)

    # Convert to HTML
    html_body = convert_markdown_to_html(processed_markdown)

    # Create complete HTML document
    html_document = create_html_document(html_body)

    # Write the HTML file
    with open(temp_html_file, "w", encoding="utf-8") as f:
        f.write(html_document)


def print_to_pdf(html_file: str, pdf_file: str) -> None:
    """
    Converts HTML to PDF using Playwright.

    Args:
        html_file: Path to input HTML file.
        pdf_file: Path for output PDF file.
    """
    from playwright.sync_api import sync_playwright

    print(f"Printing to '{pdf_file}'...")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Use proper file:// URL format
        file_path = os.path.abspath(html_file)
        if os.name == "nt":  # Windows
            file_url = f"file:///{file_path.replace(os.sep, '/')}"
        else:  # Unix-like
            file_url = f"file://{file_path}"

        page.goto(file_url)

        # Wait for fonts and styles to render
        page.wait_for_timeout(1500)

        page.pdf(
            path=pdf_file,
            format="A4",
            print_background=True,
            display_header_footer=False,
            margin={
                "top": "20mm",
                "bottom": "20mm",
                "left": "15mm",
                "right": "15mm"
            }
        )
        browser.close()


def main() -> None:
    """Main entry point for the Markdown to PDF converter."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF with GitHub styling."
    )
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("output", nargs="?", help="Output PDF file (optional)")
    args = parser.parse_args()

    input_path: str = args.input
    output_path: str = args.output if args.output else f"{os.path.splitext(input_path)[0]}.pdf"

    if not os.path.exists(input_path):
        print(f"Error: '{input_path}' not found.")
        sys.exit(1)

    install_dependencies()

    temp_html = f"temp_{os.path.basename(input_path)}.html"

    try:
        convert_and_style(input_path, temp_html)
        print_to_pdf(temp_html, output_path)
        print(f"✅ PDF created: {output_path}")
    finally:
        if os.path.exists(temp_html):
            os.remove(temp_html)


if __name__ == "__main__":
    main()
