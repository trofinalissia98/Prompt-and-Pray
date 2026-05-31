import streamlit as st
import os
import sys
import concurrent.futures
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from moviepy.editor import concatenate_videoclips


st.set_page_config(
    page_title="AI Video Explainer",
    page_icon="🎬",
    layout="centered"
)

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "src")))

try:
    from schemas import ScriptVideo
    from video_processing import proceseaza_scena_individuala
except ImportError as e:
    st.error(
        f"Eroare la importul modulelor interne: {e}. "
        "Asigură-te că rulezi app.py din rădăcina proiectului."
    )
    st.stop()


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    max_retries=2
)

os.makedirs("data/outputs/audio", exist_ok=True)
os.makedirs("data/outputs/subtitles", exist_ok=True)
os.makedirs("data/outputs/video", exist_ok=True)
os.makedirs("data/outputs/images", exist_ok=True)

st.title("AI Text-to-Video Explainer")
st.markdown(
    "Transformă documentația de produs sau lecțiile educaționale în videoclipuri "
    "scurte generate autonom de AI."
)

nume_proiect = st.text_input("Numele Proiectului", value="Proiect_Demo")

text_brut = st.text_area(
    "Introdu textul sursă (aprox. 150 - 400 cuvinte):",
    height=200,
    placeholder="Ex: Noul modul EcoTrack..."
)

foloseste_imagini = st.checkbox(
    "Folosește imagini generate cu Azure OpenAI",
    value=False,
    help=(
        "Dacă este activ, emoji-urile vor fi înlocuite cu imagini generate. "
        "Dacă imaginea nu se poate genera, se folosește fallback pe emoji."
    )
)


def extrage_lista_scene(script: ScriptVideo):
    """
    Extrage lista de scene indiferent dacă schema folosește câmpul 'scene' sau 'scenes'.
    """
    if hasattr(script, "scene"):
        return script.scene

    if hasattr(script, "scenes"):
        return script.scenes

    raise ValueError(
        "Obiectul ScriptVideo nu conține nici câmpul 'scene', nici câmpul 'scenes'. "
        "Verifică schema din src/schemas.py."
    )


if st.button("🚀 Generează Videoclipul", type="primary"):
    if not text_brut.strip():
        st.warning("Te rog să introduci un text înainte de a continua.")
    else:
        with st.status("Agentul AI procesează cererea...", expanded=True) as status:
            try:
                nume_proiect_curat = nume_proiect.strip().replace(" ", "_")

                if not nume_proiect_curat:
                    nume_proiect_curat = "Proiect_Demo"

                st.write("Pasul 1: Se analizează textul și se extrage structura narativă...")

                prompt_template = ChatPromptTemplate.from_template(
                    """
Ești un producător video expert. Transformă textul de mai jos într-un script video structurat.

Împarte conținutul în 5-8 scene logice.

Pentru fiecare scenă generează:
- numar_scena
- naratiune: text complet pentru voice-over
- text_ecran: o formulare foarte scurtă a ideii
- emoji_vizual: un singur emoji relevant, folosit ca fallback vizual
- culoare_fundal: listă RGB cu 3 valori numerice pentru un fundal închis
- prompt_imagine: un prompt în limba engleză pentru o imagine reprezentativă pentru scenă

Reguli pentru prompt_imagine:
- să descrie clar conținutul vizual al scenei
- stil modern, profesional, potrivit pentru explainer video
- fără text în imagine
- fără logo-uri
- fără watermark

Textul utilizatorului:
{text_brut}
"""
                )

                structured_llm = llm.with_structured_output(ScriptVideo)
                chain = prompt_template | structured_llm

                script = chain.invoke({"text_brut": text_brut})
                lista_scene = extrage_lista_scene(script)
                nr_scene = len(lista_scene)

                if nr_scene == 0:
                    raise RuntimeError(
                        "LLM-ul nu a generat nicio scenă. Încearcă un text mai clar sau verifică schema ScriptVideo."
                    )

                st.write(f"Structură creată: **{nr_scene} scene logice** identificate.")

                st.write(
                    "Pasul 2: Se generează media asincron: audio, subtitrări, "
                    "imagini opționale și video..."
                )

                rezultate_nesortate = []
                progress_bar = st.progress(0)


                max_workers = min(2, nr_scene) if foloseste_imagini else nr_scene

                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [
                        executor.submit(
                            proceseaza_scena_individuala,
                            scena,
                            nume_proiect_curat,
                            foloseste_imagini
                        )
                        for scena in lista_scene
                    ]

                    for i, future in enumerate(concurrent.futures.as_completed(futures)):
                        try:
                            rezultat = future.result()
                            rezultate_nesortate.append(rezultat)
                            progress_bar.progress((i + 1) / nr_scene)
                            st.write(f"Scena {rezultat[0]} procesată cu succes.")
                        except Exception as scene_error:
                            raise RuntimeError(
                                f"Eroare la procesarea unei scene: {scene_error}"
                            )

                st.write("🎞️ Pasul 3: Se randează clipul final...")

                if not rezultate_nesortate:
                    raise RuntimeError(
                        "Nu s-a generat niciun clip de scenă. "
                        "Verifică funcția proceseaza_scena_individuala."
                    )

                rezultate_sortate = sorted(rezultate_nesortate, key=lambda x: x[0])
                clipuri_scene = [rez[1] for rez in rezultate_sortate]

                if not clipuri_scene:
                    raise RuntimeError(
                        "Lista de clipuri este goală. Nu se poate concatena videoclipul final."
                    )

                cale_output_final = f"data/outputs/video/{nume_proiect_curat}_final.mp4"

                video_final = concatenate_videoclips(clipuri_scene)

                video_final.write_videofile(
                    cale_output_final,
                    fps=24,
                    codec="libx264",
                    audio_codec="aac",
                    verbose=False,
                    logger=None
                )


                video_final.close()
                for clip in clipuri_scene:
                    clip.close()

                status.update(
                    label="Proces finalizat cu succes!",
                    state="complete",
                    expanded=False
                )

                st.balloons()
                st.success(f"Videoclipul **{nume_proiect_curat}** a fost generat!")
                st.video(cale_output_final)

            except Exception as e:
                status.update(
                    label="A apărut o eroare!",
                    state="error",
                    expanded=True
                )
                st.error(f"Detalii eroare: {e}")