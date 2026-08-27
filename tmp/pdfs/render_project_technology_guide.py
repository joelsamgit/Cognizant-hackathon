from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw


pdf_path = Path("output/pdf/plant-guardian-technology-and-gcp-study-guide.pdf")
out_dir = Path("tmp/pdfs/project-technology-rendered")
out_dir.mkdir(parents=True, exist_ok=True)

document = pymupdf.open(pdf_path)
images = []
for index, page in enumerate(document):
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.15, 1.15), alpha=False)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    image.save(out_dir / f"page-{index + 1}.png")
    images.append((index + 1, image))

label_height = 24
margin = 10
columns = 4
cell_width = max(image.width for _, image in images)
cell_height = max(image.height for _, image in images) + label_height
rows = (len(images) + columns - 1) // columns
sheet = Image.new(
    "RGB",
    (cell_width * columns + margin * (columns + 1), cell_height * rows + margin * (rows + 1)),
    "#dfe9e2",
)
draw = ImageDraw.Draw(sheet)
for position, (page_number, image) in enumerate(images):
    column = position % columns
    row = position // columns
    x = margin + column * (cell_width + margin)
    y = margin + row * (cell_height + margin)
    draw.text((x, y + 3), f"Page {page_number}", fill="#123b2a")
    sheet.paste(image, (x, y + label_height))

sheet.save(out_dir / "contact-sheet.png")
print(f"pages={len(document)}")
