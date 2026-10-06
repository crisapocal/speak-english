# ============================================================
#  RECONHECIMENTO DE VOZ + NOTA DE PRONUNCIA
#  Tenta Whisper (offline, melhor) -> fallback Google (online)
# ============================================================

import threading
import json
import os
import tempfile
from difflib import SequenceMatcher

# ---------- TENTAR IMPORTAR BACKENDS ----------
WHISPER_DISPONIVEL = False
GOOGLE_DISPONIVEL = False

try:
    import speech_recognition as sr
    GOOGLE_DISPONIVEL = True
except ImportError:
    sr = None
    print("AVISO: SpeechRecognition nao instalado. Rode: pip install SpeechRecognition")

try:
    import whisper
    WHISPER_DISPONIVEL = True
except ImportError:
    whisper = None  # opcional


# ============================================================
# CLASSE PRINCIPAL
# ============================================================
class Reconhecedor:
    """Encapsula gravacao + transcricao + comparacao."""

    def __init__(self, idioma="en-US"):
        self.idioma = idioma
        self.whisper_model = None
        self._lock = threading.Lock()
        self._reconhecedor = sr.Recognizer() if sr else None
        if self._reconhecedor:
            self._reconhecedor.energy_threshold = 300
            self._reconhecedor.dynamic_energy_threshold = True
            self._reconhecedor.pause_threshold = 0.8

    # ---------- GRAVAR + TRANSCREVER ----------
    def ouvir(self, timeout=5, phrase_limit=8):
        """Grava do microfone e retorna o texto transcrito."""
        if not self._reconhecedor:
            return {"erro": "SpeechRecognition nao instalado"}

        try:
            with sr.Microphone() as source:
                self._reconhecedor.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._reconhecedor.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
        except sr.WaitTimeoutError:
            return {"erro": "Tempo esgotado. Voce nao falou nada."}
        except Exception as e:
            return {"erro": f"Erro no microfone: {e}"}

        # Tentar Whisper local primeiro (se disponivel)
        texto = None
        fonte = None
        if WHISPER_DISPONIVEL:
            try:
                texto = self._transcrever_whisper(audio)
                fonte = "whisper"
            except Exception as e:
                print(f"Whisper falhou: {e}")

        if texto is None and GOOGLE_DISPONIVEL:
            try:
                texto = self._reconhecedor.recognize_google(
                    audio, language=self.idioma
                )
                fonte = "google"
            except sr.UnknownValueError:
                return {"erro": "Nao entendi o que voce falou."}
            except sr.RequestError as e:
                return {"erro": f"Erro no Google Speech: {e}"}

        if texto is None:
            return {"erro": "Nenhum backend de transcricao disponivel."}

        return {"texto": texto, "fonte": fonte}

    def _transcrever_whisper(self, audio):
        if self.whisper_model is None:
            self.whisper_model = whisper.load_model("tiny")
        wav_bytes = audio.get_wav_data()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(wav_bytes)
            path = tmp.name
        try:
            result = self.whisper_model.transcribe(path, language="en")
            return result["text"].strip()
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass


# ============================================================
# COMPARACAO / NOTA DE PRONUNCIA
# ============================================================
def normalizar(texto):
    """Lowercase, remove pontuacao basica."""
    return "".join(c.lower() if c.isalnum() or c.isspace() else " "
                   for c in texto).split()


def comparar(falado, esperado):
    """Retorna dict com nota 0-100, palavras coloridas e detalhes."""
    if not falado or not esperado:
        return {"nota": 0, "palavras": [], "similaridade": 0.0,
                "falado": falado or "", "esperado": esperado or ""}

    p_falado = normalizar(falado)
    p_esperado = normalizar(esperado)

    # 1) Nota global (similaridade da frase toda)
    sim_global = SequenceMatcher(
        None, " ".join(p_falado), " ".join(p_esperado)
    ).ratio()

    # 2) Nota por palavra usando alinhamento
    matcher = SequenceMatcher(None, p_esperado, p_falado)
    palavras = []
    acertos_palavra = 0

    status_esperado = ["faltando"] * len(p_esperado)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i in range(i1, i2):
                status_esperado[i] = "ok"
                acertos_palavra += 1
        elif tag == "replace":
            for i, j in zip(range(i1, i2), range(j1, j2)):
                s = SequenceMatcher(None, p_esperado[i], p_falado[j]).ratio()
                if s >= 0.7:
                    status_esperado[i] = "aprox"
                    acertos_palavra += 0.5
                else:
                    status_esperado[i] = "errado"

    for i, palavra in enumerate(p_esperado):
        palavras.append({"palavra": palavra, "status": status_esperado[i]})

    if p_esperado:
        nota_palavra = (acertos_palavra / len(p_esperado)) * 100
    else:
        nota_palavra = 0
    nota = int(round(0.6 * nota_palavra + 0.4 * sim_global * 100))
    nota = max(0, min(100, nota))

    return {
        "nota": nota,
        "palavras": palavras,
        "similaridade": sim_global,
        "falado": falado,
        "esperado": esperado,
    }


# ============================================================
# PERSISTENCIA DE NOTAS (dados/pronuncia.json)
# ============================================================
def carregar_notas(caminho):
    if not os.path.exists(caminho):
        return {}
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def salvar_notas(caminho, dados):
    try:
        pasta = os.path.dirname(caminho)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar notas: {e}")


def registrar_nota(dados, frase, nota):
    """Guarda historico de notas de uma frase e retorna a media."""
    entry = dados.setdefault(frase, {"notas": [], "media": 0, "tentativas": 0})
    entry["notas"].append(nota)
    entry["tentativas"] += 1
    entry["media"] = round(sum(entry["notas"]) / len(entry["notas"]), 1)
    return entry["media"]