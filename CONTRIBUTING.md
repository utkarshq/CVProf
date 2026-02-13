# Contributing to CV Generator

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/cv.git
   cd cv
   ```
3. **Set up your environment** following the README.md instructions
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Making Changes

1. **LaTeX Templates**: Edit files in `variants/one_page/` or `variants/two_page/`
2. **Web Resume**: Edit JSON schema in `variants/json/` or theme in `theme/stackoverflow/`
3. **Build System**: Modify `scripts/build.py` or `scripts/render_cv.js`

### Testing Your Changes

Before submitting, verify your changes work:

```bash
# Test full build
python3 scripts/build.py

# Test specific variants
python3 scripts/build.py --web
python3 scripts/build.py --one-page
```

Inspect output in `dist/latest/` to ensure everything renders correctly.

## Code Style

### Python
- Follow PEP 8 style guidelines
- Use descriptive variable names
- Add docstrings to functions
- Prefer explicit over implicit

### JavaScript
- Use `const` and `let`, avoid `var`
- Add JSDoc comments for functions
- Handle errors explicitly

### LaTeX
- Keep consistent indentation (2 spaces)
- Comment complex sections
- Use semantic command names

## Pull Request Process

1. **Update documentation** if you've changed functionality
2. **Test thoroughly** on your local machine
3. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add support for new date format"
   ```
4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** on GitHub with:
   - Clear description of changes
   - Motivation for the change
   - Screenshots if UI-related

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, no logic changes)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## Feature Requests & Bug Reports

### Reporting Bugs

Open an issue on GitHub with:
- **Description** of the bug
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment** (OS, LaTeX version, Node version)

### Suggesting Features

Open an issue on GitHub with:
- **Use case** - what problem does it solve?
- **Proposed solution** - how would you implement it?
- **Alternatives considered** - any other approaches?

## Questions?

Feel free to open a GitHub issue with the `question` label.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
