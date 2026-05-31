import pysrt
from pysrt import SubRipItem, SubRipTime


def _secunde_in_subriptime(secunde_totale: float) -> SubRipTime:
    """
    Funcție de utilitate internă.
    Convertește timpul din format float (secunde) în formatul specific SubRipTime
    necesar pentru fișierele .srt (ore, minute, secunde, milisecunde).
    """
    ore = int(secunde_totale // 3600)
    minute = int((secunde_totale % 3600) // 60)
    secunde = int(secunde_totale % 60)
    milisecunde = int(round((secunde_totale - int(secunde_totale)) * 1000))
    return SubRipTime(hours=ore, minutes=minute, seconds=secunde, milliseconds=milisecunde)


def genereaza_srt_proiect(date_scene: list, fisier_iesire: str, cuvinte_per_chunk: int = 7) -> str:
    """
    Generează un fișier de subtitrare .srt dinamic, sincronizat cu durata fiecărei scene.

    Parametri:
    - date_scene: o listă de dicționare de forma [{'text': 'Narațiunea...', 'durata': 5.4}, ...]
    - fisier_iesire: calea unde va fi salvat fișierul .srt
    - cuvinte_per_chunk: câte cuvinte să fie afișate simultan pe ecran (default: 7, optim pentru readability)

    Returnează:
    - Calea către fișierul .srt generat.
    """
    subs = pysrt.SubRipFile()
    timp_curent_secunde = 0.0
    index_subtitrare = 1

    for scena in date_scene:
        text = scena['text'].strip()
        durata_totala_scena = scena['durata']

        cuvinte = text.split()
        nr_total_cuvinte = len(cuvinte)

        if nr_total_cuvinte == 0:
            timp_curent_secunde += durata_totala_scena
            continue

        durata_per_cuvant = durata_totala_scena / nr_total_cuvinte

        for i in range(0, nr_total_cuvinte, cuvinte_per_chunk):
            chunk_cuvinte = cuvinte[i:i + cuvinte_per_chunk]
            text_chunk = " ".join(chunk_cuvinte)

            durata_chunk = len(chunk_cuvinte) * durata_per_cuvant

            timp_inceput = _secunde_in_subriptime(timp_curent_secunde)
            timp_curent_secunde += durata_chunk
            timp_sfarsit = _secunde_in_subriptime(timp_curent_secunde)

            item = SubRipItem(
                index=index_subtitrare,
                start=timp_inceput,
                end=timp_sfarsit,
                text=text_chunk
            )
            subs.append(item)
            index_subtitrare += 1

    subs.save(fisier_iesire, encoding='utf-8')
    return fisier_iesire