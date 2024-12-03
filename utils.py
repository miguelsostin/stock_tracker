# utils.py

def hex_to_rgb(hex_color):
    """
    Converts a hex color string to an RGB list with values between 0 and 1.

    Args:
        hex_color (str): Hex color string (e.g., '#ffffff').

    Returns:
        list: RGB values as floats between 0 and 1.
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError(f"Input '{hex_color}' is not in '#RRGGBB' format.")
    return [int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4)]
