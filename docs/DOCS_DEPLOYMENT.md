# Documentation Deployment

## Overview

The documentation is automatically built and deployed using GitHub Actions:

- **Production**: Deployed to GitHub Pages on every push to `main`
- **Preview**: Deployed as PR preview for every pull request

## URLs

- **Production**: `https://openrailassociation.github.io/dac-migration-dss-popupsim/`
- **PR Preview**: `https://openrailassociation.github.io/dac-migration-dss-popupsim/pr-preview/pr-<number>/`

## Setup

### Enable GitHub Pages

1. Go to repository Settings → Pages
2. Set Source to "Deploy from a branch"
3. Select branch: `gh-pages`
4. Select folder: `/ (root)`
5. Save

### Workflow

The workflow runs on:
- Push to `main` → Production deployment
- Pull request → Preview deployment

## Local Development

```bash
# Install dependencies
uv sync --group docs

# Serve locally
uv run mkdocs serve

# Build
uv run mkdocs build
```

## Preview Deployments

PR previews are automatically:
- Created when PR is opened
- Updated when PR is updated
- Removed when PR is closed/merged

Preview URL is posted as a comment on the PR.
