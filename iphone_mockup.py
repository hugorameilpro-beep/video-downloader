"""Génération d'un cadre d'iPhone (PNG transparent) et incrustation vidéo via ffmpeg."""

from __future__ import annotations

import io
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

# Finitions du châssis : dégradé métallique (de gauche à droite) + couleur des boutons.
FINISHES: dict[str, dict] = {
    "Argent": {
        "stops": ["#9a9da3", "#f4f5f7", "#c9ccd1", "#e6e8eb", "#c9ccd1", "#f4f5f7", "#9a9da3"],
        "buttons": "#a6aab0",
    },
    "Or": {
        "stops": ["#a8824a", "#fbe9c6", "#d6b27a", "#f0d9ac", "#d6b27a", "#fbe9c6", "#a8824a"],
        "buttons": "#c9a467",
    },
    "Graphite": {
        "stops": ["#2b2c30", "#7d7f85", "#45474c", "#5d5f64", "#45474c", "#7d7f85", "#2b2c30"],
        "buttons": "#4a4c51",
    },
    "Titane bleu": {
        "stops": ["#2f3a4a", "#8f9fb5", "#4d5d73", "#6b7c93", "#4d5d73", "#8f9fb5", "#2f3a4a"],
        "buttons": "#56667d",
    },
}

QUALITIES = {"Standard (720p)": 720, "Haute (1080p)": 1080}

SUPERSAMPLE = 2  # Dessin en 2x puis réduction → bords anti-crénelés.


@dataclass(frozen=True)
class FrameGeometry:
    width: int
    height: int
    screen_x: int
    screen_y: int
    screen_w: int
    screen_h: int


def _even(value: float) -> int:
    return int(round(value / 2)) * 2


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _metal_gradient(width: int, height: int, stops: list[str]) -> Image.Image:
    """Dégradé horizontal multi-points imitant un châssis métallique poli."""
    positions = np.linspace(0, 1, len(stops))
    xs = np.linspace(0, 1, width)
    colors = np.array([_hex_to_rgb(c) for c in stops], dtype=np.float32)
    row = np.stack([np.interp(xs, positions, colors[:, c]) for c in range(3)], axis=-1)
    # Léger assombrissement vertical pour donner du volume.
    shade = np.linspace(1.04, 0.92, height, dtype=np.float32)[:, None, None]
    img = np.clip(row[None, :, :] * shade, 0, 255).astype(np.uint8)
    return Image.fromarray(img, "RGB").convert("RGBA")


def build_iphone_frame(screen_width: int = 720, finish: str = "Argent", landscape: bool = False
                       ) -> tuple[Image.Image, FrameGeometry]:
    """Dessine un iPhone à encoche dont l'écran est entièrement transparent (alpha = 0)."""
    spec = FINISHES[finish]
    s = SUPERSAMPLE

    sw = _even(screen_width)
    sh = _even(sw * 19.5 / 9)                     # Ratio d'écran d'un iPhone moderne.
    bezel = _even(sw * 0.036)                     # Bordure noire autour de l'écran.
    band = _even(sw * 0.022)                      # Bande métallique du châssis.
    margin = _even(sw * 0.09)                     # Espace pour les boutons et l'ombre.
    phone_w, phone_h = sw + 2 * (bezel + band), sh + 2 * (bezel + band)
    W, H = phone_w + 2 * margin, phone_h + 2 * margin
    sx, sy = margin + band + bezel, margin + band + bezel

    r_screen = sw * 0.121
    r_bezel = r_screen + bezel
    r_body = r_bezel + band

    def box(x, y, w, h):
        return [x * s, y * s, (x + w) * s - 1, (y + h) * s - 1]

    canvas = Image.new("RGBA", (W * s, H * s), (0, 0, 0, 0))

    # Boutons latéraux (dessinés avant le châssis, qui les recouvre en partie).
    draw = ImageDraw.Draw(canvas)
    knob = band * 0.75
    btn_color = spec["buttons"]
    left_x, right_x = margin - knob, margin + phone_w - band
    for top, length in ((0.165, 0.035), (0.235, 0.065), (0.315, 0.065)):
        draw.rounded_rectangle(box(left_x, margin + phone_h * top, knob + band, phone_h * length),
                               radius=knob * s * 0.6, fill=btn_color)
    draw.rounded_rectangle(box(right_x, margin + phone_h * 0.25, knob + band, phone_h * 0.1),
                           radius=knob * s * 0.6, fill=btn_color)

    # Châssis métallique.
    body_mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(body_mask).rounded_rectangle(box(margin, margin, phone_w, phone_h),
                                                radius=r_body * s, fill=255)
    body = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    body.paste(_metal_gradient(phone_w * s, phone_h * s, spec["stops"]), (margin * s, margin * s))
    body.putalpha(body_mask)
    canvas.alpha_composite(body)

    draw = ImageDraw.Draw(canvas)
    # Liseré lumineux sur l'arête extérieure.
    draw.rounded_rectangle(box(margin, margin, phone_w, phone_h), radius=r_body * s,
                           outline=(255, 255, 255, 110), width=max(2, int(sw * 0.003 * s)))
    # Bordure noire de l'écran (verre).
    draw.rounded_rectangle(box(margin + band, margin + band, phone_w - 2 * band, phone_h - 2 * band),
                           radius=r_bezel * s, fill=(8, 8, 10, 255))
    draw.rounded_rectangle(box(margin + band, margin + band, phone_w - 2 * band, phone_h - 2 * band),
                           radius=r_bezel * s, outline=(0, 0, 0, 255), width=max(2, int(sw * 0.002 * s)))

    # Encoche : rectangle arrondi en bas + petits congés concaves de part et d'autre.
    notch_w, notch_h = sw * 0.42, sw * 0.082
    notch_r, ear = sw * 0.05, sw * 0.022
    nx0 = sx + (sw - notch_w) / 2
    nx1 = nx0 + notch_w
    notch_mask = Image.new("L", canvas.size, 0)
    nd = ImageDraw.Draw(notch_mask)
    nd.rounded_rectangle(box(nx0, sy - notch_r, notch_w, notch_h + notch_r), radius=notch_r * s, fill=255)
    nd.rectangle(box(nx0 - ear, sy, ear + 1, ear), fill=255)
    nd.rectangle(box(nx1 - 1, sy, ear + 1, ear), fill=255)
    nd.ellipse(box(nx0 - 2 * ear, sy, 2 * ear, 2 * ear), fill=0)
    nd.ellipse(box(nx1, sy, 2 * ear, 2 * ear), fill=0)

    # Zone d'écran transparente = écran arrondi moins l'encoche.
    screen_mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(screen_mask).rounded_rectangle(box(sx, sy, sw, sh), radius=r_screen * s, fill=255)
    hole_arr = np.asarray(screen_mask, dtype=np.float32) * (1 - np.asarray(notch_mask, dtype=np.float32) / 255)
    hole = Image.fromarray(np.clip(hole_arr, 0, 255).astype(np.uint8), "L")
    canvas.putalpha(ImageChops.multiply(canvas.getchannel("A"), ImageChops.invert(hole)))

    # Haut-parleur et caméra dans l'encoche.
    draw = ImageDraw.Draw(canvas)
    cy = sy + notch_h * 0.42
    spk_w, spk_h = sw * 0.13, sw * 0.013
    draw.rounded_rectangle(box(sx + (sw - spk_w) / 2, cy - spk_h / 2, spk_w, spk_h),
                           radius=spk_h * s / 2, fill=(38, 38, 42, 255))
    cam_r = sw * 0.02
    cam_x = sx + sw / 2 + notch_w * 0.27
    draw.ellipse(box(cam_x - cam_r, cy - cam_r, 2 * cam_r, 2 * cam_r), fill=(22, 24, 34, 255))
    draw.ellipse(box(cam_x - cam_r * 0.5, cy - cam_r * 0.5, cam_r, cam_r), fill=(32, 48, 92, 255))
    draw.ellipse(box(cam_x - cam_r * 0.15, cy - cam_r * 0.45, cam_r * 0.3, cam_r * 0.3),
                 fill=(150, 170, 220, 200))

    frame = canvas.resize((W, H), Image.LANCZOS)
    hole = hole.resize((W, H), Image.LANCZOS)
    geometry = FrameGeometry(W, H, sx, sy, sw, sh)

    if landscape:
        # Rotation de 90° (encoche à gauche) ; les marges étant symétriques, on permute les axes.
        frame = frame.transpose(Image.Transpose.ROTATE_90)
        hole = hole.transpose(Image.Transpose.ROTATE_90)
        geometry = FrameGeometry(H, W, sy, sx, sh, sw)

    # Ombre portée douce, toujours vers le bas (calculée après rotation).
    silhouette = ImageChops.lighter(frame.getchannel("A"), hole)
    shadow_alpha = ImageChops.offset(silhouette, 0, int(sw * 0.018)).point(lambda v: v * 150 // 255)
    shadow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    shadow.putalpha(shadow_alpha.filter(ImageFilter.GaussianBlur(sw * 0.03)))
    shadow.alpha_composite(frame)
    # L'écran reste parfaitement transparent (aucune ombre derrière la vidéo).
    shadow.putalpha(ImageChops.multiply(shadow.getchannel("A"), ImageChops.invert(hole)))
    return shadow, geometry


def frame_png_bytes(frame: Image.Image) -> bytes:
    buf = io.BytesIO()
    frame.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _filter_graph(geo: FrameGeometry, fit: str, background: str, for_video: bool) -> str:
    bg = "0x" + background.lstrip("#")
    w, h = geo.screen_w, geo.screen_h
    if fit == "fill":
        # Remplir l'écran : on agrandit puis on rogne l'excédent.
        screen = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
    else:
        # Ajuster : la vidéo entière est visible, bandes noires si besoin.
        screen = (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                  f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=black")
    graph = (f"[0:v]{screen},setsar=1,pad={geo.width}:{geo.height}:{geo.screen_x}:{geo.screen_y}:color={bg}[v];"
             f"[v][1:v]overlay=0:0:shortest=1")
    if for_video:
        graph += ",format=yuv420p"
    return graph + "[out]"


def _run(cmd: list[str], timeout: int) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        lines = [line for line in result.stderr.strip().splitlines() if line.strip()]
        raise RuntimeError(lines[-1] if lines else "ffmpeg a échoué.")


def render_preview(video: Path, frame_png: Path, geo: FrameGeometry, fit: str, background: str,
                   output: Path, at_seconds: float = 1.0) -> Path:
    """Génère une image PNG d'aperçu (une seule image de la vidéo dans le cadre)."""
    base = ["ffmpeg", "-y", "-loglevel", "error"]
    tail = ["-loop", "1", "-i", str(frame_png),
            "-filter_complex", _filter_graph(geo, fit, background, for_video=False),
            "-map", "[out]", "-frames:v", "1", str(output)]
    try:
        _run([*base, "-ss", f"{at_seconds:.2f}", "-i", str(video), *tail], timeout=120)
    except RuntimeError:
        _run([*base, "-i", str(video), *tail], timeout=120)  # Vidéo très courte : première image.
    if not output.exists():
        _run([*base, "-i", str(video), *tail], timeout=120)
    return output


def render_video(video: Path, frame_png: Path, geo: FrameGeometry, fit: str, background: str,
                 output: Path) -> Path:
    """Incruste la vidéo dans l'écran et exporte un MP4 H.264 + AAC compatible PowerPoint."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video),
        "-loop", "1", "-i", str(frame_png),
        "-filter_complex", _filter_graph(geo, fit, background, for_video=True),
        "-map", "[out]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-ac", "2",
        "-movflags", "+faststart",
        str(output),
    ]
    _run(cmd, timeout=3600)
    return output
