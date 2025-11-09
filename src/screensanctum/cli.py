"""Command-line interface for ScreenSanctum."""

import sys
import json
import click
from pathlib import Path

from screensanctum.core import image_loader, redaction, ocr, detection, regions, config
from screensanctum.core.redaction import RedactionStyle
from screensanctum.licensing import license_check
from screensanctum.batch.audit_logger import AuditLogger


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


@cli.command()
@click.option('--input', 'input_dir', required=True, type=click.Path(exists=True),
              help='Path to input directory containing images.')
@click.option('--output', 'output_dir', required=True, type=click.Path(),
              help='Path to output directory for redacted images.')
@click.option('--template-id', 'template_id', type=str,
              help='Template ID to use (e.g., tpl_01_default). Uses active template if not specified.')
@click.option('--template-file', 'template_file', type=click.Path(exists=True),
              help='Path to .sctmpl.json template file (not yet implemented).')
@click.option('--recursive/--no-recursive', default=True,
              help='Process subdirectories recursively (default: True).')
@click.option('--audit/--no-audit', default=True,
              help='Create audit log (.json receipt) (default: True).')
def batch(input_dir, output_dir, template_id, template_file, recursive, audit):
    """Batch process multiple images with a redaction template (Pro only).

    Examples:

        # Process entire folder with default template:
        screensanctum-cli batch --input ./screenshots --output ./redacted

        # Use specific template:
        screensanctum-cli batch --input ./screenshots --output ./redacted --template-id tpl_02_social_share

        # Non-recursive (only top-level directory):
        screensanctum-cli batch --input ./screenshots --output ./redacted --no-recursive
    """
    try:
        # Check for Pro license (batch is Pro-only)
        license_data = license_check.get_verified_license()
        is_pro = license_data is not None and license_data.tier == "pro"

        if not is_pro:
            click.echo("Error: Batch processing requires a Pro license.", err=True)
            click.echo("", err=True)
            click.echo("Batch processing is only available with a Pro license.", err=True)
            click.echo("To purchase a Pro license, visit: https://screensanctum.example.com/purchase", err=True)
            sys.exit(1)

        # Display license info
        click.echo(f"✓ Pro license verified (Licensed to: {license_data.email})")

        # Load configuration
        app_config = config.load_config()

        # Get template
        if template_file:
            # TODO: Implement loading from .sctmpl.json file
            click.echo("Error: --template-file is not yet implemented.", err=True)
            click.echo("Use --template-id instead to select from configured templates.", err=True)
            sys.exit(1)

        # Find template by ID or use active template
        template = None
        if template_id:
            for t in app_config.templates:
                if t.id == template_id:
                    template = t
                    break
            if not template:
                click.echo(f"Error: Template '{template_id}' not found.", err=True)
                click.echo("", err=True)
                click.echo("Available templates:")
                for t in app_config.templates:
                    click.echo(f"  - {t.id}: {t.name}")
                sys.exit(1)
        else:
            # Use active template
            for t in app_config.templates:
                if t.id == app_config.active_template_id:
                    template = t
                    break

        if not template:
            click.echo("Error: No template found.", err=True)
            sys.exit(1)

        click.echo(f"Using template: {template.name} ({template.id})")
        click.echo(f"Input directory: {input_dir}")
        click.echo(f"Output directory: {output_dir}")
        click.echo(f"Recursive: {recursive}")
        click.echo(f"Audit log: {'Enabled' if audit else 'Disabled'}")
        click.echo("")

        # Find all images
        input_path = Path(input_dir)
        SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
        images = []

        if recursive:
            for ext in SUPPORTED_EXTENSIONS:
                images.extend(input_path.rglob(f'*{ext}'))
                images.extend(input_path.rglob(f'*{ext.upper()}'))
        else:
            for ext in SUPPORTED_EXTENSIONS:
                images.extend(input_path.glob(f'*{ext}'))
                images.extend(input_path.glob(f'*{ext.upper()}'))

        images = sorted(images)
        total_files = len(images)

        if total_files == 0:
            click.echo("No images found in input directory.")
            sys.exit(0)

        click.echo(f"Found {total_files} images to process")
        click.echo("")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Create audit logger if enabled
        audit_logger = None
        audit_log_path = ""
        if audit:
            audit_logger = AuditLogger(output_dir, template.id)

        success_count = 0
        error_count = 0

        # Process each image
        with click.progressbar(images, label='Processing images') as bar:
            for image_path in bar:
                # Get relative path to preserve folder structure
                try:
                    relative_path = image_path.relative_to(input_path)
                except ValueError:
                    relative_path = Path(image_path.name)

                # Create output path preserving folder structure
                output_file = output_path / relative_path
                output_file.parent.mkdir(parents=True, exist_ok=True)

                # Process the image
                try:
                    # Load image
                    image = image_loader.load_image(str(image_path))

                    # Run OCR with template's confidence threshold
                    tokens = ocr.run_ocr(image, conf_threshold=template.ocr_conf)

                    # Run detection with template's ignore list
                    items = detection.detect_pii(tokens, template.ignore)

                    # Apply template policy to build regions
                    detected_regions = regions.apply_template_policy(items, template)

                    # Apply redaction using template's default style
                    redacted_image = redaction.apply_redaction(
                        image,
                        detected_regions,
                        template.style.default
                    )

                    # Save redacted image
                    if template.export.format == "png":
                        output_file = output_file.with_suffix('.png')

                    redacted_image.save(str(output_file))

                    # Log to audit logger if enabled
                    if audit_logger:
                        audit_logger.log_file(str(image_path), str(output_file), detected_regions)

                    success_count += 1

                except Exception as e:
                    click.echo(f"\n✗ {relative_path}: {str(e)}", err=True)
                    error_count += 1

        # Save audit log if enabled
        if audit_logger:
            audit_log_path = audit_logger.save_log()

        # Print summary
        click.echo("")
        click.echo("=" * 60)
        click.echo(f"Batch processing complete!")
        click.echo(f"  ✓ Successfully processed: {success_count} files")
        if error_count > 0:
            click.echo(f"  ✗ Errors: {error_count} files")
        click.echo(f"  Output directory: {output_dir}")
        if audit_log_path:
            click.echo(f"  Audit log saved to: {audit_log_path}")
        click.echo("=" * 60)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
