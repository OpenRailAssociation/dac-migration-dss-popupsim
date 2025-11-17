"""Unified CLI for OSM railway data extraction."""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from .clipper import clip_data
from .extractor import OSMRailwayExtractor
from .models import BoundingBox, Polygon
from .plotter import plot_data
from .projector import project_data

app = typer.Typer(help="OSM Railway Data Extraction Tool")
console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, show_time=False, show_path=False)]
)
logger = logging.getLogger(__name__)


def parse_boundary(coords: str, boundary_type: str):
    """Parse boundary from coordinates string."""
    if boundary_type == "bbox":
        parts = [float(x.strip()) for x in coords.split(",")]
        if len(parts) != 4:
            raise ValueError("Bbox requires 4 values: south,west,north,east")
        return BoundingBox(south=parts[0], west=parts[1], north=parts[2], east=parts[3])
    else:
        pairs = [p.strip().split(",") for p in coords.split()]
        coords_list = [(float(lat), float(lon)) for lat, lon in pairs]
        return Polygon(coordinates=coords_list)


@app.command()
def extract(
    coordinates: str = typer.Argument(..., help="Boundary coordinates"),
    output: Path = typer.Option("railway_data.json", "-o", help="Output file"),
    boundary_type: str = typer.Option("bbox", "-t", help="Boundary type: bbox or polygon"),
    railway_types: Optional[str] = typer.Option("rail,siding,yard,spur", "-r", help="Comma-separated railway types"),
    node_types: Optional[str] = typer.Option("switch,buffer_stop", "-n", help="Comma-separated node types"),
    timeout: int = typer.Option(180, "--timeout", help="Request timeout in seconds"),
    include_disused: bool = typer.Option(False, "--include-disused", help="Include disused/abandoned tracks"),
    include_razed: bool = typer.Option(False, "--include-razed", help="Include razed (demolished) tracks"),
    project: bool = typer.Option(False, "--project", help="Project to Cartesian coordinates"),
    clip: bool = typer.Option(False, "--clip", help="Clip to boundary"),
    show_plot: bool = typer.Option(False, "--plot", help="Show plot after extraction"),
):
    """Extract railway data from OSM."""
    try:
        # Parse boundary
        boundary = parse_boundary(coordinates, boundary_type)
        
        # Parse types
        railway_list = [t.strip() for t in railway_types.split(',')] if railway_types else []
        node_list = [t.strip() for t in node_types.split(',')] if node_types else []
        
        # Extract
        console.print("[1/4] Extracting from OSM...", style="bold blue")
        extractor = OSMRailwayExtractor(
            timeout=timeout, 
            railway_types=railway_list, 
            node_types=node_list,
            include_disused=include_disused,
            include_razed=include_razed
        )
        data = extractor.extract(boundary, filter_geometry=False)
        console.print(f"      Extracted {len(data['elements'])} elements", style="green")
        
        # Project
        if project:
            console.print("[2/4] Projecting coordinates...", style="bold blue")
            data = project_data(data)
            console.print("      Projection complete", style="green")
        
        # Clip
        if clip:
            console.print("[3/4] Clipping to boundary...", style="bold blue")
            original = len(data['elements'])
            data = clip_data(data, boundary)
            console.print(f"      Clipped {original} -> {len(data['elements'])} elements", style="green")
        
        # Save
        console.print("[4/4] Saving...", style="bold blue")
        import json
        with open(output, 'w') as f:
            json.dump(data, f, indent=2)
        console.print(f"      Saved to {output}", style="green")
        
        # Plot
        if show_plot:
            plot_data(data, show_plot=True)
        
        console.print("\nSUCCESS", style="bold green")
        
    except Exception as e:
        console.print(f"\nERROR: {e}", style="bold red")
        raise typer.Exit(1)


@app.command()
def plot(
    input_file: Path = typer.Argument(..., help="Input JSON file"),
    output: Optional[Path] = typer.Option(None, "-o", help="Output image file"),
    show_labels: bool = typer.Option(False, "--labels", help="Show track labels"),
    label_switches: bool = typer.Option(False, "--switch-labels", help="Show switch labels"),
):
    """Plot railway data."""
    try:
        import json
        with open(input_file) as f:
            data = json.load(f)
        
        plot_data(
            data,
            output_file=output,
            title=input_file.stem,
            show_labels=show_labels,
            label_switches=label_switches,
            show_plot=output is None
        )
        
        if output:
            console.print(f"Saved to {output}", style="bold green")
        
    except Exception as e:
        console.print(f"ERROR: {e}", style="bold red")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
