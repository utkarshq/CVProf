"""
CV/Resume Generator Build System

Automated build script for generating professional CVs in multiple formats:
- PDF/DOCX from Jinja2 LaTeX templates + YAML data
- Web resumes from JSON Resume format with i18n support

Architecture:
    config/resume_XX.yaml  →  templates/*.tex.j2  →  pdflatex  →  PDF
    config/resume_XX.yaml  →  JSON Resume format  →  Web/SPA

Features:
- Data-driven: all CV content in YAML, templates are separate
- Multi-language support (English/German)
- Privacy-first: PII isolated in config/ directory
- Selective building via CLI flags

Usage:
    python3 build.py                    # Build all formats
    python3 build.py --web              # Web resumes only
    python3 build.py --one-page --docx  # 1-page PDF+DOCX only
"""

import os
import shutil
import subprocess
import argparse
from datetime import datetime
import glob
import json
import re
import base64
import yaml
from jinja2 import Environment, FileSystemLoader, BaseLoader


# Caches
_personal_config_cache = None
_resume_yaml_cache = {}  # keyed by lang


# Configuration — template-driven variants
VARIANTS = [
    {
        "name": "1Page_EN",
        "template": "cv_1page.tex.j2",
        "data": "config/resume_en.yaml",
        "lang": "en",
        "archival_suffix": "_EN",
        "type": "1Page"
    },
    {
        "name": "1Page_DE",
        "template": "cv_1page.tex.j2",
        "data": "config/resume_de.yaml",
        "lang": "de",
        "archival_suffix": "_DE",
        "type": "1Page"
    },
    {
        "name": "2Page_EN",
        "template": "cv_2page.tex.j2",
        "data": "config/resume_en.yaml",
        "lang": "en",
        "archival_suffix": "_EN",
        "type": "2Page"
    },
    {
        "name": "2Page_DE",
        "template": "cv_2page.tex.j2",
        "data": "config/resume_de.yaml",
        "lang": "de",
        "archival_suffix": "_DE",
        "type": "2Page"
    }
]

def load_resume_yaml(project_root, lang):
    """
    Load and cache resume YAML data for a given language.
    
    Args:
        project_root: Project root directory path
        lang: Language code (e.g., 'en', 'de')
        
    Returns:
        Dictionary with resume data, or empty dict on failure
    """
    global _resume_yaml_cache
    if lang in _resume_yaml_cache:
        return _resume_yaml_cache[lang]
    
    yaml_path = os.path.join(project_root, "config", f"resume_{lang}.yaml")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        _resume_yaml_cache[lang] = data or {}
    except FileNotFoundError:
        print(f"  ! Warning: {yaml_path} not found")
        _resume_yaml_cache[lang] = {}
    except Exception as e:
        print(f"  ! Warning: Failed to load {yaml_path}: {e}")
        _resume_yaml_cache[lang] = {}
    
    return _resume_yaml_cache[lang]


def get_personal_config(project_root):
    """
    Load personal config from YAML (falls back to personal.json for compatibility).
    Returns data in JSON Resume format for the web pipeline.
    """
    global _personal_config_cache
    if _personal_config_cache is not None:
        return _personal_config_cache
    
    # Try YAML first (new system)
    data = load_resume_yaml(project_root, 'en')
    if data and 'basics' in data:
        basics = data['basics']
        _personal_config_cache = {
            "basics": {
                "name": basics.get('name', ''),
                "email": basics.get('email', ''),
                "phone": basics.get('phone', ''),
                "url": basics.get('linkedin', {}).get('url', ''),
                "location": {
                    "city": basics.get('location', '').split(',')[0].strip() if basics.get('location') else '',
                    "countryCode": "DE",
                    "region": ""
                },
                "profiles": [
                    {
                        "network": "LinkedIn",
                        "username": basics.get('linkedin', {}).get('username', ''),
                        "url": basics.get('linkedin', {}).get('url', '')
                    },
                    {
                        "network": "GitHub",
                        "username": basics.get('github', {}).get('username', ''),
                        "url": basics.get('github', {}).get('url', '')
                    }
                ]
            }
        }
        return _personal_config_cache
    
    # Fallback to personal.json
    try:
        with open(os.path.join(project_root, "config", "personal.json"), 'r') as f:
            _personal_config_cache = json.load(f)
    except:
        _personal_config_cache = {}
    return _personal_config_cache


def get_slug_name(project_root):
    """
    Extract slugified name from resume YAML for use in filenames.
    Falls back to "resume" if unavailable.
    """
    data = load_resume_yaml(project_root, 'en')
    if not data:
        data = load_resume_yaml(project_root, 'de')
    name = data.get('basics', {}).get('name', 'resume')
    return name.lower().replace(" ", "_")

# FontAwesome inline cache
_fa_inline_css_cache = None

def get_fontawesome_inline_css(project_root):
    """
    Build a self-contained FontAwesome CSS string with Base64-encoded woff2 fonts.
    
    Reads the local FontAwesome CSS and font files from assets/fontawesome/,
    replaces relative font URLs with data URIs, producing a fully offline CSS blob.
    
    Args:
        project_root: Project root directory path
        
    Returns:
        Complete CSS string with embedded fonts, or empty string on failure
    """
    global _fa_inline_css_cache
    if _fa_inline_css_cache is not None:
        return _fa_inline_css_cache
    
    fa_dir = os.path.join(project_root, "assets", "fontawesome")
    css_path = os.path.join(fa_dir, "all.min.css")
    
    if not os.path.exists(css_path):
        print("  ! Warning: FontAwesome CSS not found at assets/fontawesome/all.min.css")
        _fa_inline_css_cache = ""
        return ""
    
    try:
        with open(css_path, 'r', encoding='utf-8') as f:
            css = f.read()
        
        # Replace each woff2 font URL with Base64 data URI
        font_files = {
            "../webfonts/fa-brands-400.woff2": os.path.join(fa_dir, "webfonts", "fa-brands-400.woff2"),
            "../webfonts/fa-regular-400.woff2": os.path.join(fa_dir, "webfonts", "fa-regular-400.woff2"),
            "../webfonts/fa-solid-900.woff2": os.path.join(fa_dir, "webfonts", "fa-solid-900.woff2"),
        }
        
        for url_ref, font_path in font_files.items():
            if os.path.exists(font_path):
                with open(font_path, "rb") as fnt:
                    b64 = base64.b64encode(fnt.read()).decode('utf-8')
                data_uri = f"data:font/woff2;base64,{b64}"
                css = css.replace(url_ref, data_uri)
        
        # Also replace ttf references with empty (woff2 is sufficient for modern browsers)
        css = re.sub(r'url\(\.\./webfonts/[^)]+\.ttf\)[^,}]*,?', '', css)
        
        _fa_inline_css_cache = css
        return css
    except Exception as e:
        print(f"  ! Warning: Failed to build inline FontAwesome CSS: {e}")
        _fa_inline_css_cache = ""
        return ""

def get_display_name(project_root):
    """
    Extract display name from resume YAML for use in titles.
    Falls back to "Resume" if config unavailable.
    """
    data = load_resume_yaml(project_root, 'en')
    if not data:
        data = load_resume_yaml(project_root, 'de')
    return data.get('basics', {}).get('name', 'Resume')


def render_latex_template(project_root, template_name, data):
    """
    Render a Jinja2 LaTeX template with resume data.
    
    Uses custom delimiters (<< >> for variables, <<for/if>> for blocks)
    to avoid conflicts with LaTeX's {} syntax.
    
    Args:
        project_root: Project root directory path
        template_name: Template filename (e.g., 'cv_2page.tex.j2')
        data: Dictionary of resume data from YAML
        
    Returns:
        Rendered LaTeX string
    """
    template_dir = os.path.join(project_root, "templates")
    
    def latex_escape_text(value):
        """Escape special LaTeX characters in text."""
        if not isinstance(value, str):
            return value
        
        # Protect already-escaped sequences (simple heuristic)
        # We assume if it looks like \& or \# it is intentional
        # But for robustness with simple YAML, we might want to escape everything that isn't a command.
        # Given we allow commands, we should arguably NOT escape? 
        # But the user example uses "#1", which breaks.
        # Let's escape #, $, %, _ if they are NOT escaped.
        
        # Strategy: 
        # 1. Escape & -> \& (unless already escaped)
        # 2. Escape # -> \#
        # 3. Escape $ -> \$
        # 4. Escape % -> \%
        # 5. Escape _ -> \_
        
        # We used a placeholder for & before. Let's do it for others.
        SAFE_AMP = '\x00AMP\x00'
        SAFE_HASH = '\x00HASH\x00'
        SAFE_DOLLAR = '\x00DOLLAR\x00'
        SAFE_PERCENT = '\x00PERCENT\x00'
        SAFE_UNDERSCORE = '\x00US\x00'
        
        value = value.replace('\\&', SAFE_AMP)
        value = value.replace('\\#', SAFE_HASH)
        value = value.replace('\\$', SAFE_DOLLAR)
        value = value.replace('\\%', SAFE_PERCENT)
        value = value.replace('\\_', SAFE_UNDERSCORE)
        
        value = value.replace('&', '\\&')
        value = value.replace('#', '\\#')
        value = value.replace('$', '\\$')
        value = value.replace('%', '\\%')
        value = value.replace('_', '\\_')
        
        value = value.replace(SAFE_AMP, '\\&')
        value = value.replace(SAFE_HASH, '\\#')
        value = value.replace(SAFE_DOLLAR, '\\$')
        value = value.replace(SAFE_PERCENT, '\\%')
        value = value.replace(SAFE_UNDERSCORE, '\\_')
        
        return value

    env = Environment(
        loader=FileSystemLoader(template_dir),
        # Custom delimiters to avoid LaTeX conflicts
        # Variables: << >> (e.g., <<name>>)
        # Blocks: <% %> (e.g., <%for ...%>, <%if ...%>)
        # Comments: <# #>
        variable_start_string='<<',
        variable_end_string='>>',
        block_start_string='<%',
        block_end_string='%>',
        comment_start_string='<#',
        comment_end_string='#>',
        # Keep whitespace control tight for LaTeX
        trim_blocks=True,
        lstrip_blocks=True,
        # Auto-escape for LaTeX
        finalize=latex_escape_text,
    )
    
    template = env.get_template(template_name)
    return template.render(**data)


def generate_personal_tex(project_root, data):
    """
    Auto-generate config/personal.tex from YAML resume data.
    
    This creates the LaTeX \\newcommand definitions that cv_style.sty
    uses for the header (\\makecvheader).
    
    Args:
        project_root: Project root directory path
        data: Resume data dictionary (from any language YAML)
    """
    basics = data.get('basics', {})
    
    # Build personal.tex content
    lines = [
        "% Auto-generated from YAML data — do not edit manually",
        "% Run: python3 scripts/build.py to regenerate",
        "",
        f"\\newcommand{{\\myName}}{{{basics.get('name', 'Name')}}}",
        f"\\newcommand{{\\myLocation}}{{{basics.get('location', 'City, Country')}}}",
        f"\\newcommand{{\\myPhone}}{{{basics.get('phone', '')}}}",
        f"\\newcommand{{\\myEmail}}{{{basics.get('email', '')}}}",
        f"\\newcommand{{\\myLinkedIn}}{{{basics.get('linkedin', {}).get('display', '')}}}",
        f"\\newcommand{{\\myLinkedInUrl}}{{{basics.get('linkedin', {}).get('url', '')}}}",
        f"\\newcommand{{\\myGithub}}{{{basics.get('github', {}).get('display', '')}}}",
        f"\\newcommand{{\\myGithubUrl}}{{{basics.get('github', {}).get('url', '')}}}",
        "",
        # Photo path relative to build/ directory
        f"\\newcommand{{\\myPhotoPath}}{{{'../' + basics['photo'] if basics.get('photo') else ''}}}",
        "",
    ]
    
    tex_path = os.path.join(project_root, "config", "personal.tex")
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def clean_latex(text):
    """
    Strip LaTeX commands from text for Web/JSON output, converting to Markdown where possible.
    Handles: \\href -> [text](url), \\textbf -> **text**, \\emph -> *text*
    """
    if not isinstance(text, str):
        return text
        
    # Replace \\& with &
    text = text.replace('\\&', '&')
    
    # Remove \\newline
    text = text.replace('\\newline', ' ')
    
    # \href{url}{text} -> [text](url) (Markdown)
    while '\\href{' in text:
        # Simple regex for non-nested braces
        # Capture URL (group 1) and Text (group 2)
        new_text = re.sub(r'\\href\{([^}]*)\}\{([^}]*)\}', r'[\2](\1)', text)
        # LaTeX: \href{https://url}{text}
        # Regex: \\href\{([^}]*)\}\{([^}]*)\}
        # Group 1: https://url
        # Group 2: text
        # Markdown: [text](url) -> [\2](\1)
        
        # Let's fix the regex in the replacement content below
        new_text = re.sub(r'\\href\{([^}]*)\}\{([^}]*)\}', r'[\2](\1)', text)
        
        if new_text == text:
            # Fallback if regex fails (complex nesting): just strip command but keep text
            # Try to preserve text part if possible, otherwise strip
            text = text.replace('\\href{', '').replace('}', '') 
            break
        text = new_text

    # \textbf{text} -> **text**, \emph{text} -> *text*
    # Map commands to their markdown delimiters
    cmd_map = {
        '\\textbf': '**',
        '\\emph': '*',
        '\\textit': '*',
        '\\small': '' # No markdown equivalent for small, just strip
    }
    
    for cmd, delim in cmd_map.items():
         while f'{cmd}{{ ' in text or f'{cmd}{{' in text:
            # Construct regex safely without f-string complex escaping
            # Pattern for {{ content }}: \\cmd\{\{([^}]*)\}\}
            pattern_double = r'\\' + cmd[1:] + r'\{\{([^}]*)\}\}'
            # Replacement: delim + group1 + delim
            text = re.sub(pattern_double, f'{delim}\\1{delim}', text)
            
            # Pattern for { content }: \\cmd\{([^}]*)\}
            pattern_single = r'\\' + cmd[1:] + r'\{([^}]*)\}'
            new_text = re.sub(pattern_single, f'{delim}\\1{delim}', text)
            
            if new_text == text:
                 text = text.replace(f'{cmd}{{', '').replace('}', '')
                 break
            text = new_text
            
    # Cleanup any remaining braces if macros were malformed
    # text = text.replace('{', '').replace('}', '') # Too aggressive?
    
    return text.strip()

def yaml_to_json_resume(data, lang):
    """
    Convert YAML resume data to JSON Resume format for the web pipeline.
    """
    basics = data.get('basics', {})
    
    # Determine current date string based on language
    current_date_str = "Heute" if lang == 'de' else "Present"
    
    json_resume = {
        "basics": {
            "name": basics.get('name', ''),
            "label": basics.get('label', ''),
            "email": basics.get('email', ''),
            "phone": basics.get('phone', ''),
            "image": "profile.jpg",
            "summary": clean_latex(data.get('profile', '')),
            "url": basics.get('linkedin', {}).get('url', ''),
            "location": {
                "city": basics.get('location', '').split(',')[0].strip() if basics.get('location') else '',
                "countryCode": "DE",
                "region": ""
            },
            "profiles": [
                {
                    "network": "LinkedIn",
                    "username": basics.get('linkedin', {}).get('username', ''),
                    "url": basics.get('linkedin', {}).get('url', '')
                },
                {
                    "network": "GitHub",
                    "username": basics.get('github', {}).get('username', ''),
                    "url": basics.get('github', {}).get('url', '')
                }
            ]
        },
        "meta": {"theme": "stackoverflow"},
        "work": [],
        "education": [],
        "skills": [],
        "awards": [],
        "languages": [],
        "projects": [],
        "volunteer": []
    }
    
    # Map experience
    for job in data.get('experience', []):
        highlights_raw = job.get('highlights') or job.get('highlights_short') or []
        if isinstance(highlights_raw, str):
             highlights_raw = [highlights_raw]
        
        highlights_clean = [clean_latex(h) for h in highlights_raw]
        
        # Parse dates
        start_date = job.get('date', '').split(' – ')[0] if ' – ' in job.get('date', '') else job.get('date', '')
        end_date = job.get('date', '').split(' – ')[1] if ' – ' in job.get('date', '') else ''
        if not end_date and ' – ' in job.get('date', ''):
             end_date = current_date_str
        
        entry = {
            "name": clean_latex(job.get('company', '')),
            "position": clean_latex(job.get('title', '')),
            "url": job.get('company_url', ''),
            "startDate": start_date,
            "endDate": end_date,
            "highlights": highlights_clean
        }
        if job.get('summary'):
            entry["summary"] = clean_latex(job['summary'])
        json_resume["work"].append(entry)
    
    # Map education
    for edu in data.get('education', []):
        if edu.get('one_page_only'):
            continue
            
        start_date = edu.get('date', '').split(' – ')[0] if ' – ' in edu.get('date', '') else edu.get('date', '')
        end_date = edu.get('date', '').split(' – ')[1] if ' – ' in edu.get('date', '') else ''
        if not end_date and ' – ' in edu.get('date', ''):
             end_date = current_date_str
             
        entry = {
            "institution": clean_latex(edu.get('institution', '')),
            "url": edu.get('institution_url', ''),
            "area": clean_latex(edu.get('degree', '').split(': ')[-1] if ': ' in edu.get('degree', '') else edu.get('degree', '')),
            "studyType": clean_latex(edu.get('degree', '').split(': ')[0] if ': ' in edu.get('degree', '') else ''),
            "startDate": start_date,
            "endDate": end_date,
        }
        # Map coursework to 'courses' (rendered as tags/pills)
        if edu.get('coursework'):
            entry["courses"] = [clean_latex(c.strip()) for c in edu['coursework'].split(',')]
        
        # Map highlights to 'highlights' (rendered as bullet list in modified template)
        if edu.get('highlights'):
             hl_raw = edu.get('highlights')
             if isinstance(hl_raw, str): hl_raw = [hl_raw]
             entry["highlights"] = [clean_latex(h) for h in hl_raw]
            
        json_resume["education"].append(entry)
        
    # Map projects
    for proj in data.get('projects', []):
        hl = proj.get('highlights', [])
        if isinstance(hl, str): hl = [hl]
        
        entry = {
            "name": clean_latex(proj.get('name', '')),
            "description": clean_latex(proj.get('tech', '')),
            "url": proj.get('url', ''),
            "startDate": proj.get('year', ''),
            "highlights": [clean_latex(h) for h in hl]
        }
        json_resume["projects"].append(entry)
        
    # Map certificates -> awards
    for cert in data.get('certificates', []):
        entry = {
            "title": clean_latex(cert.get('name', '')),
            "date": cert.get('date', ''),
            "awarder": clean_latex(cert.get('issuer', '')),
            "summary": cert.get('url', '')
        }
        json_resume["awards"].append(entry)
        
    # Map other experience -> volunteer
    for other in data.get('other_experience', []):
        hl = other.get('highlights', [])
        if isinstance(hl, str): hl = [hl]
        
        start_date = other.get('date', '').split(' – ')[0] if ' – ' in other.get('date', '') else other.get('date', '')
        end_date = other.get('date', '').split(' – ')[1] if ' – ' in other.get('date', '') else ''
        if not end_date and ' – ' in other.get('date', ''):
             end_date = current_date_str
             
        entry = {
            "organization": clean_latex(other.get('organization', '')),
            "position": clean_latex(other.get('title', '')),
            "url": other.get('organization_url', ''),
            "startDate": start_date,
            "endDate": end_date,
            "summary": clean_latex(" ".join(hl)),
            "highlights": [clean_latex(h) for h in hl]
        }
        json_resume["volunteer"].append(entry)
        
    # Map skills
    for skill_group in data.get('skills', []):
        entry = {
            "name": clean_latex(skill_group.get('category', '')),
            "keywords": [clean_latex(k.strip()) for k in skill_group.get('keywords', '').split(',')]
        }
        json_resume["skills"].append(entry)
        
    # Map languages
    for lang_entry in data.get('spoken_languages', []):
        entry = {
            "language": clean_latex(lang_entry.get('language', '')),
            "fluency": clean_latex(lang_entry.get('level', ''))
        }
        json_resume["languages"].append(entry)
        
    return json_resume

def run_command(command, cwd=None):
    """
    Execute a shell command with error handling.
    
    Args:
        command: Shell command string to execute
        cwd: Working directory for command execution (optional)
        
    Returns:
        True if command succeeded, False otherwise
    """
    try:
        subprocess.check_call(command, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(e)
        return False
    return True



# Date translation is now handled by the theme (moment.js) via local vendor


def build_web_resume(project_root, latest_dir, theme_override=None):
    """
    Build JSON Resume HTML files from YAML data with multi-language support.
    
    This function:
    1. Loads YAML data from config/resume_XX.yaml
    2. Converts to JSON Resume format
    3. Renders HTML using vendored theme with locale support
    4. Creates language-specific directories (en/, de/)
    5. Copies profile pictures to each language directory
    
    Args:
        project_root: Project root directory path
        latest_dir: Output directory for latest build (dist/latest/)
        theme_override: Optional theme name to override JSON config
    """
    config_dir = os.path.join(project_root, "config")
    
    # Find all resume YAML files
    yaml_files = sorted(glob.glob(os.path.join(config_dir, "resume_*.yaml")))
    
    if not yaml_files:
        # Fallback: try legacy variants/json/ directory
        json_dir = os.path.join(project_root, "variants", "json")
        if os.path.exists(json_dir):
            json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
            if json_files:
                print("  ! Using legacy variants/json/ files. Consider migrating to config/resume_XX.yaml")
                _build_web_resume_legacy(project_root, latest_dir, theme_override)
                return
        print("No resume YAML files found in config/")
        return

    web_dist_dir = os.path.join(latest_dir, "Web")
    os.makedirs(web_dist_dir, exist_ok=True)

    # Copy Profile Picture once
    profile_pic_src = os.path.join(project_root, "assets", "profilepc_optimized.jpg")
    if os.path.exists(profile_pic_src):
        shutil.copy2(profile_pic_src, os.path.join(web_dist_dir, "profile.jpg"))

    print(f"\n--- Building Web Resumes ({len(yaml_files)} variants) ---")

    built_langs = []

    for yaml_path in yaml_files:
        # Extract lang from filename: resume_en.yaml -> en
        basename = os.path.splitext(os.path.basename(yaml_path))[0]  # resume_en
        lang = basename.split('_')[-1]  # en or de
        
        # Load YAML data
        data = load_resume_yaml(project_root, lang)
        if not data:
            print(f"  ! Failed to load {yaml_path}")
            continue
        
        # Convert YAML to JSON Resume format
        json_resume = yaml_to_json_resume(data, lang)
        
        # Determine Theme
        theme = json_resume.get("meta", {}).get("theme", "stackoverflow")
        if theme_override:
            theme = theme_override

        # Determine Theme Path (Local vendor or npm)
        local_theme_path = os.path.join(project_root, "theme", theme)
        if os.path.exists(local_theme_path):
            theme_arg = local_theme_path
            print(f"    Using local/vendored theme: {theme_arg}")
        else:
            theme_arg = f"jsonresume-theme-{theme}"

        # Create lang directory: dist/latest/Web/en/
        lang_dist_dir = os.path.join(web_dist_dir, lang)
        os.makedirs(lang_dist_dir, exist_ok=True)
        
        output_html = os.path.join(lang_dist_dir, "index.html")
        
        # Copy Profile Picture to each lang dir for relative path correctness
        if os.path.exists(profile_pic_src):
            shutil.copy2(profile_pic_src, os.path.join(lang_dist_dir, "profile.jpg"))

        # Save generated JSON for rendering
        temp_json_name = f"temp_resume_{lang}.json"
        temp_json_path = os.path.join(project_root, temp_json_name)
        with open(temp_json_path, 'w') as f:
            json.dump(json_resume, f, indent=2)

        print(f"  > Building resume_{lang}.json (merged configuration) using theme '{theme}'...")
        
        # Use custom renderer
        render_script = os.path.join(project_root, "scripts", "render_cv.js")
        
        if os.path.exists(local_theme_path):
             theme_script_arg = local_theme_path
        else:
             theme_script_arg = f"jsonresume-theme-{theme}"

        cmd_json = f"node {render_script} {theme_script_arg} {temp_json_path} {output_html}"
        
        success = run_command(cmd_json, cwd=project_root)
        
        if success and os.path.exists(output_html):
            inject_language_switcher(output_html, lang)
            built_langs.append(lang)

        # Cleanup temp file
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)

        if success:
             print(f"    Success: Web/{lang}/index.html")
        else:
             print(f"    Failed to build resume_{lang}")
             
    # Create Root Redirect (index.html)
    if built_langs:
        create_root_router(web_dist_dir, built_langs)
        # Attempt to bundle into Single Page Application
        bundle_spa_resume(web_dist_dir)


def extract_html_content(html_path):
    """
    Extract style and body content from a rendered HTML resume.
    
    Strips injected scripts and language switcher elements to prepare
    content for SPA embedding.
    
    Args:
        html_path: Path to rendered HTML file
        
    Returns:
        Tuple of (style_content, body_content) strings
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        full_html = f.read()

    style_match = re.search(r'<style>(.*?)</style>', full_html, re.DOTALL)
    style_content = style_match.group(1) if style_match else ""
    
    body_match = re.search(r'<body[^>]*>(.*?)</body>', full_html, re.DOTALL)
    body_content = body_match.group(1) if body_match else ""
    
    # Strip injected scripts and switcher (SPA has its own)
    body_content = re.sub(r'<script.*?>.*?</script>', '', body_content, flags=re.DOTALL)
    body_content = re.sub(r'<div id="lang-switcher".*?</div>', '', body_content, flags=re.DOTALL)
    
    return style_content, body_content


def embed_base64_image(body_html, image_path):
    """
    Replace profile.jpg references with Base64 data URI for single-file portability.
    
    Args:
        body_html: HTML string containing src="profile.jpg" references
        image_path: Absolute path to the profile image file
        
    Returns:
        Modified HTML string with embedded Base64 image, or original if encoding fails
    """
    if not os.path.exists(image_path):
        return body_html
    
    try:
        with open(image_path, "rb") as img_file:
            b64_img = base64.b64encode(img_file.read()).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{b64_img}"
        return body_html.replace('src="profile.jpg"', f'src="{data_uri}"')
    except Exception as e:
        print(f"  ! Warning: Failed to base64 encode profile picture: {e}")
        return body_html


def bundle_spa_resume(web_dist_dir):
    """
    Bundle EN and DE resumes into a single-file SPA with Shadow DOM isolation.
    
    Creates a self-contained HTML file with:
    - Both language versions embedded
    - Hash-based routing (#/en, #/de)
    - Floating language switcher button
    - Browser language auto-detection
    - Base64-embedded profile picture
    
    Args:
        web_dist_dir: Path to Web output directory (dist/latest/Web/)
    """
    en_path = os.path.join(web_dist_dir, "en", "index.html")
    de_path = os.path.join(web_dist_dir, "de", "index.html")
    out_path = os.path.join(web_dist_dir, "resume.html")

    if not (os.path.exists(en_path) and os.path.exists(de_path)):
        print("  ! Skipping SPA Bundle: en/index.html or de/index.html missing.")
        return

    # Extract content from rendered HTML files
    style_en, body_en = extract_html_content(en_path)
    style_de, body_de = extract_html_content(de_path)

    # Embed profile picture as Base64 for single-file portability
    profile_pic_src = os.path.join(os.getcwd(), "assets", "profilepc_optimized.jpg")
    body_en = embed_base64_image(body_en, profile_pic_src)
    body_de = embed_base64_image(body_de, profile_pic_src)


    # Build inline FontAwesome CSS for true offline capability
    fa_inline_css = get_fontawesome_inline_css(os.getcwd())
    
    display_name = get_display_name(os.getcwd())
    spa_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_name} CV</title>
    <style>
        {fa_inline_css}
    </style>
    <style>
        body {{ margin: 0; padding: 0; font-family: sans-serif; background: #f0f0f0; }}
        #app {{ display: block; }}
        
        /* Floating Switcher Host Styling */
        #fab-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 10000;
        }}
        
        .fab {{
            display: inline-block;
            padding: 12px 24px;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0,0,0,0.1);
            border-radius: 50px;
            color: #333;
            text-decoration: none;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.2s ease;
            cursor: pointer;
            font-size: 14px;
        }}
        .fab:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }}

        @media print {{
            #fab-container {{ display: none; }}
            body {{ background: white; }}
        }}
    </style>
</head>
<body>

    <div id="app"></div>

    <div id="fab-container">
        <button id="lang-btn" class="fab">Switch to German 🇩🇪</button>
    </div>

    <script>
        const STYLES_EN = `{style_en.replace('`', '\\`')}`;
        const STYLES_DE = `{style_de.replace('`', '\\`')}`;
        const BODY_EN = `{body_en.replace('`', '\\`')}`;
        const BODY_DE = `{body_de.replace('`', '\\`')}`;
        
        const app = document.getElementById('app');
        const btn = document.getElementById('lang-btn');

        function render() {{
            const hash = window.location.hash;
            const isDe = hash === '#/de';
            
            // Update Button
            btn.textContent = isDe ? "Switch to English 🇬🇧" : "Switch to German 🇩🇪";
            btn.onclick = () => {{
                window.location.hash = isDe ? '#/en' : '#/de';
            }};

            const content = isDe ? BODY_DE : BODY_EN;
            const style = isDe ? STYLES_DE : STYLES_EN;

            // Direct DOM injection (no shadow DOM needed for a resume viewer)
            app.innerHTML = `
                <style>
                    ${{style}}
                    @media print {{
                        body {{ background: white; }}
                        .section {{ break-inside: avoid; }}
                    }}
                </style>
                ${{content}}
            `;
            
            // Scroll to top
            window.scrollTo(0, 0);
        }}

        // Listen for hash changes
        window.addEventListener('hashchange', render);
        
        // Initial Render
        // If no hash, detect language
        if (!window.location.hash) {{
             const userLang = navigator.language || navigator.userLanguage; 
             if (userLang.startsWith('de')) {{
                 window.location.hash = '#/de';
             }} else {{
                 window.location.hash = '#/en';
             }}
        }} else {{
            render();
        }}
    </script>
</body>
</html>"""

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(spa_html)
    
    print(f"  > Generated Single-File SPA: Web/resume.html")

    # Promote to dist/latest root for easy access
    try:
        slug_name = get_slug_name(os.getcwd()) # Re-use utility
        promoted_name = f"{slug_name}_resume.html"
        promoted_path = os.path.join(web_dist_dir, "..", promoted_name) # dist/latest/_name.html
        shutil.copy2(out_path, promoted_path)
        print(f"  > Deployed Standalone HTML: {promoted_name}")
    except Exception as e:
        print(f"  ! Warning: Failed to promote HTML: {e}")

def create_root_router(web_dist_dir, available_langs):
    """Generates a root index.html that auto-redirects based on browser language."""
    router_path = os.path.join(web_dist_dir, "index.html")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Redirecting...</title>
    <script>
        (function() {
            var userLang = navigator.language || navigator.userLanguage; 
            if (userLang.startsWith('de')) {
                window.location.href = './de/';
            } else {
                window.location.href = './en/';
            }
        })();
    </script>
</head>
<body>
    <p>Redirecting to language version...</p>
    <ul>
        <li><a href="./en/">English Version</a></li>
        <li><a href="./de/">German Version</a></li>
    </ul>
</body>
</html>"""
    
    with open(router_path, 'w') as f:
        f.write(html_content)
    print("  > Generated Root Router (Auto-Language Detection)")

def inject_language_switcher(html_path, current_lang):
    """
    Injects a floating button to switch language.
    Does NOT use SPA logic, just standard relative links.
    """
    target_lang = "de" if current_lang == "en" else "en"
    target_link = f"../{target_lang}/" # Relative link to sibling directory
    label = "Switch to German 🇩🇪" if current_lang == "en" else "Switch to English 🇬🇧"
    
    switcher_code = f"""
    <div id="lang-switcher" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        font-family: sans-serif;
    ">
        <a href="{target_link}" style="
            display: inline-block;
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 50px;
            color: #333;
            text-decoration: none;
            font-weight: bold;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        " onmouseover="this.style.background='rgba(255, 255, 255, 0.4)'" onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">
            {label}
        </a>
    </div>
    <style>
        @media print {{
            #lang-switcher {{ display: none !important; }}
        }}
    </style>
    """
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "</body>" in content:
            new_content = content.replace("</body>", f"{switcher_code}</body>")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"    Added Language Switcher -> {target_lang}")
    except Exception as e:
        print(f"    Failed to inject switcher: {e}")

def build(docx=False, one_page=False, two_page=False, web=False, theme=None):
    """Main build orchestration function."""
    # Reset caches at start of each build
    global _personal_config_cache, _fa_inline_css_cache, _resume_yaml_cache
    _personal_config_cache = None
    _fa_inline_css_cache = None
    _resume_yaml_cache = {}
    
    project_root = os.getcwd()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    latest_dir = os.path.join(project_root, "dist", "latest")
    
    # Determine selection
    build_all = not (one_page or two_page or web)
    do_1page = build_all or one_page
    do_2page = build_all or two_page
    do_web = build_all or web

    # 1. Build PDFs
    variants_to_build = []
    if do_1page:
        variants_to_build.extend([v for v in VARIANTS if v["type"] == "1Page"])
    if do_2page:
        variants_to_build.extend([v for v in VARIANTS if v["type"] == "2Page"])

    # Ensure directories exist
    os.makedirs(latest_dir, exist_ok=True)
    
    slug_name = get_slug_name(project_root)

    print(f"Build started for date: {today_str}")
    
    if variants_to_build:
        # Generate personal.tex from YAML (once, using EN data as canonical)
        en_data = load_resume_yaml(project_root, 'en')
        if not en_data:
            en_data = load_resume_yaml(project_root, 'de')
        if en_data:
            generate_personal_tex(project_root, en_data)
            print("  > Generated config/personal.tex from YAML data")
        
        # Build directory for rendered .tex files
        build_dir = os.path.join(project_root, "build")
        os.makedirs(build_dir, exist_ok=True)
        
        for variant in variants_to_build:
            print(f"\n--- Building Variant: {variant['name']} ---")
            
            variant_type = variant["type"]  # e.g. "1Page" or "2Page"
            latest_type_dir = os.path.join(latest_dir, variant_type)
            os.makedirs(latest_type_dir, exist_ok=True)
            
            # Load YAML data
            lang = variant["lang"]
            data = load_resume_yaml(project_root, lang)
            if not data:
                print(f"  ! Failed to load YAML for {variant['name']}")
                continue
            
            # Filter data based on variant type (1Page vs 2Page)
            # This prevents empty list errors in LaTeX by verifying content visibility
            if variant_type == "1Page":
                # Filter out items marked as two_page_only
                for section in ['experience', 'education', 'projects', 'other_experience', 'certificates']:
                    if section in data and isinstance(data[section], list):
                        data[section] = [item for item in data[section] if not item.get('two_page_only', False)]
            elif variant_type == "2Page":
                # Filter out items marked as one_page_only
                for section in ['experience', 'education', 'projects', 'other_experience', 'certificates']:
                    if section in data and isinstance(data[section], list):
                        data[section] = [item for item in data[section] if not item.get('one_page_only', False)]
            
            # Render Jinja2 template -> .tex
            template_name = variant["template"]
            try:
                rendered_tex = render_latex_template(project_root, template_name, data)
            except Exception as e:
                print(f"  ! Template rendering failed for {variant['name']}: {e}")
                continue
            
            # Write rendered .tex to build directory
            tex_filename = f"cv_{variant_type.lower()}_{lang}.tex"
            tex_path = os.path.join(build_dir, tex_filename)
            with open(tex_path, 'w', encoding='utf-8') as f:
                f.write(rendered_tex)
            
            print(f"  > Rendered template: build/{tex_filename}")
            
            # Compile PDF
            cmd = f"pdflatex -interaction=nonstopmode -output-directory={build_dir} {tex_filename}"
            if not run_command(cmd, cwd=build_dir):
                continue
            
            # Identify generated PDF
            pdf_filename = tex_filename.replace(".tex", ".pdf")
            pdf_path = os.path.join(build_dir, pdf_filename)
            
            if not os.path.exists(pdf_path):
                print(f"Failed to generate PDF for {variant['name']}")
                continue

            # Deploy (Latest)
            simple_name = f"_{slug_name}_cv.pdf" if "EN" in variant['archival_suffix'] else f"_{slug_name}_lebenslauf.pdf"
            latest_path = os.path.join(latest_type_dir, simple_name)
            shutil.copy2(pdf_path, latest_path)
            print(f"Deployed Latest: {variant_type}/{simple_name}")

            # Cleanup Aux files in build dir
            for ext in ['.aux', '.log', '.out', '.fls', '.fdb_latexmk', '.synctex.gz']:
                aux_file = os.path.join(build_dir, tex_filename.replace(".tex", ext))
                if os.path.exists(aux_file):
                    os.remove(aux_file)

            # Compile DOCX
            if docx:
                print(f"Generating DOCX for {variant['name']}...")
                docx_filename = tex_filename.replace(".tex", ".docx")
                docx_source_path = os.path.join(build_dir, docx_filename)
                
                cmd_docx = f"pandoc {tex_filename} -o {docx_filename}"
                if run_command(cmd_docx, cwd=build_dir):
                    simple_docx_name = f"_{slug_name}_cv.docx" if "EN" in variant['archival_suffix'] else f"_{slug_name}_lebenslauf.docx"
                    shutil.copy2(docx_source_path, os.path.join(latest_type_dir, simple_docx_name))
                    print(f"Generated DOCX: {variant_type}/{simple_docx_name}")
                    if os.path.exists(docx_source_path):
                        os.remove(docx_source_path)

    # 2. Web Resume Generation (from YAML -> JSON Resume)
    if do_web:
        build_web_resume(project_root, latest_dir, theme_override=theme)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build automation for CV")
    parser.add_argument("--docx", action="store_true", help="Generate DOCX files")
    parser.add_argument("--one-page", action="store_true", help="Build only 1-page variants")
    parser.add_argument("--two-page", action="store_true", help="Build only 2-page variants")
    parser.add_argument("--web", action="store_true", help="Build Web/JSON variant")
    parser.add_argument("--theme", type=str, help="Override JSON Resume theme (e.g. flat, stackoverflow)")
    
    args = parser.parse_args()
    
    build(docx=args.docx, one_page=args.one_page, two_page=args.two_page, web=args.web, theme=args.theme)
