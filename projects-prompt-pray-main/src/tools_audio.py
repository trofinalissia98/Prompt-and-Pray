import edge_tts
import asyncio
import threading


def genereaza_audio_scena(text: str, fisier_iesire: str, voice: str = "ro-RO-EmilNeural") -> str:
    """
    Transformă textul în audio folosind Edge TTS.
    Rulează într-un fir de execuție separat (thread) pentru a rula perfect
    în Jupyter Notebook fără erori de tip Context sau Event Loop.
    """

    # Definim funcția asincronă internă
    async def _generare_asincrona():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(fisier_iesire)

    # O rulăm într-un mediu izolat
    def _ruleaza_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generare_asincrona())
        loop.close()

    # Pornim firul de execuție separat și așteptăm să termine
    thread = threading.Thread(target=_ruleaza_in_thread)
    thread.start()
    thread.join()

    return fisier_iesire