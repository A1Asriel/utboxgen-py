import os
from io import BytesIO
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont


class BaseTextboxTemplate:
    def __init__(
        self,
        base_image: Union[Image.Image, bytes, str],
        font: Union[ImageFont.FreeTypeFont, bytes, str],
        text_color: Tuple[int, int, int] = (0, 0, 0),
        text_offset: Tuple[int, int] = (0, 0),
        sprite: Optional[Union[Image.Image, bytes, str]] = None,
        sprite_offset: Tuple[int, int] = (0, 0),
        scale: int = 1,
    ):
        self.base_image = self._get_base_image(base_image)
        self.font = self._get_font(font)
        self.text_color = text_color
        self.text_offset = text_offset
        self.sprite = self._get_sprite(sprite)
        self.sprite_offset = sprite_offset
        self.scale = scale

    @staticmethod
    def _bound_text(text: str, width: int, prefix: Optional[str] = None):
        def recurse(line: str):
            out = ""
            line = prefix + line.strip() if prefix is not None else line.strip()
            length = len(line)
            if length <= width:
                out += line + "\n"
                return out
            words = line.split(" ")
            next_line = ""
            while length > width and len(words) > (1 + bool(prefix)):
                word = words.pop()
                length -= len(word) + 1
                next_line = word + " " + next_line
            out += " ".join(words) + "\n" + recurse(next_line)
            return out

        lines = text.split("\n")
        out = ""
        for line in lines:
            out += recurse(line)
        out = out.strip()
        if prefix is not None:
            out = "\n".join(
                " "*len(prefix) + line if not line.startswith(prefix) else line
                for line in out.split("\n")
            )
        return out

    def _get_base_image(self, base_image: Union[Image.Image, bytes, str]) -> Optional[Image.Image]:
        if isinstance(base_image, Image.Image):
            return base_image
        if isinstance(base_image, str):
            try:
                return Image.open(base_image)
            except OSError:
                return None
        elif isinstance(base_image, bytes):
            try:
                return Image.open(BytesIO(base_image))
            except OSError:
                return None
        else:
            return None

    def set_base_image(self, base_image: Union[Image.Image, bytes, str]) -> bool:
        img = self._get_base_image(base_image)
        if img is None:
            return False
        self.base_image = img
        return True

    def _get_font(self, font: Union[ImageFont.FreeTypeFont, bytes, str], size: int = 10) -> Optional[ImageFont.FreeTypeFont]:
        if isinstance(font, ImageFont.FreeTypeFont):
            return font
        if isinstance(font, str):
            try:
                return ImageFont.truetype(font, size)
            except OSError:
                return None
        if isinstance(font, bytes):
            try:
                return ImageFont.truetype(BytesIO(font))
            except OSError:
                return None
        return None

    def set_font(self, font: Union[ImageFont.FreeTypeFont, bytes, str]) -> bool:
        fnt = self._get_font(font)
        if fnt is None:
            return False
        self.font = fnt
        return True

    def _get_sprite(self, sprite: Union[Image.Image, bytes, str]) -> Optional[Image.Image]:
        if isinstance(sprite, Image.Image):
            return sprite
        if isinstance(sprite, str):
            try:
                return Image.open(sprite)
            except OSError:
                return None
        if isinstance(sprite, bytes):
            try:
                return Image.open(BytesIO(sprite))
            except OSError:
                return None
        return None

    def set_sprite(self, sprite: Union[Image.Image, bytes, str]) -> bool:
        spr = self._get_sprite(sprite)
        if spr is None:
            return False
        self.sprite = spr
        return True

    def generate(
        self,
        text: str,
        prefix: Optional[str] = None,
    ):
        scale = min(3, max(1, round(self.scale)))

        base = self.base_image.copy()
        d = ImageDraw.Draw(base)
        d.fontmode = "1"

        if self.sprite is not None:
            base.alpha_composite(self.sprite, self.sprite_offset)
        text = self._bound_text(text, 31 - 7 * bool(self.sprite), prefix)
        pos = (self.text_offset[0] + 58 * bool(self.sprite), self.text_offset[1])

        d.multiline_text(pos, text, font=self.font, fill=self.text_color, spacing=5)
        # d.rectangle((3, 3, 285, 72), None, (0, 0, 0))  # TODO: automate the mask somehow

        base = base.resize(
            (base.size[0] * scale, base.size[1] * scale), Image.Resampling.NEAREST
        )
        return base


class UTTextboxTemplate(BaseTextboxTemplate):
    def __init__(
        self,
        text_color: Tuple[int, int, int] = (255, 255, 255),
        sprite: Optional[bytes] = None,
        scale: int = 2,
    ):
        base_path = os.path.join(os.path.dirname(__file__), "assets", "utbox_base.png")
        font_path = os.path.join(os.path.dirname(__file__), "assets", "utbox_font_cyr.otf")
        font = self._get_font(font_path, 16)
        font.size = 16

        super().__init__(
            base_image=base_path,
            font=font,
            text_color=text_color,
            text_offset=(14, 10),
            sprite=sprite,
            sprite_offset=(3, 3),
            scale=scale,
        )


class Textbox(BaseTextboxTemplate):
    def __init__(self, text: str, prefix: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text
        self.prefix = prefix

    @classmethod
    def from_textbox(cls, textbox: BaseTextboxTemplate, text: str, prefix: Optional[str] = None):
        return cls(
            text=text,
            prefix=prefix,
            base_image=textbox.base_image,
            font=textbox.font,
            text_color=textbox.text_color,
            text_offset=textbox.text_offset,
            sprite=textbox.sprite,
            sprite_offset=textbox.sprite_offset,
            scale=textbox.scale,
        )

    def generate(self):
        return super().generate(self.text, self.prefix)


def generate_multi(textboxes: List[Textbox], margin: bool = False):
    if not textboxes:
        return None
    base_scale = textboxes[0].scale
    # base_scale = 1  # To prevent huge images
    true_height = sum([t.base_image.size[1] for t in textboxes])
    true_width = max([t.base_image.size[0] for t in textboxes])
    img = Image.new("RGBA", (true_width + 6*margin, true_height + 6*len(textboxes)*margin), (0, 0, 0, 255*margin))
    cur_y_offset = 3*margin
    for textbox in textboxes:
        textbox.scale = 1
        textbox_img = textbox.generate()
        img.paste(textbox_img, (3*margin, cur_y_offset))
        # img.paste(textbox_img)
        cur_y_offset += textbox_img.size[1] + 6*margin

    img = img.resize((img.size[0] * base_scale, img.size[1] * base_scale), Image.Resampling.NEAREST)
    return img