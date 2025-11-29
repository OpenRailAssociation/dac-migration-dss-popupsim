# ADR-009: Matplotlib for Visualization

**Status:** Accepted - 2025-01-15

## Context

Need visualization for simulation results. Full version will have web interface, but MVP needs simple charts.

## Decision

Use **Matplotlib** for generating static charts (PNG files).

## Rationale

- **Simple**: Easy to use, well-known library
- **Offline**: No web server required
- **Sufficient**: Meets MVP visualization needs
- **Python native**: Integrated in Python ecosystem
- **No frontend developer**: Backend team can handle it
- **Fast development**: Quick to implement basic charts

## Alternatives Considered

- **Matplotlib** ✅ Chosen
- **Plotly**: Interactive but requires web server
- **Bokeh**: Overkill for static charts
- **Seaborn**: Built on Matplotlib, no significant advantage
- **Custom web charts**: Requires frontend development

## Consequences

- **Positive**: Fast implementation, no web complexity
- **Negative**: Static charts only (acceptable for MVP)
- **Migration**: JSON data export prepared for web charts in full version