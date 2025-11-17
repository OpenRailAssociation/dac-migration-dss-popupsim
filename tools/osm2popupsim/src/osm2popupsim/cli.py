"""CLI for OSM to PopUpSim converter."""

import json
from pathlib import Path

import typer
import yaml

from .converter import convert_osm_to_popupsim
from .converter import extract_tracks_from_osm
from .converter import plot_popupsim_network
from .route_animator import create_animated_map
from .matplotlib_animator import create_matplotlib_animation
from .debug_plotter import plot_topology_debug
from .folium_plotter import plot_popupsim_folium

app = typer.Typer()

@app.command()
def convert(
	input_file: Path = typer.Argument(..., help='Input OSM JSON file'),
	output: Path = typer.Option('topology.yaml', '-o', '--output', help='Output topology YAML file'),
	description: str = typer.Option('Railway network', '-d', '--description', help='Network description'),
	include_disused: bool = typer.Option(False, '--include-disused', help='Include disused/abandoned tracks'),
	include_razed: bool = typer.Option(False, '--include-razed', help='Include razed (demolished) tracks'),
) -> None:
	"""Convert OSM railway data to PopUpSim topology format."""
	try:
		with open(input_file, encoding='utf-8') as f:
			osm_data = json.load(f)

		popupsim_data = convert_osm_to_popupsim(osm_data, description, include_disused, include_razed)

		with open(output, 'w', encoding='utf-8') as f:
			yaml.dump(popupsim_data, f, default_flow_style=False, sort_keys=False)

		typer.echo(f'SUCCESS: Converted {len(popupsim_data["nodes"])} nodes and {len(popupsim_data["edges"])} edges')
		typer.echo(f'Output saved to {output}')

	except Exception as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1) from None

@app.command()
def extract_tracks(
	input_file: Path = typer.Argument(..., help='Input OSM JSON file'),
	topology: Path = typer.Argument(..., help='Topology YAML file path'),
	output: Path = typer.Option('tracks.yaml', '-o', '--output', help='Output tracks YAML file'),
) -> None:
	"""Extract track definitions from OSM railway data."""
	try:
		with open(input_file, encoding='utf-8') as f:
			osm_data = json.load(f)

		tracks_data = extract_tracks_from_osm(osm_data, str(topology))

		with open(output, 'w', encoding='utf-8') as f:
			yaml.dump(tracks_data, f, default_flow_style=False, sort_keys=False)

		typer.echo(f'SUCCESS: Extracted {len(tracks_data["tracks"])} tracks')
		typer.echo(f'Output saved to {output}')

	except Exception as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1) from None

@app.command()
def plot(
	topology_file: Path = typer.Argument(..., help='Topology YAML file'),
	tracks_file: Path = typer.Option(None, '-t', '--tracks', help='Tracks YAML file for labels'),
	output: Path = typer.Option(None, '-o', '--output', help='Output image file'),
) -> None:
	"""Plot PopUpSim railway network."""
	try:
		plot_popupsim_network(str(topology_file), str(tracks_file) if tracks_file else None, str(output) if output else None)
		if output:
			typer.echo(f'SUCCESS: Plot saved to {output}')
		else:
			typer.echo('SUCCESS: Plot displayed')
	except Exception as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1) from None

@app.command()
def animate(
	sequence_file: Path = typer.Argument(..., help='Animation sequence YAML file'),
	topology_file: Path = typer.Argument(..., help='Topology YAML file'),
	tracks_file: Path = typer.Argument(..., help='Tracks YAML file'),
	routes_file: Path = typer.Argument(..., help='Routes YAML file'),
	output: Path = typer.Option('animation.html', '-o', '--output', help='Output HTML file'),
	timestep: float = typer.Option(1.0, '-t', '--timestep', help='Time between frames in seconds'),
) -> None:
	"""Create animated map of train movements."""
	try:
		create_animated_map(sequence_file, topology_file, tracks_file, routes_file, output, timestep)
		typer.echo(f'SUCCESS: Animation saved to {output}')
	except Exception as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1) from None

@app.command()
def animate_matplotlib(
	sequence_file: Path = typer.Argument(..., help='Animation sequence YAML file'),
	topology_file: Path = typer.Argument(..., help='Topology YAML file'),
	tracks_file: Path = typer.Argument(..., help='Tracks YAML file'),
	routes_file: Path = typer.Argument(..., help='Routes YAML file'),
	output: Path = typer.Option('animation.gif', '-o', '--output', help='Output GIF file'),
	timestep: float = typer.Option(1.0, '-t', '--timestep', help='Time between frames in seconds'),
	fps: int = typer.Option(10, '--fps', help='Frames per second'),
) -> None:
	"""Create matplotlib animation of train movements."""
	try:
		create_matplotlib_animation(sequence_file, topology_file, tracks_file, routes_file, output, timestep, fps)
		typer.echo(f'SUCCESS: Animation saved to {output}')
	except Exception as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1) from None

@app.command()
def plot_debug(
	topology_file: Path = typer.Argument(..., help='Topology YAML file'),
	output: Path = typer.Option('debug.html', '-o', '--output', help='Output HTML file'),
) -> None:
	"""Plot topology with all node and edge IDs for debugging."""
	try:
		plot_topology_debug(topology_file, output)
		typer.echo(f'SUCCESS: Debug plot saved to {output}')
	except Exception as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1) from None

@app.command()
def plot_folium(
	topology_file: Path = typer.Argument(..., help='Topology YAML file'),
	tracks_file: Path = typer.Argument(..., help='Tracks YAML file'),
	output: Path = typer.Option('network.html', '-o', '--output', help='Output HTML file'),
	throats_file: Path = typer.Option(None, '--throats', help='Throats YAML file (optional)'),
) -> None:
	"""Plot network with track types and throats using Folium."""
	try:
		plot_popupsim_folium(topology_file, tracks_file, output, throats_file=throats_file)
		typer.echo(f'SUCCESS: Folium plot saved to {output}')
	except Exception as e:
		typer.echo(f'ERROR: {e}', err=True)
		raise typer.Exit(1) from None

if __name__ == '__main__':
	app()
