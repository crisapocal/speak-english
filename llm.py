# ============================================================
#  LLM - Fase 4 (otimizado para Llama 3.2 1B)
#  Explicacao de erros + Geracao de frases + Conversacao
# ============================================================

import os
import json
import threading

# ---------- BACKENDS OPCIONAIS ----------
REQUESTS_OK = False
OPENAI_DISPONIVEL = False

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    requests = None
    print("AVISO: requests nao instalado. Rode: pip install requests")

try:
    import openai
    OPENAI_DISPONIVEL = True
except ImportError:
    openai = None


# ============================================================
# CONFIG
# ============================================================
CONFIG = {
    "backend": "ollama",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.2:1b",     # modelo leve e obediente
    "openai_model": "gpt-4o-mini",
    "openai_key": os.environ.get("OPENAI_API_KEY", ""),
    "timeout": 120,
    "debug": True,
}


def _log(msg):
    if CONFIG.get("debug"):
        print(f"[LLM] {msg}")


# ============================================================
# CHAMADA OLLAMA
# ============================================================
def _chamar_ollama(prompt, sistema=None):
    """Envia prompt ao Ollama via /api/generate."""
    if not REQUESTS_OK:
        return None, "requests nao instalado"

    # Llama 3.2 entende bem o campo system separado
    payload = {
        "model": CONFIG["ollama_model"],
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 200,     # resposta curta
        },
    }
    if sistema:
        payload["system"] = sistema

    url = f"{CONFIG['ollama_url']}/api/generate"
    _log(f"POST {url} model={CONFIG['ollama_model']} prompt_len={len(prompt)}")

    try:
        r = requests.post(url, json=payload, timeout=CONFIG["timeout"])
    except requests.exceptions.Timeout:
        return None, f"Timeout ({CONFIG['timeout']}s)."
    except requests.exceptions.ConnectionError as e:
        return None, f"Ollama nao respondeu em {CONFIG['ollama_url']}: {e}"
    except Exception as e:
        return None, f"Erro HTTP: {e}"

    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:200]}"

    try:
        data = r.json()
    except Exception as e:
        return None, f"JSON invalido: {e}"

    resposta = data.get("response", "").strip()
    if not resposta:
        return None, "Resposta vazia do Ollama"
    _log(f"OK ({len(resposta)} chars)")
    return resposta, None


# ============================================================
# CHAMADA OPENAI (opcional)
# ============================================================
def _chamar_openai(prompt, sistema=None):
    if not OPENAI_DISPONIVEL:
        return None, "openai nao instalado"
    if not CONFIG["openai_key"]:
        return None, "OPENAI_API_KEY nao definida"
    try:
        client = openai.OpenAI(api_key=CONFIG["openai_key"])
        msgs = []
        if sistema:
            msgs.append({"role": "system", "content": sistema})
        msgs.append({"role": "user", "content": prompt})
        resp = client.chat.completions.create(
            model=CONFIG["openai_model"],
            messages=msgs,
            timeout=CONFIG["timeout"],
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip(), None
    except Exception as e:
        return None, f"OpenAI erro: {e}"


# ============================================================
# DISPATCHER
# ============================================================
def _chamar_llm(prompt, sistema=None):
    backend = CONFIG.get("backend", "ollama").lower()
    if backend == "openai":
        return _chamar_openai(prompt, sistema)
    return _chamar_ollama(prompt, sistema)


def disponivel():
    if CONFIG.get("backend") == "openai":
        return OPENAI_DISPONIVEL and bool(CONFIG.get("openai_key"))
    if not REQUESTS_OK:
        return False
    try:
        r = requests.get(f"{CONFIG['ollama_url']}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def testar_conexao():
    if CONFIG.get("backend") == "openai":
        if not OPENAI_DISPONIVEL:
            return False, "openai nao instalado"
        if not CONFIG.get("openai_key"):
            return False, "OPENAI_API_KEY nao definida"
        texto, err = _chamar_openai("Responda apenas: OK")
        if texto:
            return True, f"OpenAI: {texto[:40]}"
        return False, err or "sem resposta"
    if not REQUESTS_OK:
        return False, "requests nao instalado"
    try:
        r = requests.get(f"{CONFIG['ollama_url']}/api/tags", timeout=3)
        if r.status_code == 200:
            modelos = [m.get('name', '?') for m in r.json().get('models', [])]
            return True, f"Ollama OK. Modelos: {', '.join(modelos[:5])}"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, f"Ollama nao respondeu: {e}"


# ============================================================
# FUNCOES DE ALTO NIVEL
# ============================================================

def explicar_erro(frase_esperada, frase_falada, contracao=None):
    """Explica por que o usuario errou."""
    sistema = (
        "Voce e um professor de ingles brasileiro, paciente e didatico. "
        "Responda em portugues do Brasil, em no maximo 3 frases curtas. "
        "Seja direto, sem formatacao markdown."
    )
    prompt = (
        f"O aluno tentou falar: '{frase_esperada}'\n"
        f"Mas ele falou: '{frase_falada}'\n"
        f"Contracao em estudo: '{contracao or 'N/A'}'\n\n"
        f"Explique em 2-3 frases curtas:\n"
        f"1) O que ele errou\n"
        f"2) Por que essa contracao e usada assim\n"
        f"3) Uma dica para lembrar"
    )
    texto, err = _chamar_llm(prompt, sistema)
    if texto:
        return texto, None
    _log(f"explicar_erro falhou: {err}")
    return _fallback_explicacao(frase_esperada, frase_falada, contracao), err


def _fallback_explicacao(frase_esperada, frase_falada, contracao):
    esperado_words = set(frase_esperada.lower().replace("'", "'").split())
    falado_words = set(frase_falada.lower().replace("'", "'").split())
    faltando = esperado_words - falado_words
    sobrando = falado_words - esperado_words
    linhas = [f"Esperado: {frase_esperada}", f"Voce falou: {frase_falada}"]
    if contracao:
        linhas.append(f"Contracao: {contracao}")
    if faltando:
        linhas.append(f"Faltou: {', '.join(sorted(faltando))}")
    if sobrando:
        linhas.append(f"Sobrou: {', '.join(sorted(sobrando))}")
    if not faltando and not sobrando:
        linhas.append("Palavras ok - foque na pronuncia.")
    return "\n".join(linhas)


def gerar_frases(contracao, tema="cotidiano", quantidade=5):
    """Gera frases novas com a contracao."""
    sistema = (
        "Voce cria frases curtas em ingles informal para estudantes brasileiros. "
        "Responda APENAS com as frases no formato pedido, sem numeracao, "
        "sem explicacao, sem cabecalho, sem markdown."
    )
    prompt = (
        f"Crie {quantidade} frases curtas em ingles informal usando '{contracao}', "
        f"tema: {tema}.\n\n"
        f"Formato EXATO (uma por linha, 3 colunas separadas por |):\n"
        f"INGLES|PORTUGUES|FONETICA\n\n"
        f"Fonetica aproximada em portugues brasileiro. "
        f"Responda com APENAS as {quantidade} linhas, sem cabecalho."
    )
    texto, err = _chamar_llm(prompt, sistema)
    if not texto:
        _log(f"gerar_frases falhou: {err}")
        return [], err

    frases = []
    for linha in texto.splitlines():
        linha = linha.strip()
        low = linha.lower()
        if low.startswith("ingles|") or low.startswith("english|"):
            continue
        if "|" in linha:
            partes = [p.strip() for p in linha.split("|")]
            if len(partes) >= 3 and partes[0]:
                frases.append({
                    "ing": partes[0],
                    "por": partes[1] if len(partes) > 1 else "",
                    "fon": partes[2] if len(partes) > 2 else "",
                })
    return frases[:quantidade], None


def conversar(historico, mensagem_usuario):
    """Modo conversacao livre - otimizado para Llama 3.2."""
    # ---- SISTEMA CLARO ----
    sistema = (
        "You are an American English tutor chatting with a Brazilian student. "
        "Rules: reply with 1-2 short sentences in English using natural "
        "contractions (gonna, wanna, gotta, ain't). End with the Portuguese "
        "translation in parentheses. Do not repeat the student's message. "
        "Do not write labels like 'Student:' or 'Tutor:'. Just answer directly."
    )

    # ---- PROMPT COM CONTEXTO LEVE ----
    contexto = ""
    if len(historico) >= 2:
        ultimas = historico[-3:-1]
        if ultimas:
            linhas_ctx = []
            for msg in ultimas:
                quem = "Student" if msg['role'] == 'user' else "Tutor"
                linhas_ctx.append(f"{quem}: {msg['content'][:80]}")
            contexto = "Recent context:\n" + "\n".join(linhas_ctx) + "\n\n"

    prompt = (
        f"{contexto}"
        f"Student just said: \"{mensagem_usuario}\"\n\n"
        f"Your response (1 short sentence in English + Portuguese "
        f"translation in parentheses):"
    )

    _log(f"conversar() prompt com {len(prompt)} chars")
    texto, err = _chamar_llm(prompt, sistema)

    if not texto:
        _log(f"conversar falhou: {err}")
        return (f"(LLM indisponivel: {err})\n"
                f"Sure! That's cool. Wanna try again?\n"
                f"(Claro! Isso e legal. Quer tentar de novo?)"), err

    # ---- LIMPEZA POS-PROCESSAMENTO ----
    linhas_limpas = []
    for linha in texto.split("\n"):
        linha_strip = linha.strip()
        if not linha_strip:
            continue
        low = linha_strip.lower()

        # Remove linhas que sao eco/instrucao
        lixo = [
            "student:", "tutor:", "you:", "assistant:",
            "brazil's response", "brazil's reply",
            "your response", "english + portuguese",
            "recent context", "student just said",
            "(english", "(traducao)",
        ]
        if any(low.startswith(x) or x in low[:40] for x in lixo):
            continue

        linhas_limpas.append(linha_strip)

    texto_limpo = "\n".join(linhas_limpas).strip()

    if not texto_limpo:
        texto_limpo = texto.strip()

    linhas_final = texto_limpo.split("\n")[:4]
    texto_final = "\n".join(linhas_final)

    _log(f"conversar OK: {texto_final[:60]}...")
    return texto_final, None