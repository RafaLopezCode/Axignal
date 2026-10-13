"""Decode only bounded raster images and discard all original metadata."""

import warnings
from io import BytesIO


class RasterAvatarNormalizer:
    def normalize(self, raw: bytes) -> bytes:
        from PIL import Image, ImageOps, UnidentifiedImageError

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(BytesIO(raw)) as image:
                    if (
                        image.format not in {"PNG", "JPEG", "WEBP"}
                        or getattr(image, "n_frames", 1) != 1
                    ):
                        raise ValueError("unsupported avatar format")
                    if max(image.size) > 2048 or image.width * image.height > 4000000:
                        raise ValueError("avatar dimensions exceed limit")
                    image.load()
                    clean = ImageOps.fit(ImageOps.exif_transpose(image).convert("RGBA"), (128, 128))
                    output = BytesIO()
                    # New pixel buffer strips EXIF, ICC, comments and text chunks.
                    Image.frombytes("RGBA", clean.size, clean.tobytes()).save(output, format="PNG")
                    result = output.getvalue()
                    if len(result) > 131072:
                        raise ValueError("normalized avatar exceeds limit")
                    return result
        except (
            OSError,
            UnidentifiedImageError,
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
        ):
            raise ValueError("invalid avatar") from None
