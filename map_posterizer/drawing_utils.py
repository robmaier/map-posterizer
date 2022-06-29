from PIL import Image, ImageDraw, ImageOps

import io
import cairosvg

# --------------------------------------------------------------------
# canvas functions

def mm_to_pixels(size_mm, dpi):
    # conversion constants
    inch_to_mm = 25.4
    mm_to_inch = 1 / inch_to_mm
    # convert size in mm to pixel size
    return int(size_mm * mm_to_inch * dpi)

def mm_to_pixels_tuple(size_mm, dpi):
    width_px = mm_to_pixels(size_mm[0], dpi)
    height_px = mm_to_pixels(size_mm[1], dpi)
    return (width_px, height_px)

# --------------------------------------------------------------------
# drawing functions

def draw_circle(image, pos, radius, fill, outline):
    image_draw = ImageDraw.Draw(image, "RGBA")
    image_draw.ellipse((pos[0] - radius, pos[1] - radius, pos[0] + radius, pos[1] + radius), fill=fill, outline=outline)

def load_svg(filename):
   """Load an SVG file and return image in Numpy array"""
   # Make memory buffer
   mem = io.BytesIO()
   # Convert SVG to PNG in memory
   cairosvg.svg2png(url=filename, write_to=mem)
   # Convert PNG to Numpy array
   return Image.open(mem)

def draw_heart_svg(image, pos, width_px, opacity=1.0):
    # load heart icon from svg
    image_heart = load_svg("resources/pin-heart.svg")
    image_heart_ratio = image_heart.size[1] / image_heart.size[0]
    size_heart = (width_px, int(width_px * image_heart_ratio))
    # resize image
    image_heart = image_heart.resize(size_heart, resample=Image.BICUBIC)
    # scale alpha value
    r, g, b, alpha = image_heart.split()
    alpha = alpha.point(lambda i: i * opacity)
    # paste heart into image
    pos_int = (int(pos[0]) - int(size_heart[0] / 2), int(pos[1]) - size_heart[1])
    image.paste(image_heart, pos_int, alpha)
