"""
Markdown to PDF converter with GitHub styling.

Converts Markdown files to PDF preserving GitHub-flavored styling,
including support for GitHub-specific alerts (NOTE, TIP, IMPORTANT, WARNING, CAUTION).
Optionally supports IEE (TU Graz) institutional branding with header/footer.
Configuration via themes.ini file.
"""

import argparse
import base64
import configparser
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

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


class ThemeConfig:
    """Configuration class for theme settings loaded from themes.ini."""

    def __init__(self, theme_name: str = "Standard", config_path: Optional[str] = None):
        self.theme_name = theme_name
        self.config = configparser.ConfigParser()

        # Default values
        self.name = "Institute of Electricity Economics and Energy Innovation"
        self.university = "Graz University of Technology"
        self.address = "Inffeldgasse 18, 8010 Graz, Austria"
        self.email = "iee@tugraz.at"
        self.website = "www.iee.tugraz.at"
        self.slogan = "SCIENCE · PASSION · TECHNOLOGY"
        self.accent_color = "#000000"
        self.heading_line_color = "#d1d9e0"
        self.logo_left = "Logo_IEE.png"
        self.logo_right = "Logo_TuGraz.png"

        # Try to load config
        if config_path is None:
            config_path = Path(__file__).parent / "themes.ini"

        if Path(config_path).exists():
            self.config.read(config_path)
            self._load_theme(theme_name)

    def _load_theme(self, theme_name: str) -> None:
        """Load theme settings from config file."""
        if theme_name in self.config:
            section = self.config[theme_name]
            self.name = section.get("name", self.name)
            self.university = section.get("university", self.university)
            self.address = section.get("address", self.address)
            self.email = section.get("email", self.email)
            self.website = section.get("website", self.website)
            self.slogan = section.get("slogan", self.slogan)
            self.accent_color = section.get("accent_color", self.accent_color)
            self.logo_left = section.get("logo_left", self.logo_left)
            self.logo_right = section.get("logo_right", self.logo_right)

        if "DEFAULT" in self.config:
            self.heading_line_color = self.config["DEFAULT"].get(
                "heading_line_color", self.heading_line_color
            )


def install_dependencies() -> None:
    """Checks for required packages and installs them if missing."""
    print("Checking system dependencies...")
    for package in ["markdown", "playwright"]:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing missing package: {package}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package]
            )

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch()
    except Exception:
        print("Installing Playwright browsers...")
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install", "chromium"]
        )


def load_image_as_base64(image_path: str, script_dir: Path) -> Optional[str]:
    """
    Load an image file and return as base64 data URI.

    Args:
        image_path: Path to the image file.
        script_dir: Directory of the script for locating resources.
    """
    path = Path(image_path)
    if not path.is_absolute():
        path = script_dir / image_path

    if not path.exists():
        print(f"Warning: Image not found: {path}")
        return None

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    ext = path.suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    mime = mime_types.get(ext, "image/png")
    return f"data:{mime};base64,{data}"


def get_github_css(heading_line_color: str = "#d1d9e0") -> str:
    """
    Returns CSS for GitHub-style rendering.

    Args:
        heading_line_color: Color for heading underline.
    """
    return f"""
        * {{ box-sizing: border-box; }}
        html, body {{ margin: 0; padding: 0; background: #fff; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.5;
            color: #1f2328;
            padding: 20px 45px;
            max-width: 900px;
        }}

        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            color: #1f2328;
        }}
        h1:first-child, h2:first-child, h3:first-child {{ margin-top: 0; }}
        h1 {{ font-size: 2em; border-bottom: 1px solid {heading_line_color}; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid {heading_line_color}; padding-bottom: 0.3em; }}
        h3 {{ font-size: 1.25em; }}
        h4 {{ font-size: 1em; }}

        p {{ margin-top: 0; margin-bottom: 16px; }}
        a {{ color: #0969da; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        a code {{ color: #0969da; }}
        strong {{ font-weight: 600; }}

        code, tt {{
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 85%;
            padding: 0.2em 0.4em;
            background-color: #eff1f3;
            border-radius: 6px;
        }}
        pre {{
            font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
            font-size: 85%;
            padding: 16px;
            overflow: auto;
            line-height: 1.45;
            background-color: #f6f8fa;
            border-radius: 6px;
            margin-bottom: 16px;
        }}
        pre code {{ padding: 0; background-color: transparent; font-size: 100%; }}

        ul, ol {{ padding-left: 2em; margin-bottom: 16px; }}
        ul {{ list-style-type: disc; }}
        ol {{ list-style-type: decimal; }}
        li {{ margin-top: 0.25em; }}
        ul ul, ol ul {{ list-style-type: circle; margin-top: 0; margin-bottom: 0; }}

        blockquote {{
            padding: 0 1em;
            color: #656d76;
            border-left: 0.25em solid #d0d7de;
            margin: 0 0 16px 0;
        }}

        table {{ border-spacing: 0; border-collapse: collapse; margin-bottom: 16px; }}
        th, td {{ padding: 6px 13px; border: 1px solid #d0d7de; }}
        th {{ font-weight: 600; background-color: #f6f8fa; }}
        tr:nth-child(2n) {{ background-color: #f6f8fa; }}

        hr {{ height: 0.25em; padding: 0; margin: 24px 0; background-color: #d0d7de; border: 0; }}
        img {{ max-width: 100%; }}

        .markdown-alert {{
            padding: 8px 16px;
            margin-bottom: 16px;
            border-left: 4px solid;
            border-radius: 0 6px 6px 0;
        }}
        .markdown-alert > :first-child {{ margin-top: 0; }}
        .markdown-alert > :last-child {{ margin-bottom: 0; }}
        .markdown-alert-title {{
            display: flex;
            align-items: center;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .markdown-alert-title .octicon {{ margin-right: 8px; }}

        .markdown-alert-note {{ border-color: #0969da; background-color: #ddf4ff; }}
        .markdown-alert-note .markdown-alert-title {{ color: #0969da; }}
        .markdown-alert-note .octicon {{ fill: #0969da; }}

        .markdown-alert-tip {{ border-color: #1a7f37; background-color: #dafbe1; }}
        .markdown-alert-tip .markdown-alert-title {{ color: #1a7f37; }}
        .markdown-alert-tip .octicon {{ fill: #1a7f37; }}

        .markdown-alert-important {{ border-color: #8250df; background-color: #fbefff; }}
        .markdown-alert-important .markdown-alert-title {{ color: #8250df; }}
        .markdown-alert-important .octicon {{ fill: #8250df; }}

        .markdown-alert-warning {{ border-color: #9a6700; background-color: #fff8c5; }}
        .markdown-alert-warning .markdown-alert-title {{ color: #9a6700; }}
        .markdown-alert-warning .octicon {{ fill: #9a6700; }}

        .markdown-alert-caution {{ border-color: #cf222e; background-color: #ffebe9; }}
        .markdown-alert-caution .markdown-alert-title {{ color: #cf222e; }}
        .markdown-alert-caution .octicon {{ fill: #cf222e; }}
    """


def get_iee_css(theme: ThemeConfig) -> str:
    """
    Returns CSS for IEE header/footer styling matching reference images.

    Args:
        theme: Theme configuration.
    """
    return f"""
        body {{ padding-top: 12px; }}

        .iee-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 8px;
            margin-bottom: 15px;
            border-bottom: 1px solid {theme.accent_color};
        }}
        .iee-header-left {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .iee-header-left img {{
            height: 28px;
            width: auto;
        }}
        .iee-header-title {{
            font-size: 10px;
            line-height: 1.3;
        }}
        .iee-header-title .inst-name {{
            color: {theme.accent_color};
            font-weight: 600;
            font-size: 11px;
        }}
        .iee-header-title .univ-name {{
            color: #666;
        }}
        .iee-header-right img {{
            height: 26px;
            width: auto;
        }}

        .iee-footer {{
            margin-top: 25px;
            padding-top: 8px;
            border-top: 1px solid {theme.accent_color};
            font-size: 9px;
            color: #666;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .iee-footer-left {{
            line-height: 1.5;
        }}
        .iee-footer-left .univ {{
            color: {theme.accent_color};
            font-weight: 600;
        }}
        .iee-footer-left .inst {{
            color: {theme.accent_color};
        }}
        .iee-footer-right {{
            text-align: right;
            color: {theme.accent_color};
            font-style: italic;
            font-size: 8px;
        }}
    """


def get_iee_header(
        theme: ThemeConfig, logo_left_data: str, logo_right_data: str
) -> str:
    """
    Returns HTML for IEE header matching reference image.

    Args:
        theme: Theme configuration.
        logo_left_data: Base64 data URI for left logo.
        logo_right_data: Base64 data URI for right logo.
    """
    return f"""
<div class="iee-header">
    <div class="iee-header-left">
        <img src="{logo_left_data}" alt="IEE">
        <div class="iee-header-title">
            <div class="inst-name">{theme.name}</div>
            <div class="univ-name">{theme.university}</div>
        </div>
    </div>
    <div class="iee-header-right">
        <img src="{logo_right_data}" alt="TU Graz">
    </div>
</div>
"""


def get_iee_footer(theme: ThemeConfig) -> str:
    """
    Returns HTML for IEE footer matching reference image.

    Args:
        theme: Theme configuration.
    """
    return f"""
<div class="iee-footer">
    <div class="iee-footer-left">
        <div class="univ">{theme.university}</div>
        <div class="inst">{theme.name}</div>
        <div>{theme.address}</div>
        <div>{theme.email} | {theme.website}</div>
    </div>
    <div class="iee-footer-right">{theme.slogan}</div>
</div>
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
    pattern = re.compile(
        r"^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*\n((?:>.*(?:\n|$))*)",
        re.MULTILINE | re.IGNORECASE,
    )

    def replace_alert(match: re.Match) -> str:
        alert_type = match.group(1).lower()
        content_block = match.group(2)
        clean_lines = [
            re.sub(r"^>\s?", "", line) for line in content_block.split("\n")
        ]
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

    return pattern.sub(replace_alert, markdown_content)


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


def create_html_document(
        body: str,
        theme: Optional[ThemeConfig] = None,
        iee_style: bool = False,
        script_dir: Optional[Path] = None,
) -> str:
    """
    Creates complete HTML document with optional IEE styling.

    Args:
        body: HTML body content.
        theme: Theme configuration for IEE styling.
        iee_style: Whether to apply IEE styling.
        script_dir: Directory of the script for locating resources.
    """
    heading_color = theme.heading_line_color if theme else "#d1d9e0"
    css = get_github_css(heading_color)
    header, footer = "", ""

    if iee_style and theme and script_dir:
        css += get_iee_css(theme)
        logo_left = load_image_as_base64(theme.logo_left, script_dir)
        logo_right = load_image_as_base64(theme.logo_right, script_dir)
        if logo_left and logo_right:
            header = get_iee_header(theme, logo_left, logo_right)
            footer = get_iee_footer(theme)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Document</title>
    <style>{css}</style>
</head>
<body>
{header}
{body}
{footer}
</body>
</html>"""


def convert_and_style(
        input_file: str,
        temp_html: str,
        iee_style: bool = False,
        theme: Optional[ThemeConfig] = None,
        script_dir: Optional[Path] = None,
) -> None:
    """
    Converts Markdown to styled HTML.

    Args:
        input_file: Path to input Markdown file.
        temp_html: Path for output temporary HTML file.
        iee_style: Whether to apply IEE styling.
        theme: Theme configuration for IEE styling.
        script_dir: Directory of the script for locating resources.
    """
    print(f"Converting '{input_file}' to HTML...")

    # Read the Markdown file
    with open(input_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    processed = preprocess_github_alerts(md_content)
    html_body = convert_markdown_to_html(processed)
    html_doc = create_html_document(html_body, theme, iee_style, script_dir)

    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(html_doc)


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
        file_url = (
            f"file:///{file_path.replace(os.sep, '/')}"
            if os.name == "nt"
            else f"file://{file_path}"
        )
        page.goto(file_url)

        # Wait for fonts and styles to render
        page.wait_for_timeout(1500)

        page.pdf(
            path=pdf_file,
            format="A4",
            print_background=True,
            display_header_footer=False,
            margin={
                "top": "15mm",
                "bottom": "15mm",
                "left": "15mm",
                "right": "15mm",
            },
        )
        browser.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Markdown to PDF with GitHub styling."
    )
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("output", nargs="?", help="Output PDF file (optional)")
    parser.add_argument(
        "--iee", action="store_true", help="Add IEE/TU Graz header and footer"
    )
    parser.add_argument(
        "--theme", default="Standard", help="Theme name from themes.ini"
    )
    parser.add_argument("--config", default="themes.ini", help="Path to themes.ini config file")
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output or f"{os.path.splitext(input_path)[0]}.pdf"
    script_dir = Path(__file__).parent

    if not os.path.exists(input_path):
        print(f"Error: '{input_path}' not found.")
        sys.exit(1)

    install_dependencies()

    theme = ThemeConfig(args.theme, args.config) if args.iee else None
    temp_html = f"temp_{os.path.basename(input_path)}.html"

    try:
        convert_and_style(input_path, temp_html, args.iee, theme, script_dir)
        print_to_pdf(temp_html, output_path)
        print(f"✅ PDF created: {output_path}")
        if args.iee:
            print("   (with IEE styling)")
    finally:
        if os.path.exists(temp_html):
            os.remove(temp_html)


if __name__ == "__main__":
    main()
