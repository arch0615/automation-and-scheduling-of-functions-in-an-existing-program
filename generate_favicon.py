"""Generate a favicon for the Housoft Meta dashboard."""
from PIL import Image, ImageDraw, ImageFont

# Create 64x64 image
size = 64
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background: rounded square with gradient-like color
# Dark blue background matching the dashboard theme
draw.rounded_rectangle([2, 2, 61, 61], radius=12, fill="#16213e", outline="#e94560", width=2)

# Draw "HM" text (Housoft Meta)
try:
    font = ImageFont.truetype("arial.ttf", 24)
except OSError:
    font = ImageFont.load_default()

# Draw "H" in accent color
draw.text((10, 16), "H", fill="#e94560", font=font)
# Draw "M" in teal
draw.text((32, 16), "M", fill="#4ecdc4", font=font)

# Save as ICO and PNG
ico_path = "web/static/favicon.ico"
png_path = "web/static/favicon.png"

# Save 16x16, 32x32, 64x64 sizes in ICO
img_16 = img.resize((16, 16), Image.LANCZOS)
img_32 = img.resize((32, 32), Image.LANCZOS)

img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (64, 64)])
img.save(png_path, format="PNG")

print(f"Favicon saved to {ico_path} and {png_path}")
