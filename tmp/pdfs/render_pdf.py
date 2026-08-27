from pathlib import Path

import fitz
from PIL import Image, ImageDraw


pdf_path = Path("output/pdf/plant-guardian-gcp-connection-guide.pdf")
out_dir = Path("tmp/pdfs/rendered")
out_dir.mkdir(parents=True, exist_ok=True)

document = fitz.open(pdf_path)
page_indexes = list(range(len(document)))
images = []
for index in page_indexes:
    page = document[index]
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    page_path = out_dir / f"page-{index + 1}.png"
    image.save(page_path)
    images.append((index + 1, image))

label_height = 26
margin = 12
columns = 3
cell_width = max(image.width for _, image in images)
cell_height = max(image.height for _, image in images) + label_height
rows = (len(images) + columns - 1) // columns
sheet = Image.new("RGB", (cell_width * columns + margin * (columns + 1), cell_height * rows + margin * (rows + 1)), "#dfe9e2")
draw = ImageDraw.Draw(sheet)
for position, (page_number, image) in enumerate(images):
    column = position % columns
    row = position // columns
    x = margin + column * (cell_width + margin)
    y = margin + row * (cell_height + margin)
    draw.text((x, y + 4), f"Page {page_number}", fill="#123b2a")
    sheet.paste(image, (x, y + label_height))

sheet.save(out_dir / "contact-sheet.png")
print(f"pages={len(document)} rendered={','.join(str(index + 1) for index in page_indexes)}")
