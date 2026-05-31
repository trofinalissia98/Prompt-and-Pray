from moviepy.editor import AudioFileClip
from tools_audio import genereaza_audio_scena
from tools_text import genereaza_srt_proiect
from tools_video import creeaza_clip_scena
from tools_images_azure import genereaza_imagine_scena_azure


def proceseaza_scena_individuala(scena, nume_proiect, foloseste_imagini=False):
    """
    Procesează o singură scenă apelând uneltele interne pentru audio, text și video.
    Returnează numărul scenei (pentru sortare) și clipul asamblat.
    """
    audio_path = f"data/outputs/audio/{nume_proiect}scena{scena.numar_scena}.mp3"
    srt_path = f"data/outputs/subtitles/{nume_proiect}scena{scena.numar_scena}.srt"

    genereaza_audio_scena(scena.naratiune, audio_path)

    clip_audio_temp = AudioFileClip(audio_path)
    durata_audio = clip_audio_temp.duration
    clip_audio_temp.close()

    date_scena = [{'text': scena.naratiune, 'durata': durata_audio}]
    genereaza_srt_proiect(date_scena, srt_path, cuvinte_per_chunk=6)

    imagine_path = None
    if foloseste_imagini:
        imagine_path = f"data/outputs/images/{nume_proiect}scena{scena.numar_scena}.png"
        imagine_path = genereaza_imagine_scena_azure(
            prompt_imagine=getattr(scena, "prompt_imagine", ""),
            fisier_iesire=imagine_path
        )

    clip = creeaza_clip_scena(
        audio_path=audio_path,
        srt_path=srt_path,
        emoji_vizual=scena.emoji_vizual,
        culoare_fundal=scena.culoare_fundal,
        imagine_path=imagine_path
    )

    return scena.numar_scena, clip