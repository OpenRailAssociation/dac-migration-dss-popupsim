# Documentation Setup

## Local Development

### Install Dependencies
```bash
uv sync --group docs
```

### Serve Documentation Locally
```bash
uv run mkdocs serve
```

The documentation will be available at `http://127.0.0.1:8000`

### Build Static Site
```bash
uv run mkdocs build
```

The static site will be generated in the `site/` directory.

## Commands

- `uv run mkdocs serve` - Start live-reloading dev server
- `uv run mkdocs build` - Build static site
- `uv run mkdocs gh-deploy` - Deploy to GitHub Pages (future)
