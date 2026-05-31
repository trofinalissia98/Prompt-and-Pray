import os
import textwrap
import numpy as np
import pysrt
from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont, ImageOps


# --- 1. GENERARE CADRE (PILLOW) ---
def _creeaza_cadru_fundal(
    latime: int,
    inaltime: int,
    emoji_vizual: str,
    culoare_fundal: list,
    imagine_path: str = None
) -> np.ndarray:
    """
    Creează fundalul scenei.
    Dacă există imagine_path valid, folosește imaginea.
    Altfel, folosește fundalul clasic cu emoji.
    """

    # Varianta nouă: imagine generată
    if imagine_path and os.path.exists(imagine_path):
        img = Image.open(imagine_path).convert("RGB")

        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.LANCZOS

        img = ImageOps.fit(
            img,
            (latime, inaltime),
            method=resample,
            centering=(0.5, 0.5)
        )

        # overlay discret pentru lizibilitate
        overlay = Image.new("RGB", (latime, inaltime), (0, 0, 0))
        img = Image.blend(img, overlay, alpha=0.22)

        return np.array(img)

    # Varianta veche: fundal + emoji
    culoare_rgb = tuple(culoare_fundal)

    img = Image.new("RGB", (latime, inaltime), color=culoare_rgb)
    draw = ImageDraw.Draw(img)

    try:
        font_mare = ImageFont.truetype("seguiemj.ttf", 250)
    except IOError:
        try:
            font_mare = ImageFont.truetype("Apple Color Emoji.ttc", 250)
        except IOError:
            font_mare = ImageFont.load_default()

    try:
        bbox = draw.textbbox((0, 0), emoji_vizual, font=font_mare)
        w_text = bbox[2] - bbox[0]
        h_text = bbox[3] - bbox[1]
    except AttributeError:
        w_text = draw.textlength(emoji_vizual, font=font_mare)
        h_text = 250

    x_text = (latime - w_text) / 2
    y_text = (inaltime - h_text) / 2 - 50

    try:
        draw.text(
            (x_text, y_text),
            emoji_vizual,
            font=font_mare,
            embedded_color=True,
            fill=(255, 255, 255)
        )
    except TypeError:
        draw.text(
            (x_text, y_text),
            emoji_vizual,
            font=font_mare,
            fill=(255, 255, 255)
        )

    return np.array(img)

def _creeaza_cadru_subtitrare(text: str, latime: int, inaltime: int) -> np.ndarray:
    """Creează un cadru transparent (RGBA) care conține doar textul subtitrării."""
    img = Image.new('RGBA', (latime, inaltime), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font_sub = ImageFont.truetype("arial.ttf", 45)
    except IOError:
        font_sub = ImageFont.load_default()

    linii_text = textwrap.wrap(text, width=40)
    inaltime_linie = 60

    y_text = inaltime - (len(linii_text) * inaltime_linie) - 80

    for linie in linii_text:
        try:
            bbox = draw.textbbox((0, 0), linie, font=font_sub)
            lungime_linie = bbox[2] - bbox[0]
        except AttributeError:
            lungime_linie = draw.textlength(linie, font=font_sub)

        x_text = (latime - lungime_linie) / 2

        pozitii_contur = [(-2, -2), (2, -2), (-2, 2), (2, 2)]
        for offset_x, offset_y in pozitii_contur:
            draw.text((x_text + offset_x, y_text + offset_y), linie, font=font_sub, fill=(0, 0, 0, 255))

        draw.text((x_text, y_text), linie, font=font_sub, fill=(255, 255, 255, 255))
        y_text += inaltime_linie

    return np.array(img)


# --- 2. ORCHESTRAREA CLIPULUI SCENEI ---

def creeaza_clip_scena(
    audio_path,
    srt_path,
    emoji_vizual,
    culoare_fundal,
    imagine_path=None,
    latime=1280,
    inaltime=720
):
    """
    Combină audio-ul generat, fundalul vizual dinamic și subtitrările (SRT).
    """
    audio_clip = AudioFileClip(audio_path)
    durata_scena = audio_clip.duration

    cadru_fundal_np = _creeaza_cadru_fundal(
        latime=latime,
        inaltime=inaltime,
        emoji_vizual=emoji_vizual,
        culoare_fundal=culoare_fundal,
        imagine_path=imagine_path
    )
    clip_fundal = ImageClip(cadru_fundal_np).set_duration(durata_scena)

    clipuri_suprapuse = [clip_fundal]

    if os.path.exists(srt_path):
        subtitrari = pysrt.open(srt_path, encoding='utf-8')
        for sub in subtitrari:
            start_sec = sub.start.ordinal / 1000.0
            end_sec = sub.end.ordinal / 1000.0

            if start_sec >= durata_scena:
                continue
            end_sec = min(end_sec, durata_scena)
            durata_subtitrare = end_sec - start_sec

            if durata_subtitrare > 0:
                cadru_sub_np = _creeaza_cadru_subtitrare(sub.text, latime, inaltime)
                clip_subtitrare = (ImageClip(cadru_sub_np)
                                   .set_duration(durata_subtitrare)
                                   .set_start(start_sec))
                clipuri_suprapuse.append(clip_subtitrare)

    video_final = CompositeVideoClip(clipuri_suprapuse, size=(latime, inaltime))
    video_final = video_final.set_audio(audio_clip)

    return video_final