from typing import Optional, Union
from PIL import Image, ImageDraw, ImageFont


def _bound_text(text: str, width: int, asterisk: bool = False):
    def recurse(line: str, asterisk: bool = False):
        out = ""
        line = "* " + line.strip() if asterisk else line.strip()
        length = len(line)
        if length <= width:
            out += line + "\n"
            return out
        words = line.split(" ")
        next_line = ""
        while length > width and len(words) > (1 + asterisk):
            word = words.pop()
            length -= len(word) + 1
            next_line = word + " " + next_line
        out += " ".join(words) + "\n" + recurse(next_line)
        return out
        
    lines = text.split("\n")
    out = ""
    for line in lines:
        out += recurse(line, asterisk)
    out = out.strip()
    if asterisk:
        out = "\n".join("  " + line if not line.startswith("* ") else line for line in out.split("\n"))
    return out

def generate(text: str, asterisk: bool = False, scale: int = 2, image: Optional[Union[bytes, str]] = None):
    scale = min(3, max(1, round(scale)))
    
    base = Image.open("src/utboxgen_py_A1Asriel/assets/utbox_base.png")
    fnt = ImageFont.FreeTypeFont("src/utboxgen_py_A1Asriel/assets/utbox_font_cyr.otf", 16)
    d = ImageDraw.Draw(base)

    if isinstance(image, str):
        char = Image.open(image)
        base.alpha_composite(char, (3, 3))
    text = _bound_text(text, 34 - 2*asterisk - 8*bool(char), asterisk)
    pos = (14 + 58*bool(char), 10)

    d.multiline_text(pos, text, font=fnt, fill=(255, 255, 255), spacing=5)
    d.rectangle((3, 3, 285, 72), None, (0, 0, 0))
    
    base = base.resize((base.size[0] * scale, base.size[1] * scale), Image.Resampling.NEAREST)
    base.show()