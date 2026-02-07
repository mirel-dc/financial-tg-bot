"""CLI interface for T-Bank CSV converter."""

from pathlib import Path

import click

from tbank_converter.pipeline import convert


@click.command()
@click.option(
    "--input",
    "-i",
    "input_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to T-Bank CSV file",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    required=True,
    type=click.Path(path_type=Path),
    help="Path for output XLSX file",
)
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to custom config file (default: configs/default.yaml)",
)
def main(input_path: Path, output_path: Path, config_path: Path | None) -> None:
    """Convert T-Bank CSV statements to XLSX with double-entry bookkeeping.

    Reads CSV export from T-Bank, applies double-entry bookkeeping logic,
    and creates XLSX file ready for import into financial tracking spreadsheets.
    """
    try:
        click.echo("Converting T-Bank CSV to XLSX...")

        # Run conversion
        report = convert(input_path, output_path, config_path)

        # Display results
        click.echo("\n[SUCCESS] Conversion completed!")
        click.echo(f"  Operations processed: {len(report.operations)}")

        if report.period_start and report.period_end:
            period = (
                f"{report.period_start.strftime('%d.%m.%Y')} - "
                f"{report.period_end.strftime('%d.%m.%Y')}"
            )
            click.echo(f"  Period: {period}")

        click.echo(f"  Categories used: {len(report.categories)}")
        click.echo(f"  Output: {output_path.absolute()}")

    except FileNotFoundError as e:
        click.echo(f"[ERROR] {e}", err=True)
        raise click.Abort()

    except ValueError as e:
        click.echo(f"[ERROR] {e}", err=True)
        raise click.Abort()

    except Exception as e:
        click.echo(f"[ERROR] Unexpected error: {e}", err=True)
        raise


if __name__ == "__main__":
    main()
