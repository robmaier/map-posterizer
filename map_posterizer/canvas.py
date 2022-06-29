import os
from PIL import Image, ImageDraw, ImageFont

from map_posterizer.drawing_utils import *
from map_posterizer.geo_utils import *


class CanvasStyle:
    """Canvas style"""

    def __init__(self):
        self.load([])

    def __init__(self, config):
        self.load(config)

    def load(self, config):
        # default values
        # self.size_mm = (210, 297)     # din-a4 size
        # self.size_mm = (200, 300)     # 20x30cm
        self.size_mm = (225, 300)       # 22.5x30cm
        self.foreground = (60, 60, 60)
        self.background = (255, 255, 255)
        self.border_mm = (20, 20)
        self.border_background = (255, 255, 255)
        self.font = "Optima"

        # load values from dict
        if "size_mm" in config:
            self.size_mm = config["size_mm"]
        if "foreground" in config:
            self.foreground = tuple(config["foreground"])
        if "background" in config:
            self.background = tuple(config["background"])
        if "border_mm" in config:
            self.border_mm = config["border_mm"]
        if "border_background" in config:
            self.border_background = tuple(config["border_background"])
        if "font" in config:
            self.font = config["font"]


class Canvas:
    """Canvas class"""

    def __init__(self, style, dpi):
        self.style = style
        self.size_mm = style.size_mm
        self.border_mm = style.border_mm
        self.content_size_mm = (style.size_mm[0] - 2 * style.border_mm[0], style.size_mm[1] - 2 * style.border_mm[1])
        self.dpi = dpi

        # calculate pixel dimensions
        self.size_px = mm_to_pixels_tuple(style.size_mm, dpi)
        self.border_px = mm_to_pixels_tuple(style.border_mm, dpi)

        # calculate center pixel location
        self.center_px = (int(self.size_px[0] / 2), int(self.size_px[1] / 2))

        # create canvas image
        self.image = Image.new("RGB", self.size_px, style.border_background)
        draw = ImageDraw.Draw(self.image, "RGB")
        draw.rectangle((self.border_px[0], self.border_px[1], 
                        self.image.size[0] - self.border_px[0] - 1, 
                        self.image.size[1] - self.border_px[1]), 
                        fill=style.background)

    def draw_map(self, map):
        self.map_size_px = map.size
        self.image.paste(map, self.border_px)

    def draw_text_box(self, caption1, caption2, caption3, caption4, coords):
        # draw captions below map
        image_caption1 = caption1
        image_caption2 = caption2

        image_caption3 = caption3
        if image_caption3 == "<location>":
            image_caption3 = geoCoordinatesToPlace(coords)
        
        image_caption4 = caption4
        if coords is None:
            dms = ("", "")
        else:
            dms = degToDMSformatted(coords[0], coords[1])
        if image_caption4 == "":
            image_caption4 = dms[0] + "  " + dms[1]
        if "<lon>" in image_caption4:
            image_caption4 = image_caption4.replace("<lon>", dms[0])
        if "<lat>" in image_caption4:
            image_caption4 = image_caption4.replace("<lat>", dms[1])
        
        # font sizes for captions
        font_size = int(72 / 150 * self.dpi)
        cap1_font = ImageFont.truetype(self.style.font, font_size)
        cap1_color = self.style.foreground

        font_size2 = int(72 / 150 * self.dpi)
        cap2_font = ImageFont.truetype(self.style.font, font_size2)
        cap2_color = self.style.foreground

        font_size3 = int(font_size * 0.70)
        cap3_font = ImageFont.truetype(self.style.font, font_size3)
        cap3_color = (150, 150, 150)

        font_size4 = int(font_size * 0.50)
        cap4_font = ImageFont.truetype(self.style.font, font_size4)
        cap4_color = cap3_color

        # compute caption print sizes
        canvas_draw = ImageDraw.Draw(self.image, "RGBA")
        text_w1, text_h1 = canvas_draw.textsize(image_caption1, font=cap1_font)
        text_spacer2 = 0
        text_w2 = 0
        text_h2 = 0
        if not image_caption2 == "":
            text_spacer2 = mm_to_pixels(5, self.dpi)
            text_w2, text_h2 = canvas_draw.textsize(image_caption2, font=cap2_font)
        text_spacer3 = 0
        text_w3, text_h3 = canvas_draw.textsize(image_caption3, font=cap3_font)
        text_spacer4 = mm_to_pixels(5, self.dpi)
        text_w4, text_h4 = canvas_draw.textsize(image_caption4, font=cap4_font)
        text_spacer5 = mm_to_pixels(10, self.dpi) if image_caption2 == "" else mm_to_pixels(2, self.dpi)

        # compute vertical text alignment
        box_height_px = text_h1 + text_spacer3 + text_h3 + text_spacer4 + text_h4 + text_spacer5
        if not image_caption2 == "":
            box_height_px += text_spacer2 + text_h2

        # compute y offset from box size
        box_height_max_px = self.size_px[1] - 2 * self.border_px[1] - self.map_size_px[1]
        box_free_space_px = box_height_max_px - box_height_px
        box_spacer_px = int(box_free_space_px * 0.3) if box_free_space_px > mm_to_pixels(50, self.dpi) else int(box_free_space_px * 0.5)
        box_y = self.border_px[1] + self.map_size_px[1] + box_spacer_px
        text_spacer3 = box_spacer_px

        pos_y1 = 0
        pos_y2 = pos_y1 + text_spacer2 + text_h1
        pos_y3 = pos_y2 + text_spacer3 + text_h2
        pos_y4 = pos_y3 + text_spacer4 + text_h3

        # draw caption 1
        pos_x = self.center_px[0] - text_w1 / 2
        canvas_draw.text((pos_x, box_y + pos_y1), image_caption1, font=cap1_font, fill=cap1_color, align="center")

        if not image_caption2 == "":
            # draw caption 2
            pos_x = self.center_px[0] - text_w2 / 2
            canvas_draw.text((pos_x, box_y + pos_y2), image_caption2, font=cap2_font, fill=cap2_color, align="center")
        else:
            # draw line
            pos_line_y = box_y + pos_y3 - int(box_spacer_px * 0.5)
            line_indent_x = mm_to_pixels(40, self.dpi) if len(image_caption1) < 15 else mm_to_pixels(30, self.dpi)
            canvas_draw.rectangle((self.border_px[0] + line_indent_x, pos_line_y, self.image.size[0] - self.border_px[0] - line_indent_x, pos_line_y + mm_to_pixels(0.2, self.dpi)), fill=cap1_color)

        # draw caption 3
        pos_x = self.center_px[0] - text_w3 / 2
        canvas_draw.text((pos_x, box_y + pos_y3), image_caption3, font=cap3_font, fill=cap3_color, align="center")

        # draw caption 4
        pos_x = self.center_px[0] - text_w4 / 2
        canvas_draw.text((pos_x, box_y + pos_y4), image_caption4, font=cap4_font, fill=cap4_color, align="center")

    def save(self, filename, show):
        self.image.save(filename, 'PNG')
        if show:
            self.image.show()

    def __str__(self):
        output = str(__class__.__name__) + ":"
        output += os.linesep + "   dpi: " + str(self.dpi)
        output += os.linesep + "   size mm: " + str(self.size_mm) + " mm"
        output += os.linesep + "   size px: " + str(self.size_px) + " px"
        return output
