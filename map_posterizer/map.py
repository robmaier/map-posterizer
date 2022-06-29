from io import BytesIO
import os
import threading

from PIL import Image, ImageOps
import urllib.request

from map_posterizer.drawing_utils import *
from map_posterizer.geo_utils import *

class MapLocation:
    """Map location"""

    def __init__(self):
        self.load([])

    def __init__(self, config):
        self.load(config)

    def load(self, config):
        # default values
        # note: coords for lat/lon and tl/br region from https://www.openstreetmap.org/export#map=12/48.1479/11.5549
        self.name = None
        self.top_left = None
        self.bottom_right = None
        self.zoom = None
        self.marker = None
        self.hide_marker = False
        self.caption1 = "H O M E"
        self.caption2 = ""
        self.caption3 = "<location>"
        self.caption4 = "<lon>  <lat>"

        # load values from dict
        if "name" in config:
            self.name = config["name"]
        if "location" in config:
            if "top_left" in config["location"]: 
                self.top_left = config["location"]["top_left"]
            if "bottom_right" in config["location"]: 
                self.bottom_right = config["location"]["bottom_right"]
            if "marker" in config["location"]: 
                self.marker = config["location"]["marker"]
            if "hide_marker" in config["location"]: 
                self.hide_marker = config["location"]["hide_marker"]
        if "zoom" in config:
            self.zoom = config["zoom"]
            if self.zoom < 13 or self.zoom > 18:
                self.zoom = None
        if "caption" in config:
            if "caption1" in config["caption"]: 
                self.caption1 = config["caption"]["caption1"]
            if "caption2" in config["caption"]: 
                self.caption2 = config["caption"]["caption2"]
            if "caption3" in config["caption"]: 
                self.caption3 = config["caption"]["caption3"]
            if "caption4" in config["caption"]: 
                self.caption4 = config["caption"]["caption4"]

    def get_marker_coords(self):
        if self.hide_marker is None:
            center_coord_x = self.bottom_right[0] + (self.bottom_right[0] - self.top_left[0]) / 2
            center_coord_y = self.bottom_right[1] + (self.bottom_right[1] - self.top_left[1]) / 2
            return (center_coord_x, center_coord_y)
        else:
            return self.marker

    def __str__(self):
        output = str(__class__.__name__) + ":"
        output += os.linesep + "   name: " + self.name
        output += os.linesep + "   coords top-left: " + str(self.top_left)
        output += os.linesep + "   coords bottom-right: " + str(self.bottom_right)
        if self.marker:
            output += os.linesep + "   coords marker: " + str(self.marker)
        output += os.linesep + "   zoom level: " + str(self.zoom)
        return output

class MapStyle:
    """Map style"""

    def __init__(self):
        self.load([])

    def __init__(self, config):
        self.load(config)

    def load(self, config):
        # default values
        self.style = "toner"
        self.foreground = (255, 255, 255)
        self.background = (60, 60, 60)
        self.boost_contrast = True
        self.marker_size_mm = (8, 8)
        self.marker_style = "none"
        self.marker_opacity = 1.0

        # load values from dict
        if "foreground" in config:
            self.foreground = tuple(config["foreground"])
        if "background" in config:
            self.background = tuple(config["background"])
        if "boost_contrast" in config:
            self.boost_contrast = config["boost_contrast"]
        if "marker" in config:
            if "size_mm" in config["marker"]:
                self.marker_size_mm = config["marker"]["size_mm"]
            if "style" in config["marker"]:
                self.marker_style = config["marker"]["style"]
            if "opacity" in config["marker"]:
                self.marker_opacity = config["marker"]["opacity"]


class MapTileProvider:
    """Map tile provider class"""

    def _create_map_tile_providers():
        provider_toner = {
            "name": "toner",
            "url": "http://tile.stamen.com/toner-background/{0}/{1}/{2}.png",
            "copyright": "Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
            "web": "http://maps.stamen.com/toner",
        }
        providers = {
            "toner": provider_toner,
        }
        return providers

    def __init__(self, map_style, tiles_folder, use_cache):
        # increase max image size for outputting HR maps
        Image.MAX_IMAGE_PIXELS = 933120000 # or 231952900

        # find map tile provider
        providers = MapTileProvider._create_map_tile_providers()
        if map_style in providers:
            self.provider = providers[map_style]
        else:
            self.provider = providers["toner"]

        self.tiles_folder = tiles_folder + "{0}/{1}/{2}/"
        self.tiles_file = self.tiles_folder + "/{3}.png"
        self.use_cache = use_cache

    def make_tiles_dir(self, zoom, tile_y):
        tile_dir = self.tiles_folder.format(self.provider["name"], zoom, tile_y)
        if not os.path.exists(tile_dir):
            os.makedirs(tile_dir)

    def _make_tile_filename(self, zoom, tile_x, tile_y):
        return self.tiles_file.format(self.provider["name"], zoom, tile_y, tile_x)

    def _download_url(self, url):
        for i in range(5):
            try: 
                # print("downloading (trial " + str(i) + ") " + url)
                response = urllib.request.urlopen(url)
                content = response.read()
                response.close()
            except urllib.error.URLError as e:  
                print("Download URLError " + str(e.reason))
                content = bytes()
            except urllib.error.HTTPError as e:
                print("Download HTTPError " + str(e.reason))
                content = bytes()
            except ConnectionResetError as e:
                print("Download ConnectionResetError ")
                content = bytes()
            else:
                break
        return content

    def _download_image(self, url):
        content = self._download_url(url)
        tile_image = Image.open(BytesIO(content))
        return tile_image

    def download_tile(self, zoom, tile_x, tile_y, save_image):
        # download file if it doesn't exist
        tile_file = self._make_tile_filename(zoom, tile_x, tile_y)
        if not os.path.isfile(tile_file) or not self.use_cache:
            tile_url = self.provider["url"].format(zoom, tile_x, tile_y)
            tile_image = self._download_image(tile_url)
            if save_image:
                tile_image.save(tile_file, "PNG")
            return tile_image
        else:
            return None

    def load_tile(self, zoom, tile_x, tile_y):
        if self.use_cache:
            # load tile from disk
            tile_file = self._make_tile_filename(zoom, tile_x, tile_y)
            if os.path.isfile(tile_file):
                return Image.open(tile_file)
            else:
                return None
        else:
            return self.download_tile(zoom, tile_x, tile_y, False)
    

class Map:
    """Map class"""

    tile_size_px = (256, 256)

    def __init__(self, style, size_mm, dpi, corner_tl_deg, corner_br_deg, zoom):
        self.style = style
        # create map tile provider
        self.map_tile_provider = MapTileProvider(style.style, "cache/", True)
        # map size and resolution
        self.size_px = mm_to_pixels_tuple((size_mm[0], size_mm[1]), dpi)
        sides_ratio = float(self.size_px[1]) / self.size_px[0]
        self.dpi = dpi
        self.zoom = zoom

        # compute tile grid dimensions
        corner_tl_tile, corner_br_tile = degToCornerTiles(corner_tl_deg, corner_br_deg, self.zoom)
        num_tiles = numTilesFromCorners(corner_tl_tile, corner_br_tile, make_squared=True)
        # align vertical tiles with map sides ratio
        num_tiles = (num_tiles[0], int(math.ceil(float(num_tiles[0]) * sides_ratio)))
        # update br tile to account for squared grid
        corner_br_tile = (corner_tl_tile[0] + num_tiles[0], corner_tl_tile[1] + num_tiles[1])
        # calculate raw map size
        self.raw_size_px = (num_tiles[0] * Map.tile_size_px[0], num_tiles[1] * Map.tile_size_px[1])

        # compute global tiles locations
        self.num_tiles = num_tiles
        self.corner_tl_tile = corner_tl_tile
        self.corner_br_tile = corner_br_tile
        # compute global xy locations on tiles
        corner_tl_xy = degToXY(corner_tl_deg[0], corner_tl_deg[1], self.zoom)
        corner_br_xy = degToXY(corner_br_deg[0], corner_br_deg[1], self.zoom)
        # align bottom right xy location with map sides ratio
        corner_br_xy = (corner_br_xy[0], corner_tl_xy[1] + (corner_br_xy[0] - corner_tl_xy[0]) * sides_ratio)
        # compute tl and br in local pixels
        self.corner_tl_px_x = int(corner_tl_xy[0] - self.corner_tl_tile[0] * Map.tile_size_px[0])
        self.corner_tl_px_y = int(corner_tl_xy[1] - self.corner_tl_tile[1] * Map.tile_size_px[1])
        self.corner_br_px_x = int(corner_br_xy[0] - self.corner_tl_tile[0] * Map.tile_size_px[0])
        self.corner_br_px_y = int(corner_br_xy[1] - self.corner_tl_tile[1] * Map.tile_size_px[1])

        # create raw map image
        self.image_raw = Image.new("RGB", self.raw_size_px, "white")

    def download_tiles(self):
        if self.map_tile_provider.use_cache:
            # download all tiles images
            print ("downloading tiles ... ")
            num_tiles = self.num_tiles[0] * self.num_tiles[1]
            counter = 1
            for y in range(self.corner_tl_tile[1], self.corner_br_tile[1], 1):
                download_threads = []
                for x in range(self.corner_tl_tile[0], self.corner_br_tile[0], 1):
                    if counter % 20 == 0:
                        print ("   tile " + str(counter) + " of " + str(num_tiles))
                    counter = counter + 1

                    # create tile folder
                    self.map_tile_provider.make_tiles_dir(self.zoom, y)
                    # get tile images (multi-threaded)
                    current_thread = threading.Thread(target=self.map_tile_provider.download_tile, args=(self.zoom, x, y, True, ))
                    download_threads.append(current_thread)
                    current_thread.start()

                # wait for all threads to finish
                for t in download_threads:
                    t.join()

    def draw(self):
        # draw all tile images
        print ("drawing tiles ... ")
        num_tiles = self.num_tiles[0] * self.num_tiles[1]
        counter = 1
        for y in range(self.corner_tl_tile[1], self.corner_br_tile[1], 1):
            for x in range(self.corner_tl_tile[0], self.corner_br_tile[0], 1):
                if counter % 20 == 0:
                    print ("   tile " + str(counter) + " of " + str(num_tiles))
                counter = counter + 1

                # load tile image
                tile_image = self.map_tile_provider.load_tile(self.zoom, x, y)
                if tile_image is None:
                    print("   tile does not exist: zoom=" + str(self.zoom) + ", tile_x=" + str(x) + ", tile_y=" + str(y)) 
                else:
                    # insert tile image into output image
                    subimage_x = (x - self.corner_tl_tile[0]) * Map.tile_size_px[0]
                    subimage_y = (y - self.corner_tl_tile[1]) * Map.tile_size_px[1]
                    self.image_raw.paste(tile_image,(subimage_x, subimage_y))
                    tile_image.close()

    def crop_to_coords(self):
        # crop image to tl and br region
        self.image_raw = self.image_raw.crop((self.corner_tl_px_x, self.corner_tl_px_y, self.corner_br_px_x, self.corner_br_px_y))
        self.raw_size_px = self.image_raw.size
        self.corner_tl_px_x = 0
        self.corner_tl_px_y = 0
        self.corner_br_px_x = self.raw_size_px[0] - 1
        self.corner_br_px_y = self.raw_size_px[1] - 1

    def get_cropped_size(self):
        # return size of cropped map
        return (self.corner_br_px_x - self.corner_tl_px_x, self.corner_br_px_y - self.corner_tl_px_y)

    def stylize(self):
        if self.style.boost_contrast:
            scale = 12.0
            self.image_raw = self.image_raw.point(lambda i: 255.0 - ((255.0 - i) * scale))

        self.image_raw = ImageOps.colorize(self.image_raw.convert('L'), black=self.style.background, white=self.style.foreground)

    def draw_marker(self, coords):
        if self.style.marker_style == "none":
            return

        # compute global xy location on tiles and pixel location
        location_xy = degToXY(coords[0], coords[1], self.zoom)
        location_px = (location_xy[0] - self.corner_tl_tile[0] * self.tile_size_px[0], location_xy[1] - self.corner_tl_tile[1] * self.tile_size_px[1])

        # calculate marker size in px
        map_scale_x = (self.corner_br_px_x - self.corner_tl_px_x) / self.size_px[0]
        map_scale_y = (self.corner_br_px_y - self.corner_tl_px_y) / self.size_px[1]
        marker_size_px = mm_to_pixels_tuple(self.style.marker_size_mm, self.dpi)
        marker_size_px = (int(marker_size_px[0] * map_scale_x), int(marker_size_px[1] * map_scale_y))

        if self.style.marker_style == "heart":
            draw_heart_svg(self.image_raw, location_px, marker_size_px[0], self.style.marker_opacity)
        else:
            draw_circle(self.image_raw, location_px, marker_size_px[0] / 2, (128, 0, 0, 128), (255, 0, 0, 255))

    def get_scaled(self):
        # return resized map (Image.BICUBIC, Image.ANTIALIAS or better Image.LANCZOS?)
        return self.image_raw.resize(self.size_px, resample=Image.LANCZOS)

    def __str__(self):
        output = str(__class__.__name__) + ":"
        output += os.linesep + "   size raw: " + str(self.raw_size_px) + " px"
        output += os.linesep + "   size cropped: " + str(self.get_cropped_size()) + " px"
        output += os.linesep + "   tiles grid: " + str(self.num_tiles) + " x " + str(Map.tile_size_px) + " px"
        output += os.linesep + "   size on canvas: " + str(self.size_px) + " px"
        return output
