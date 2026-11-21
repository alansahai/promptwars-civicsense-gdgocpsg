# Contributing to CivicResolve

Thank you for contributing to CivicResolve! We adhere to strict code quality and security standards.

## Engineering Standards

1. **Max Function Length**: Every function or method in `app/` and `public/js/` must not exceed 40 lines of code (excluding docstrings).
2. **Documentation**: Every public module, class, function, and method must have a descriptive docstring.
3. **Zero innerHTML**: The frontend uses safe DOM construction via `h()` and `svg()` in `public/js/dom.js`. Direct assignments to `innerHTML`, `insertAdjacentHTML`, or `outerHTML` are strictly disallowed.
4. **Content Security Policy**: The Content Security Policy in `app/security_headers.py` and `vercel.json` forbids `unsafe-inline` styles and scripts.
5. **Test Coverage**: Test coverage across `app/` must remain at or above 90% overall, with every module at 80% or higher.

## Development Workflow

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run linter
ruff check .

# Run test suite with coverage enforcement
pytest --cov=app --cov-report=term-missing --cov-fail-under=90

# Verify browser UI workflows
python scripts/verify_ui.py
```
