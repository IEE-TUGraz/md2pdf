# md2pdf

Convert Markdown files to PDF with GitHub-flavored styling, including support for GitHub-specific alerts.

## Features

- **GitHub styling** - Renders PDFs with authentic GitHub Markdown appearance
- **Alert support** - Full support for [GitHub alerts](https://github.com/orgs/community/discussions/16925) (`NOTE`,
  `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`)
- **Code blocks** - Syntax highlighting with proper background colors
- **Cross-platform** - Works on Windows, macOS, and Linux

## Installation

Installation can be done manually running:

```bash
pip install markdown playwright
playwright install chromium
```

If not, the script will attempt to install missing dependencies automatically.

## Usage

```bash
# Basic usage (outputs to same directory with .pdf extension)
python md2pdf.py document.md

# Specify output file
python md2pdf.py document.md output.pdf
```

## Supported Markdown Features

- Headings, paragraphs, and text formatting
- Bullet and numbered lists (including nested)
- Code blocks and inline code
- Links and images
- Tables
- Blockquotes
- Horizontal rules
- GitHub alerts:
  ```markdown
  > [!NOTE]
  > Useful information.

  > [!TIP]
  > Helpful advice.

  > [!IMPORTANT]
  > Key information.

  > [!WARNING]
  > Urgent info that needs attention.

  > [!CAUTION]
  > Potential negative outcomes.
  ```

## Requirements

- Python 3.10+
- markdown
- playwright

## License

MIT