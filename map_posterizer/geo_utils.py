import math

from geopy.geocoders import Nominatim

# --------------------------------------------------------------------
# useful literature
# - get location name from coordinates
#   https://www.w3resource.com/python-exercises/geopy/python-geopy-nominatim_api-exercise-6.php
# - conversion of zoom levels / tile sizes to real sizes
#   https://wiki.openstreetmap.org/wiki/Zoom_levels

# --------------------------------------------------------------------
# latitude/longitude conversion

def degToTile(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    tile_x = int((lon_deg + 180.0) / 360.0 * n)
    tile_y = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return (tile_x, tile_y)

def degToCornerTiles(corner_tl_deg, corner_br_deg, zoom):
    corner_tl_tile = degToTile(corner_tl_deg[0], corner_tl_deg[1], zoom)
    corner_br_tile = degToTile(corner_br_deg[0], corner_br_deg[1], zoom)
    return (corner_tl_tile, corner_br_tile)

def numTilesFromCorners(corner_tl_tile, corner_br_tile, make_squared):
    num_tiles = (corner_br_tile[0] - corner_tl_tile[0] + 1, corner_br_tile[1] - corner_tl_tile[1] + 1)
    if make_squared:
        num_tiles = (max(num_tiles[0], num_tiles[1]), max(num_tiles[0], num_tiles[1]))
    return num_tiles

def degToXY(lat, lon, zoom):
    C =(256 / (2 * math.pi)) * 2 ** zoom
    x = C * (math.radians(lon) + math.pi)
    y = C * (math.pi - math.log(math.tan((math.pi / 4) + math.radians(lat) / 2)))
    return (x, y)

def degToDMS(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]

def degToDMSformatted(lat_f, lon_f):
    [lat_d, lat_m, lat_sd] = degToDMS(lat_f)
    [lon_d, lon_m, lon_sd] = degToDMS(lon_f)
    postfix_lat = "N" if lat_f >= 0.0 else "S"
    postfix_lon = "E" if lon_f >= 0.0 else "W"
    return (str(abs(lat_d)) + "°" + str(lat_m) + "\'" + str(round(lat_sd, 1)) + "\""+ postfix_lat, str(abs(lon_d)) + "°" + str(lon_m) + "\'" + str(round(lon_sd, 1)) + "\"" + postfix_lon)

# --------------------------------------------------------------------
# location lookups

def geoCoordinatesToPlace(coords):
    # get location name for coordinates (geopy/Nominatim)
    geolocator = Nominatim(user_agent="MapPosterizer")
    location = geolocator.reverse(coords)
    place = ""
    if "address" in location.raw:
        if "city" in location.raw["address"]:
            place = location.raw["address"]["city"]
        if "village" in location.raw["address"]:
            place = location.raw["address"]["village"]
    return place
