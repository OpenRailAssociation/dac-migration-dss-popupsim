"""CLI for OSM railway data extractor."""

import json
import logging
import sys
import typer
from pathlib import Path
from typing import Optional
from typing import Union

# Fix Windows console encoding
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
	sys.stdout.reconfigure(encoding='utf-8')  # type: ignore
	sys.stderr.reconfigure(encoding='utf-8')  # type: ignore

from .clipper import clip_from_file
from .exceptions import ExtractionError
from .exceptions import GeometryError
from .exceptions import PlottingError
from .exceptions import ProjectionError
from .extractor import OSMRailwayExtractor
from .models import BoundingBox
from .models import Polygon
from .plotter import plot_from_file
from .projector import project_from_file

app = typer.Typer(help='OSM Railway Data Extraction Pipeline')
logging.basicConfig(level=logging.INFO, encoding='utf-8')


@app.command()
def extract(
	coordinates: str = typer.Argument(
		...,
		help=("Coordinates as 'lat1,lon1,lat2,lon2' (bbox) or 'lat1,lon1"
        "lat2,lon2 ...' (polygon)"),
	),
	output: Path = typer.Option(
		'railway_data.json', '-o', '--output', help='Output JSON file'
	),
	boundary_type: str = typer.Option(
		'bbox', '-t', '--type', help="Boundary type: 'bbox' or 'polygon'"
	),
	railway_types: Optional[str] = typer.Option(
		'rail,siding,yard,spur',
		'-r',
		'--railway-types',
		help='Comma-separated railway types',
	),
	node_types: Optional[str] = typer.Option(
		'switch,buffer_stop',
		'-n',
		'--node-types',
		help='Comma-separated node types',
	),
	no_filter: bool = typer.Option(
		False, '--no-filter', help='Disable geometry filtering'
	),
	timeout: int = typer.Option(
		60, '--timeout', help='Request timeout in seconds'
	),
) -> None:
	"""Extract railway data from OSM within specified boundary."""

	# Parse coordinates
	try:
		if boundary_type == 'bbox':
			coords = [float(x.strip()) for x in coordinates.split(',')]
			if len(coords) != 4:
				raise ValueError(
					"Bounding box requires 4 coordinates: south,west,"
                    "north,east"
				)
			boundary: Union[BoundingBox, Polygon] = BoundingBox(
				south=coords[0],
				west=coords[1],
				north=coords[2],
				east=coords[3],
			)
		else:
			coord_pairs = []
			for pair in coordinates.split():
				lat, lon = [float(x.strip()) for x in pair.split(',')]
				coord_pairs.append((lat, lon))
			if len(coord_pairs) < 3:
				raise ValueError(
					'Polygon requires at least 3 coordinate pairs'
				)
			boundary = Polygon(coordinates=coord_pairs)
	except ValueError as e:
		typer.echo(f'Error parsing coordinates: {e}', err=True)
		raise typer.Exit(1)

	# Parse types
	railway_list = (
		[t.strip() for t in railway_types.split(',')] if railway_types else []
	)
	node_list = (
		[t.strip() for t in node_types.split(',')] if node_types else []
	)

	# Create extractor
	extractor = OSMRailwayExtractor(
		timeout=timeout, railway_types=railway_list, node_types=node_list
	)

	# Extract data (no filtering by default)
	typer.echo(f'Extracting railway data from {boundary_type}...')
	try:
		data = extractor.extract(boundary, filter_geometry=False)

		# Save to file
		with open(output, 'w', encoding='utf-8') as f:
			json.dump(data, f, indent=2)

		element_count = len(data.get('elements', []))
		typer.echo(f'SUCCESS: Extracted {element_count} elements to {output}')

	except ExtractionError as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1)
	except Exception as e:
		typer.echo(f'ERROR: Unexpected error: {e}', err=True)
		raise typer.Exit(1)


@app.command()
def clip(
	input_file: Path = typer.Argument(..., help='Input JSON file'),
	output: Path = typer.Option(
		'clipped.json', '-o', '--output', help='Output JSON file'
	),
	coordinates: str = typer.Option(
		..., '-c', '--coordinates', help='Boundary coordinates'
	),
	boundary_type: str = typer.Option(
		'bbox', '-t', '--type', help="Boundary type: 'bbox' or 'polygon'"
	),
) -> None:
	"""Clip OSM data to boundary."""
	try:
		boundary: Union[BoundingBox, Polygon]
		if boundary_type == 'bbox':
			coords = [float(x.strip()) for x in coordinates.split(',')]
			boundary = BoundingBox(
				south=coords[0],
				west=coords[1],
				north=coords[2],
				east=coords[3],
			)
		else:
			coord_pairs = [
				(float(p.split(',')[0]), float(p.split(',')[1]))
				for p in coordinates.split()
			]
			boundary = Polygon(coordinates=coord_pairs)

		clip_from_file(input_file, output, boundary)
		typer.echo(f'SUCCESS: Clipped data saved to {output}')

	except GeometryError as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1)
	except Exception as e:
		typer.echo(f'ERROR: Unexpected error: {e}', err=True)
		raise typer.Exit(1)


@app.command()
def project(
	input_file: Path = typer.Argument(..., help='Input JSON file'),
	output: Path = typer.Option(
		'projected.json', '-o', '--output', help='Output JSON file'
	),
) -> None:
	"""Project OSM data to Cartesian coordinates."""
	try:
		project_from_file(input_file, output)
		typer.echo(f'SUCCESS: Projected data saved to {output}')

	except ProjectionError as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1)
	except Exception as e:
		typer.echo(f'ERROR: Unexpected error: {e}', err=True)
		raise typer.Exit(1)


@app.command()
def plot(
	input_file: Path = typer.Argument(..., help='Input JSON file'),
	output: Path = typer.Option(
		'railway_plot.png', '-o', '--output', help='Output image file'
	),
	title: Optional[str] = typer.Option(
		None, '-t', '--title', help='Plot title'
	),
	no_nodes: bool = typer.Option(
		False, '--no-nodes', help='Hide node markers'
	),
	show_boundary: bool = typer.Option(
		False, '--show-boundary', help='Show boundary polygon/bbox'
	),
	coordinates: Optional[str] = typer.Option(
		None, '-c', '--coordinates', help='Boundary coordinates (required with --show-boundary)'
	),
	boundary_type: str = typer.Option(
		'bbox', '--boundary-type', help="Boundary type: 'bbox' or 'polygon'"
	),
) -> None:
	"""Plot railway data."""
	try:
		boundary: Union[BoundingBox, Polygon, None] = None
		if show_boundary:
			if not coordinates:
				typer.echo('ERROR: --coordinates required with --show-boundary', err=True)
				raise typer.Exit(1)
			
			if boundary_type == 'bbox':
				coords = [float(x.strip()) for x in coordinates.split(',')]
				boundary = BoundingBox(
					south=coords[0], west=coords[1], north=coords[2], east=coords[3]
				)
			else:
				coord_pairs = [
					(float(p.split(',')[0]), float(p.split(',')[1]))
					for p in coordinates.split()
				]
				boundary = Polygon(coordinates=coord_pairs)
		
		plot_from_file(
			input_file, output, title=title, show_nodes=not no_nodes, boundary=boundary
		)
		typer.echo(f'SUCCESS: Plot saved to {output}')

	except PlottingError as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1)
	except Exception as e:
		typer.echo(f'ERROR: Unexpected error: {e}', err=True)
		raise typer.Exit(1)


@app.command()
def info() -> None:
	"""Show information about available railway and node types."""
	typer.echo('Available Railway Types:')
	railway_types = [
		'rail',
		'siding',
		'yard',
		'spur',
		'light_rail',
		'subway',
		'tram',
		'monorail',
	]
	for rt in railway_types:
		typer.echo(f'  • {rt}')

	typer.echo('\nAvailable Node Types:')
	node_types = [
		'switch',
		'buffer_stop',
		'railway_crossing',
		'level_crossing',
		'signal',
	]
	for nt in node_types:
		typer.echo(f'  • {nt}')


if __name__ == '__main__':
	app()
