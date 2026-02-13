# CV & Resume Generator

A comprehensive, automated system for generating professional Curriculum Vitae (CV) in both PDF/DOCX (LaTeX) and Web (JSON Resume) formats, supporting multiple languages and themes.

## 📂 Project Structure

```
├── config/               # Data & Configuration
│   ├── resume_en.yaml    # English CV Data (Gitignored)
│   ├── resume_de.yaml    # German CV Data (Gitignored)
│   ├── example_resume.yaml # Template for new users
│   └── personal.tex      # Auto-generated LaTeX PII
├── templates/            # Jinja2 LaTeX Templates
│   ├── cv_1page.tex.j2   # 1-Page Variant
│   └── cv_2page.tex.j2   # 2-Page Variant
├── theme/                # Shared Styles
│   └── cv_style.sty      # LaTeX Style Definitions
├── assets/               # Images (Gitignored)
├── scripts/
│   └── build.py          # Unified build automation script
├── dist/                 # Build Artifacts (Gitignored)
└── README.md
```

## 🚀 Getting Started

### Prerequisites

1.  **Python 3.x**
2.  **LaTeX Distribution** (TeX Live recommended)
3.  **Node.js & NPM** (for Web Resume)
4.  **Pandoc** (optional, for DOCX generation)

### Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone <repo-url>
    cd cv
    ```

2.  **Install Python Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Personal Data**
    The project separates templates from personal data for privacy.
    
    ```bash
    # Copy example template
    cp config/example_resume.yaml config/resume_en.yaml
    
    # Edit with your details
    vim config/resume_en.yaml
    ```
    
    For German version, create `config/resume_de.yaml`.
    
    > **Note**: Place your profile picture in `assets/` and update the `photo` path in your YAML file.

4.  **Install Node Dependencies** (for Web Resume)
    ```bash
    npm install
    ```

## 🛠️ Build Commands

The project uses a unified build script `scripts/build.py`.

### Standard Build (Build Everything)
```bash
python3 scripts/build.py
```

### Selective Building
Improve iteration speed by building only what you need:

```bash
# Build only 1-page PDF/DOCX
python3 scripts/build.py --one-page

# Build only 2-page PDF/DOCX
python3 scripts/build.py --two-page

# Build only Web Resumes (JSON)
python3 scripts/build.py --web
```

### Additional Flags
- `--docx`: Generate DOCX files alongside PDFs.
- `--theme <name>`: Override the web resume theme (e.g., `flat`, `stackoverflow`).

## 🌐 Web Resume (JSON Resume)

The system generates HTML resumes by converting your YAML data to JSON Resume format on the fly.

**Build Output:**
- **English**: `dist/latest/Web/en/index.html`
- **German**: `dist/latest/Web/de/index.html`
- **Single-File (Email)**: `dist/latest/_{your_name}_cv_web.html` (embeds all languages + images)
- **Auto-Router**: `dist/latest/Web/index.html` (browser language detection)

## 🏗️ Architecture

### Project Layout
- **`config/*.yaml`**: Single source of truth for all data.
- **`templates/*.j2`**: Layout definitions.
- **`build.py`**: Orchestrates rendering (Jinja2 -> LaTeX) and conversion (YAML -> JSON).

### Build Process
1. **LaTeX PDFs**: JSON data is rendered into `.tex` templates using Jinja2, then compiled with `pdflatex`.
2. **Web Resumes**: YAML is converted to JSON Resume format, then rendered using `render_cv.js`.
3. **Archival**: Previous builds can be moved to `dist/releases/` (configurable).
