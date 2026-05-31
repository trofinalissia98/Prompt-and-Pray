import base64
import os
from typing import Optional
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

STIL_VIZUAL_GLOBAL = """
Modern explainer video illustration, clean composition, professional cinematic look,
high contrast, visually clear, suitable as a 16:9 background for an explainer video.
No text, no letters, no subtitles, no logos, no watermark.
""".strip()


def genereaza_imagine_scena_azure(prompt_imagine: str, fisier_iesire: str) -> Optional[str]:
    """
    Generează o imagine pentru o scenă folosind Azure OpenAI image generation.
    Returnează calea imaginii dacă merge, altfel None.
    Folosește cache: dacă imaginea există deja, nu o mai regenerează.
    """

    if not prompt_imagine or not prompt_imagine.strip():
        return None

    if os.path.exists(fisier_iesire):
        return fisier_iesire

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_IMAGE_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_IMAGE_API_VERSION", "2025-04-01-preview")
    image_size = os.getenv("AZURE_IMAGE_SIZE", "1536x1024")
    image_quality = os.getenv("AZURE_IMAGE_QUALITY", "medium")

    if not api_key or not endpoint or not deployment:
        print("[WARN] Lipsesc valorile Azure din .env. Se folosește fallback pe emoji.")
        return None

    os.makedirs(os.path.dirname(fisier_iesire), exist_ok=True)

    prompt_final = f"""
{STIL_VIZUAL_GLOBAL}

Scene description:
{prompt_imagine.strip()}
""".strip()

    try:
        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )

        rezultat = client.images.generate(
            model=deployment,
            prompt=prompt_final,
            size=image_size,
            quality=image_quality,
            n=1,
        )

        imagine_base64 = rezultat.data[0].b64_json
        imagine_bytes = base64.b64decode(imagine_base64)

        with open(fisier_iesire, "wb") as f:
            f.write(imagine_bytes)

        return fisier_iesire

    except Exception as e:
        print(f"[WARN] Generarea imaginii a eșuat pentru scena curentă: {e}")
        return None