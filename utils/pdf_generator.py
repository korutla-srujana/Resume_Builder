import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


PAGE_WIDTH_PX = 794
PAGE_HEIGHT_PX = 1123


def find_chrome():
    candidates = [
        shutil.which("chrome"),
        shutil.which("chrome.exe"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)

    raise FileNotFoundError("Google Chrome not found for PDF export.")


def run_chrome(command, timeout=60):
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            "Chrome export failed: "
            f"{result.stderr.strip() or result.stdout.strip() or 'Unknown error'}"
        )
    return result


def extract_link_metadata(dom_text):
    match = re.search(
        r'<pre id="pdf-link-metadata"[^>]*>(.*?)</pre>',
        dom_text,
        re.DOTALL,
    )
    if not match:
        return {"pageWidth": PAGE_WIDTH_PX, "pageHeight": PAGE_HEIGHT_PX, "links": []}

    raw_json = (
        match.group(1)
        .replace("&quot;", '"')
        .replace("&#34;", '"')
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    ).strip()

    if not raw_json:
        return {"pageWidth": PAGE_WIDTH_PX, "pageHeight": PAGE_HEIGHT_PX, "links": []}

    try:
        metadata = json.loads(raw_json)
    except json.JSONDecodeError:
        return {"pageWidth": PAGE_WIDTH_PX, "pageHeight": PAGE_HEIGHT_PX, "links": []}

    metadata.setdefault("pageWidth", PAGE_WIDTH_PX)
    metadata.setdefault("pageHeight", PAGE_HEIGHT_PX)
    metadata.setdefault("links", [])
    return metadata


def build_pdf_from_snapshot(image_path, metadata, output_path):
    page_width_pt, page_height_pt = A4
    page_width_px = float(metadata.get("pageWidth") or PAGE_WIDTH_PX)
    page_height_px = float(metadata.get("pageHeight") or PAGE_HEIGHT_PX)
    scale_x = page_width_pt / page_width_px
    scale_y = page_height_pt / page_height_px

    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    pdf.drawImage(
        ImageReader(str(image_path)),
        0,
        0,
        width=page_width_pt,
        height=page_height_pt,
        preserveAspectRatio=False,
        mask="auto",
    )

    for link in metadata.get("links", []):
        href = str(link.get("href", "")).strip()
        if not href or not href.startswith(("http://", "https://", "mailto:", "tel:")):
            continue

        left = float(link.get("left", 0))
        top = float(link.get("top", 0))
        width = float(link.get("width", 0))
        height = float(link.get("height", 0))
        if width <= 0 or height <= 0:
            continue

        x1 = left * scale_x
        y1 = page_height_pt - ((top + height) * scale_y)
        x2 = (left + width) * scale_x
        y2 = page_height_pt - (top * scale_y)
        pdf.linkURL(href, (x1, y1, x2, y2), relative=0, thickness=0)

    pdf.showPage()
    pdf.save()


def generate_pdf(html_content, filename="resume.pdf"):
    chrome_path = find_chrome()
    output_path = Path(filename).resolve()
    temp_dir = output_path.parent / ".pdf_export_work"
    temp_dir.mkdir(exist_ok=True)

    export_id = uuid.uuid4().hex
    html_path = temp_dir / f"resume_export_{export_id}.html"
    screenshot_path = temp_dir / f"resume_export_{export_id}.png"

    try:
        html_path.write_text(html_content, encoding="utf-8")
        file_url = html_path.resolve().as_uri()

        screenshot_command = [
            chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--hide-scrollbars",
            "--disable-crash-reporter",
            "--disable-breakpad",
            f"--window-size={PAGE_WIDTH_PX},{PAGE_HEIGHT_PX}",
            "--force-device-scale-factor=2",
            "--run-all-compositor-stages-before-draw",
            f"--screenshot={screenshot_path}",
            file_url,
        ]
        run_chrome(screenshot_command)

        if not screenshot_path.exists():
            raise RuntimeError("Chrome screenshot export did not create an image.")

        with Image.open(screenshot_path) as snapshot:
            snapshot.load()

        metadata_command = [
            chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--hide-scrollbars",
            "--disable-crash-reporter",
            "--disable-breakpad",
            f"--window-size={PAGE_WIDTH_PX},{PAGE_HEIGHT_PX}",
            "--force-device-scale-factor=1",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=2000",
            "--dump-dom",
            file_url,
        ]
        metadata_result = run_chrome(metadata_command)
        metadata = extract_link_metadata(metadata_result.stdout)

        build_pdf_from_snapshot(screenshot_path, metadata, output_path)
    finally:
        for temp_path in (html_path, screenshot_path):
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass
