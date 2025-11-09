"""Celery tasks for asynchronous processing."""

import base64
from io import BytesIO
from PIL import Image

from screensanctum.workers.celery_app import celery_app
from screensanctum.core import config, ocr, detection, regions, redaction


@celery_app.task
def health_check_task():
    """Simple health check task to verify Celery is working."""
    return "Celery worker is alive and well."


@celery_app.task
def redact_image_task(image_b64: str, template_id: str) -> str:
    """Redact an image using the specified template.

    Args:
        image_b64: Base64-encoded image data.
        template_id: ID of the template to use for redaction.

    Returns:
        Base64-encoded redacted image data.
    """
    # 1. Decode image
    image_data = base64.b64decode(image_b64)
    image = Image.open(BytesIO(image_data))

    # 2. Get template
    app_config = config.load_config()
    try:
        template = next(t for t in app_config.templates if t.id == template_id)
    except StopIteration:
        template = next(t for t in app_config.templates if t.id == "tpl_01_default")

    # 3. Re-use ALL our v2.0 core logic
    tokens = ocr.run_ocr(image, template.ocr_conf)
    items = detection.detect_pii(tokens, template.ignore, template.custom_rules)
    region_list = regions.apply_template_policy(items, template)
    redacted_image = redaction.apply_redaction(image, region_list, template.style.default)

    # 4. Encode result
    buffered = BytesIO()
    redacted_image.save(buffered, format="PNG")
    redacted_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return redacted_b64
