import sys
import argparse
import json

# --------------------------------------------------------------------
# parse command line arguments
def parse_args():
    # create parser
    parser = argparse.ArgumentParser(description='MapPosterizer')
    parser.add_argument("-l", "--location", type=argparse.FileType('r'), help="location json file", default="location.json")
    parser.add_argument("-o", "--output", type=str, help="output png file", default="map.png")
    parser.add_argument("-d", "--dpi", type=int, help="dpi", default=300)
    parser.add_argument("-c", "--canvas_style", type=argparse.FileType('r'), help="canvas style json file", default="resources/canvas_style_light.json")
    parser.add_argument("-m", "--map_style", type=argparse.FileType('r'), help="map style json file", default="resources/map_style_dark.json")
    parser.add_argument("-s", "--show", help="show generated map", action="store_true")

    # parse command line arguments
    try:
        args = parser.parse_args()
    except:
        parser.print_usage()
        return None

    # validate resolution and output filename
    if args.dpi < 50 or args.dpi > 600:
        print("invalid dpi!")
        return None
    if args.output is None or args.output == "":
        print("invalid output filename!")
        return None

    return args

# --------------------------------------------------------------------
# main pipeline
def main():
    from map_posterizer import canvas, map

    # parse command line arguments
    args = parse_args()
    if args is None:
        sys.exit(1)

    # canvas and map styles
    canvas_style = canvas.CanvasStyle(json.load(args.canvas_style))
    map_style = map.MapStyle(json.load(args.map_style))
    if canvas_style is None or map_style is None:
        print("invalid style files!")
        sys.exit(3)

    # map location
    with args.location as location_file:
        location = map.MapLocation(json.load(location_file))
    if location is None or location.top_left is None or \
       location.bottom_right is None or location.zoom is None:
        print("invalid map location (coordinates and/or zoom)!")
        sys.exit(2)
    print(location)

    # create canvas
    canvas = canvas.Canvas(canvas_style, args.dpi)
    print(canvas)
    # create map
    map = map.Map(map_style, canvas.content_size_mm[0], args.dpi, location.top_left, location.bottom_right, location.zoom)
    print(map)

    # download all tile images
    map.download_tiles()
    # draw map
    map.draw()
    # apply image style
    map.stylize()
    # draw location marker
    if not location.marker is None and not location.hide_marker:
        map.draw_marker(location.marker)
    # crop image to tl and br region
    map.crop_to_coords()

    # draw map onto canvas
    canvas.draw_map(map.get_scaled())
    # draw text box onto canvas
    if not location.caption1 == "":
        canvas.draw_text_box(location.caption1, location.caption2, location.caption3, location.caption4, location.get_marker_coords())

    # save output canvas
    canvas.save(args.output, show=args.show)
    print("poster map saved to " + args.output)

# --------------------------------------------------------------------
# main function
if __name__ == "__main__":
    main()
