"""Command-line interface for ScreenSanctum."""

import sys
import click
from pathlib import Path

from screensanctum.core import image_loader, redaction, ocr, detection, regions
from screensanctum.core.redaction import RedactionStyle
from screensanctum.licensing import license_check


@click.group()
@click.version_option(version="0.1.0", prog_name="ScreenSanctum CLI")
def cli():
    """ScreenSanctum - Share your screen, not your secrets.

    Offline-first screenshot redaction tool with automatic PII detection.
    """
    pass


@cli.command()
@click.option('--input', 'input_path', required=True, type=click.Path(exists=True),
              help='Path to input image file.')
@click.option('--output', 'output_path', required=True, type=click.Path(),
              help='Path to save redacted output image.')
@click.option('--style', type=click.Choice(['solid', 'blur', 'pixelate'], case_sensitive=False),
              default='solid', help='Redaction style to apply.')
@click.option('--auto', is_flag=True,
              help='Automatically detect PII (Requires Pro license).')
@click.option('--trusted-domains', multiple=True,
              help='Trusted domains to skip during detection (can be used multiple times).')
def redact(input_path, output_path, style, auto, trusted_domains):
    """Redact sensitive information from an image.

    Examples:

        # Basic mode (manual redaction only - no PII detection):
        screensanctum-cli redact --input screenshot.png --output safe.png

        # Pro mode (automatic PII detection):
        screensanctum-cli redact --input screenshot.png --output safe.png --auto

        # With custom style and trusted domains:
        screensanctum-cli redact --input screenshot.png --output safe.png --auto \\
            --style blur --trusted-domains example.com --trusted-domains user@company.com
    """
    try:
        # Check for Pro license
        license_data = license_check.get_verified_license()
        is_pro = license_data is not None and license_data.tier == "pro"

        # Validate Pro-only features
        if auto and not is_pro:
            click.echo("Error: --auto requires a Pro license.", err=True)
            click.echo("", err=True)
            click.echo("The automatic PII detection feature is only available with a Pro license.", err=True)
            click.echo("You can still use ScreenSanctum CLI in manual mode (without --auto).", err=True)
            click.echo("", err=True)
            click.echo("To purchase a Pro license, visit: https://screensanctum.example.com/purchase", err=True)
            sys.exit(1)

        # Display license info
        if is_pro:
            click.echo(f"✓ Pro license verified (Licensed to: {license_data.email})")
        else:
            click.echo("ℹ Running in Basic mode (no Pro license detected)")

        # Load image
        click.echo(f"Loading image: {input_path}")
        image = image_loader.load_image(input_path)
        click.echo(f"✓ Image loaded: {image.size[0]}x{image.size[1]} pixels")

        # Process regions
        detected_regions = []

        if auto and is_pro:
            click.echo("")
            click.echo("Running automatic PII detection...")
            click.echo("  - Performing OCR...")
            tokens = ocr.run_ocr(image)
            click.echo(f"  - Extracted {len(tokens)} text tokens")

            click.echo("  - Detecting sensitive information...")
            trusted_list = list(trusted_domains) if trusted_domains else []
            items = detection.detect_pii(tokens, trusted_list)
            click.echo(f"  - Found {len(items)} PII items")

            detected_regions = regions.build_regions(items)
            click.echo(f"✓ Created {len(detected_regions)} redaction regions")

            # Show breakdown
            if detected_regions:
                pii_types = {}
                for region in detected_regions:
                    pii_type = region.pii_type.name if region.pii_type else "MANUAL"
                    pii_types[pii_type] = pii_types.get(pii_type, 0) + 1

                click.echo("")
                click.echo("Detected PII breakdown:")
                for pii_type, count in sorted(pii_types.items()):
                    click.echo(f"  - {pii_type}: {count}")
        else:
            click.echo("")
            if auto:
                click.echo("ℹ Running in manual mode (--auto flag requires Pro license)")
            else:
                click.echo("ℹ Running in manual mode (no --auto flag)")
            click.echo("  No automatic detection will be performed.")
            click.echo("  The output will be the original image with metadata stripped.")

        # Apply redaction
        click.echo("")
        click.echo(f"Applying {style.upper()} redaction...")
        style_enum = RedactionStyle[style.upper()]
        redacted_image = redaction.apply_redaction(image, detected_regions, style_enum)

        # Save output
        click.echo(f"Saving to: {output_path}")
        redacted_image.save(output_path)

        click.echo("")
        click.echo(f"✓ Successfully redacted and saved image to {output_path}")

        if detected_regions:
            click.echo(f"✓ {len(detected_regions)} regions were redacted")
        else:
            click.echo("✓ Image metadata was stripped (no regions to redact)")

    except image_loader.ImageLoadError as e:
        click.echo(f"Error: Failed to load image: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
