# md2pdf

Convert Markdown files to PDF with GitHub-flavored styling, including support for GitHub-specific alerts.

## Features

- **GitHub styling** - Renders PDFs with authentic GitHub Markdown appearance
- **Alert support** - Full support for [GitHub alerts](https://github.com/orgs/community/discussions/16925) (`NOTE`,
  `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`)
- **Code blocks** - Syntax highlighting with proper background colors
- **IEE branding** - Optional TU Graz / IEE institutional header and footer
- **Configurable** - Themes via `themes.ini` file

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

# With IEE/TU Graz institutional styling
python md2pdf.py document.md --iee

# With custom theme
python md2pdf.py document.md --iee --theme IEE --config /path/to/themes.ini
```

## Options

| Option | Description                                                  |
|--------|--------------------------------------------------------------|
| `input` | Input markdown file (required)                               |
| `output` | Output PDF file (optional, defaults to input name with .pdf) |
| `--iee` | Add IEE/TU Graz institutional header and footer              |
| `--theme` | Theme name from themes.ini (default: Standard)               |
| `--config` | Path to themes.ini config file (default: themes.ini)         |

## Configuration (themes.ini)

```ini
[DEFAULT]
heading_line_color = #d1d9e0

[Standard]
# Standard theme with black accent
accent_color = #000000
...

[IEE]
# IEE theme with teal accent
accent_color = #008080
...
```

## IEE Styling

When using the `--iee` flag, the PDF includes:
- **Header**: IEE logo (left) + Institute name + TU Graz logo (right)
- **Footer**: Contact information + TU Graz slogan "SCIENCE · PASSION · TECHNOLOGY"
- **Accent color**: Black (#000000) for Standard theme, teal (#008080) for IEE theme
- **Heading lines**: GitHub gray (#d1d9e0)

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

## File Structure

```
md2pdf/
├── md2pdf.py          # Main script
├── themes.ini         # Theme configuration
├── Logo_IEE.png       # IEE logo (required for --iee)
├── Logo_TuGraz.png    # TU Graz logo (required for --iee)
└── README.md
```

## Requirements

- Python 3.10+
- markdown
- playwright

## License

MIT