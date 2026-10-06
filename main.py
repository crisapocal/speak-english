# ============================================================
#  SPEAK ENGLISH - PYGame Edition v4.0
#  SRS + Quiz Adaptativo + Voz + Atalhos + Backup + Relatorio
#  + Tema Noturno + LLM (explicacao, geracao, conversacao)
# ============================================================

import pygame
import sys
import os
import json
import random
import threading
from datetime import datetime, date, timedelta

# ---------- TTS OPCIONAL ----------
try:
    import pyttsx3
    TTS_DISPONIVEL = True
except ImportError:
    TTS_DISPONIVEL = False
    print("AVISO: pyttsx3 nao instalado. TTS desativado. Rode: pip install pyttsx3")


# ============================================================
# CONFIGURACOES GERAIS
# ============================================================
LARGURA, ALTURA = 1000, 780
FPS = 60
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(BASE_DIR, "dados")
ARQ_PROGRESSO_JSON = os.path.join(BASE_DIR, "progresso.json")
ARQ_PROGRESSO_TXT = os.path.join(BASE_DIR, "progresso.txt")
ARQ_PRONUNCIA = os.path.join(BASE_DIR, "dados", "pronuncia.json")


# ============================================================
# IMPORTAR MODULOS LOCAIS
# ============================================================
# --- Reconhecimento de voz (Fase 3) ---
try:
    from reconhecimento import (
        Reconhecedor, comparar, carregar_notas, salvar_notas, registrar_nota
    )
    VOZ_DISPONIVEL = True
except ImportError as e:
    VOZ_DISPONIVEL = False
    print(f"AVISO: modulo reconhecimento nao carregado: {e}")

    def carregar_notas(caminho):
        return {}
    def salvar_notas(caminho, dados):
        pass
    def registrar_nota(dados, frase, nota):
        return 0
    def comparar(falado, esperado):
        return {"nota": 0, "palavras": [], "similaridade": 0.0,
                "falado": "", "esperado": ""}
    Reconhecedor = None

# --- Utils (backup, relatorio, tema noturno) ---
try:
    from utils import (
        fazer_backup, exportar_relatorio,
        aplicar_tema_noturno_se_necessario, hora_para_tema_noturno
    )
    UTILS_DISPONIVEL = True
except ImportError as e:
    UTILS_DISPONIVEL = False
    print(f"AVISO: modulo utils nao carregado: {e}")
    def fazer_backup(base, arq):
        return None
    def exportar_relatorio(base, prog, notas=None):
        return None
    def aplicar_tema_noturno_se_necessario(cls):
        return False
    def hora_para_tema_noturno():
        return False

# --- LLM (Fase 4) ---
try:
    import llm
    LLM_DISPONIVEL = True
except ImportError as e:
    LLM_DISPONIVEL = False
    print(f"AVISO: modulo llm nao carregado: {e}")
    llm = None


# ============================================================
# TTS
# ============================================================
_tts_lock = threading.Lock()


def falar(texto, devagar=False):
    if not TTS_DISPONIVEL or not texto:
        return

    def _run():
        with _tts_lock:
            try:
                engine = pyttsx3.init()
                for v in engine.getProperty('voices'):
                    vid = v.id.lower()
                    vname = v.name.lower()
                    if ('english' in vname or 'en-us' in vid or 'en_us' in vid
                            or 'david' in vname or 'zira' in vname):
                        engine.setProperty('voice', v.id)
                        break
                engine.setProperty('rate', 120 if devagar else 170)
                engine.setProperty('volume', 1.0)
                engine.say(texto)
                engine.runAndWait()
                engine.stop()
                del engine
            except Exception as e:
                print(f"Erro TTS: {e}")

    threading.Thread(target=_run, daemon=True).start()


# ============================================================
# SRS + PROGRESSO
# ============================================================
def hoje_str():
    return date.today().isoformat()


def criar_estado_vazio():
    return {
        "versao": 4,
        "criado_em": hoje_str(),
        "ultimo_estudo": None,
        "streak_dias": 0,
        "stats_globais": {
            "acertos": 0, "erros": 0, "estudos": 0, "tempo_total_seg": 0,
        },
        "srs": {},
        "contracoes_abertas": {},
        "por_contracao": {},
    }


def carregar_progresso():
    if os.path.exists(ARQ_PROGRESSO_JSON):
        try:
            with open(ARQ_PROGRESSO_JSON, encoding='utf-8') as f:
                dados = json.load(f)
            base = criar_estado_vazio()
            for k, v in base.items():
                if k not in dados:
                    dados[k] = v
            return dados
        except Exception as e:
            print(f"Erro ao ler JSON, recriando: {e}")

    estado = criar_estado_vazio()
    if os.path.exists(ARQ_PROGRESSO_TXT):
        try:
            with open(ARQ_PROGRESSO_TXT, encoding='utf-8-sig') as f:
                for linha in f:
                    linha = linha.strip()
                    if linha.startswith('ACERTOS='):
                        estado['stats_globais']['acertos'] = int(linha.split('=')[1])
                    elif linha.startswith('ERROS='):
                        estado['stats_globais']['erros'] = int(linha.split('=')[1])
                    elif linha.startswith('ESTUDOS='):
                        estado['stats_globais']['estudos'] = int(linha.split('=')[1])
            print("Progresso migrado de progresso.txt -> progresso.json")
        except Exception as e:
            print(f"Erro migrando txt: {e}")
    salvar_progresso(estado)
    return estado


def salvar_progresso(p):
    try:
        with open(ARQ_PROGRESSO_JSON, 'w', encoding='utf-8') as f:
            json.dump(p, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar progresso: {e}")


def srs_atualizar(estado, frase_ing, acertou):
    srs = estado['srs'].setdefault(frase_ing, {
        "acertos": 0, "erros": 0, "facilidade": 2.5,
        "intervalo": 0, "proxima": hoje_str(), "ultima": None,
    })
    srs['ultima'] = hoje_str()
    if acertou:
        srs['acertos'] += 1
        n = srs['acertos']
        if n == 1:
            srs['intervalo'] = 1
        elif n == 2:
            srs['intervalo'] = 3
        else:
            srs['intervalo'] = max(1, int(srs['intervalo'] * srs['facilidade']))
        srs['facilidade'] = min(3.0, srs['facilidade'] + 0.1)
    else:
        srs['erros'] += 1
        srs['acertos'] = 0
        srs['intervalo'] = 1
        srs['facilidade'] = max(1.3, srs['facilidade'] - 0.2)
    proxima = date.today() + timedelta(days=srs['intervalo'])
    srs['proxima'] = proxima.isoformat()


def srs_vencida(srs_entry):
    try:
        prox = date.fromisoformat(srs_entry.get('proxima', hoje_str()))
        return prox <= date.today()
    except Exception:
        return True


def frases_para_revisar(estado, todas_frases):
    resultado = []
    for f in todas_frases:
        info = estado['srs'].get(f['ing'])
        if info is None or srs_vencida(info):
            resultado.append(f)
    return resultado


def estatisticas_por_contracao(estado, contracao):
    return estado['por_contracao'].setdefault(contracao, {
        "acertos": 0, "erros": 0, "revisoes": 0
    })


# ============================================================
# LER ARQUIVO DE FRASES
# ============================================================
def carregar_frases(nome_arquivo):
    caminho = os.path.join(PASTA_DADOS, f"{nome_arquivo}.txt")
    frases = []
    if not os.path.exists(caminho):
        print(f"AVISO: arquivo nao encontrado -> {caminho}")
        return frases
    try:
        with open(caminho, encoding='utf-8-sig') as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                partes = linha.split('|')
                if len(partes) >= 3:
                    frases.append({
                        'ing': partes[0].strip(),
                        'por': partes[1].strip(),
                        'fon': partes[2].strip(),
                    })
    except Exception as e:
        print(f"Erro ao ler {caminho}: {e}")
    return frases


# ============================================================
# TEMA / CORES
# ============================================================
class Tema:
    escuro = True

    @staticmethod
    def get(nome):
        if Tema.escuro:
            mapa = {
                'fundo':    (30, 30, 40),
                'painel':   (40, 42, 54),
                'header':   (20, 22, 30),
                'botao':    (75, 78, 100),
                'hover':    (100, 105, 130),
                'verde':    (80, 200, 120),
                'azul':     (80, 160, 240),
                'amarelo':  (240, 190, 80),
                'vermelho': (220, 80, 80),
                'laranja':  (240, 140, 60),
                'roxo':     (170, 120, 220),
                'texto':    (255, 255, 255),
                'suave':    (180, 180, 200),
                'console':  (15, 15, 20),
            }
        else:
            mapa = {
                'fundo':    (245, 246, 250),
                'painel':   (255, 255, 255),
                'header':   (230, 232, 240),
                'botao':    (230, 233, 240),
                'hover':    (205, 212, 225),
                'verde':    (40, 160, 90),
                'azul':     (50, 120, 210),
                'amarelo':  (180, 130, 20),
                'vermelho': (200, 60, 60),
                'laranja':  (200, 110, 30),
                'roxo':     (120, 70, 180),
                'texto':    (30, 30, 40),
                'suave':    (90, 90, 110),
                'console':  (250, 250, 252),
            }
        return mapa.get(nome, (255, 255, 255))

    @staticmethod
    def alternar():
        Tema.escuro = not Tema.escuro


# ============================================================
# BOTAO
# ============================================================
class Botao:
    def __init__(self, x, y, w, h, texto, acao=None, cor_bg='botao',
                 fonte=None, alinhamento='center'):
        self.rect = pygame.Rect(x, y, w, h)
        self.texto = texto
        self.acao = acao
        self.cor_bg = cor_bg
        self.fonte = fonte
        self.alinhamento = alinhamento
        self.hover = False
        self.visivel = True
        self.habilitado = True

    def desenhar(self, surface):
        if not self.visivel:
            return
        if not self.habilitado:
            c = Tema.get('botao')
        elif self.hover:
            c = Tema.get('hover')
        else:
            c = Tema.get(self.cor_bg)
        pygame.draw.rect(surface, c, self.rect, border_radius=6)
        pygame.draw.rect(surface, Tema.get('suave'), self.rect, 1, border_radius=6)
        f = self.fonte or pygame.font.SysFont("Segoe UI", 17)
        txt = f.render(self.texto, True, Tema.get('texto'))
        if self.alinhamento == 'left':
            surface.blit(txt, (self.rect.x + 15,
                               self.rect.centery - txt.get_height() // 2))
        else:
            surface.blit(txt, txt.get_rect(center=self.rect.center))

    def atualizar(self, mouse_pos):
        self.hover = (self.visivel and self.habilitado
                      and self.rect.collidepoint(mouse_pos))

    def clicou(self, evento):
        return (self.visivel and self.habilitado
                and evento.type == pygame.MOUSEBUTTONDOWN
                and evento.button == 1
                and self.rect.collidepoint(evento.pos))

    def executar(self):
        if self.acao:
            self.acao()


# ============================================================
# CONTRACOES
# ============================================================
CONTRACOES = [
    ("gotta",    "GOTTA    (ter que)"),
    ("gonna",    "GONNA    (futuro)"),
    ("wanna",    "WANNA    (querer)"),
    ("gimme",    "GIMME    (me de)"),
    ("lemme",    "LEMME    (deixa eu)"),
    ("kinda",    "KINDA    (meio que)"),
    ("sorta",    "SORTA    (meio que)"),
    ("outta",    "OUTTA    (fora/sem)"),
    ("hafta",    "HAFTA    (ter que)"),
    ("shoulda",  "SHOULDA  (deveria ter)"),
    ("coulda",   "COULDA   (poderia ter)"),
    ("woulda",   "WOULDA   (teria)"),
    ("musta",    "MUSTA    (deve ter)"),
    ("aint",     "AIN'T    (negacao)"),
    ("dontcha",  "DON'TCHA (voce nao)"),
    ("cmon",     "C'MON    (vamos)"),
    ("gotcha",   "GOTCHA   (te peguei)"),
    ("betcha",   "BETCHA   (aposto que)"),
    ("dunno",    "DUNNO    (nao sei)"),
    ("imma",     "I'MMA    (eu vou)"),
    ("modais",   "VERBOS MODAIS"),
]


# ============================================================
# QUIZ
# ============================================================
PERGUNTAS_QUIZ = [
    {"perg": "Eu quero ir.",                "A": "I gonna go.",              "B": "I wanna go.",              "C": "I gotta go.",              "D": "I shoulda go.",              "corr": "B"},
    {"perg": "Eu tenho que ir.",            "A": "I wanna go.",              "B": "I gotta go.",              "C": "I'm gonna go.",            "D": "I dunno go.",                "corr": "B"},
    {"perg": "Eu vou viajar amanha.",       "A": "I gotta travel tomorrow.", "B": "I wanna travel tomorrow.", "C": "I'm gonna travel tomorrow.","D": "I shoulda travel tomorrow.", "corr": "C"},
    {"perg": "Deixa eu ver.",               "A": "Gimme see.",               "B": "Lemme see.",               "C": "Gonna see.",               "D": "Gotta see.",                 "corr": "B"},
    {"perg": "Me de uma chance.",           "A": "Lemme a chance.",          "B": "Gonna a chance.",          "C": "Gimme a chance.",          "D": "Wanna a chance.",            "corr": "C"},
    {"perg": "Eu deveria ter te ligado.",   "A": "I coulda called you.",     "B": "I shoulda called you.",    "C": "I woulda called you.",     "D": "I musta called you.",        "corr": "B"},
    {"perg": "Eu poderia ter ido.",         "A": "I shoulda gone.",          "B": "I woulda gone.",           "C": "I coulda gone.",           "D": "I musta gone.",              "corr": "C"},
    {"perg": "Eu nao sei.",                 "A": "I dunno.",                 "B": "I wanna.",                 "C": "I gotta.",                 "D": "I'mma.",                     "corr": "A"},
    {"perg": "Voce nao gosta disso?",       "A": "Don'tcha like it?",        "B": "Betcha like it?",          "C": "Gotcha like it?",          "D": "Dunno like it?",             "corr": "A"},
    {"perg": "Eu vou ir.",                  "A": "I gotta go.",              "B": "I wanna go.",              "C": "I'mma go.",                "D": "I shoulda go.",              "corr": "C"},
    {"perg": "Ela vai ligar mais tarde.",   "A": "She gotta call later.",    "B": "She's gonna call later.",  "C": "She wanna call later.",    "D": "She shoulda call later.",    "corr": "B"},
    {"perg": "Estou sem tempo.",            "A": "I'm outta time.",          "B": "I'm gonna time.",          "C": "I'm gotta time.",          "D": "I'm wanna time.",            "corr": "A"},
    {"perg": "Voce tem que provar isso.",   "A": "You wanna try this.",      "B": "You gonna try this.",      "C": "You gotta try this.",      "D": "You shoulda try this.",      "corr": "C"},
    {"perg": "Aposto que voce esta certo.", "A": "Gotcha you're right.",     "B": "Betcha you're right.",     "C": "Dunno you're right.",      "D": "Lemme you're right.",        "corr": "B"},
    {"perg": "Te peguei!",                  "A": "Gotcha!",                  "B": "Betcha!",                  "C": "Dunno!",                   "D": "Gimme!",                     "corr": "A"},
    {"perg": "Nos temos que conversar.",    "A": "We gonna talk.",           "B": "We wanna talk.",           "C": "We gotta talk.",           "D": "We shoulda talk.",           "corr": "C"},
    {"perg": "Eu quero aprender ingles.",   "A": "I gotta learn English.",   "B": "I wanna learn English.",   "C": "I'm gonna learn English.", "D": "I shoulda learn English.",   "corr": "B"},
    {"perg": "Estou meio cansado.",         "A": "I'm kinda tired.",         "B": "I'm gonna tired.",         "C": "I'm gotta tired.",         "D": "I'm wanna tired.",           "corr": "A"},
    {"perg": "Ele deve ter saido.",         "A": "He shoulda left.",         "B": "He coulda left.",          "C": "He woulda left.",          "D": "He musta left.",             "corr": "D"},
    {"perg": "Vamos, bora!",                "A": "C'mon, let's go!",         "B": "Gotcha, let's go!",        "C": "Betcha, let's go!",        "D": "Dunno, let's go!",           "corr": "A"},
    {"perg": "Voce pode me ajudar?",        "A": "May you help me?",         "B": "Must you help me?",        "C": "Can you help me?",         "D": "Should you help me?",        "corr": "C"},
    {"perg": "Voce deveria estudar mais.",  "A": "You could study more.",    "B": "You should study more.",   "C": "You must study more.",     "D": "You may study more.",        "corr": "B"},
    {"perg": "Voce deve usar o cinto.",     "A": "You can wear a seatbelt.", "B": "You should wear a seatbelt.","C": "You may wear a seatbelt.", "D": "You must wear a seatbelt.",  "corr": "D"},
    {"perg": "Posso entrar?",               "A": "May I come in?",           "B": "Must I come in?",          "C": "Should I come in?",        "D": "Could I come in?",           "corr": "A"},
    {"perg": "Ela talvez esteja cansada.",  "A": "She must be tired.",       "B": "She might be tired.",      "C": "She can be tired.",        "D": "She should be tired.",       "corr": "B"},
    {"perg": "Deixa eu te ajudar.",         "A": "Gimme help you.",          "B": "Gonna help you.",          "C": "Lemme help you.",          "D": "Gotta help you.",            "corr": "C"},
    {"perg": "Nao sei o que fazer.",        "A": "Dunno what to do.",        "B": "Gonna what to do.",        "C": "Gotta what to do.",        "D": "Wanna what to do.",          "corr": "A"},
    {"perg": "Isso nao e verdade.",         "A": "That don't true.",         "B": "That won't true.",         "C": "That can't true.",         "D": "That ain't true.",           "corr": "D"},
    {"perg": "Eu vou comer pizza.",         "A": "I gotta eat pizza.",       "B": "I'm gonna eat pizza.",     "C": "I shoulda eat pizza.",     "D": "I wanna eat pizza.",         "corr": "B"},
    {"perg": "Me de um minuto.",            "A": "Gimme a minute.",          "B": "Lemme a minute.",          "C": "Gonna a minute.",          "D": "Gotta a minute.",            "corr": "A"},
]


# ============================================================
# GAME
# ============================================================
class Jogo:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SPEAK ENGLISH v4.0 - Bot IA + Backup + Relatorio")
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        self.clock = pygame.time.Clock()

        # Fontes
        self.f_titulo   = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.f_sub      = pygame.font.SysFont("Segoe UI", 15)
        self.f_normal   = pygame.font.SysFont("Segoe UI", 17)
        self.f_pequena  = pygame.font.SysFont("Consolas", 14)
        self.f_grande   = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.f_frase    = pygame.font.SysFont("Segoe UI", 30, bold=True)
        self.f_mini     = pygame.font.SysFont("Segoe UI", 13)
        self.f_chat     = pygame.font.SysFont("Segoe UI", 14)

        # Tema noturno automatico (aplica antes de qualquer coisa)
        if UTILS_DISPONIVEL:
            aplicar_tema_noturno_se_necessario(Tema)

        # Estado
        self.progresso = carregar_progresso()
        self.notas_pronuncia = carregar_notas(ARQ_PRONUNCIA)
        self.reconhecedor = Reconhecedor() if (VOZ_DISPONIVEL and Reconhecedor) else None
        self.estado = 'estudo'
        self.status_log = []
        self.registrar_estudo_hoje()

        # LLM disponivel?
        self.llm_ok = LLM_DISPONIVEL and llm and llm.disponivel()

        # Botao tema
        self.btn_tema = Botao(870, 22, 100, 36, "TEMA", self.alternar_tema,
                              fonte=self.f_normal)

        # Botoes de estudo
        self.botoes_estudo = []
        self.criar_botoes_estudo()

        # Cenas
        self.cena_frases = None
        self.cena_quiz = None
        self.cena_revisao = None
        self.cena_dashboard = None
        self.cena_pronuncia = None
        self.cena_chat = None
        self.cena_gerador = None

        # Status inicial
        self.add_status("Bot v4.0 iniciado.")
        self.add_status(f"Streak: {self.progresso['streak_dias']} dias")
        if self.reconhecedor:
            self.add_status("Voz ATIVA (ESPACO=gravar, O=ouvir)")
        if self.llm_ok:
            self.add_status("LLM conectado - Fase 4 ativa!")
        elif LLM_DISPONIVEL:
            self.add_status("LLM indisponivel (rode 'ollama serve')")

    # ---------- REGISTRAR ESTUDO ----------
    def registrar_estudo_hoje(self):
        hoje = hoje_str()
        ultimo = self.progresso.get('ultimo_estudo')
        if ultimo == hoje:
            return
        if ultimo:
            try:
                d_ultimo = date.fromisoformat(ultimo)
                if (date.today() - d_ultimo).days == 1:
                    self.progresso['streak_dias'] += 1
                else:
                    self.progresso['streak_dias'] = 1
            except Exception:
                self.progresso['streak_dias'] = 1
        else:
            self.progresso['streak_dias'] = 1
        self.progresso['ultimo_estudo'] = hoje
        salvar_progresso(self.progresso)

    # ---------- UTILITARIOS ----------
    def add_status(self, msg):
        hora = datetime.now().strftime("%H:%M:%S")
        self.status_log.append(f"[{hora}] {msg}")
        if len(self.status_log) > 3:
            self.status_log.pop(0)

    def alternar_tema(self):
        Tema.alternar()
        self.add_status(f"Tema: {'escuro' if Tema.escuro else 'claro'}")

    def atualizar_progresso_label(self):
        g = self.progresso['stats_globais']
        return (f"Acertos: {g['acertos']}  Erros: {g['erros']}  "
                f"Estudos: {g['estudos']}  Streak: {self.progresso['streak_dias']}d")

    # ---------- BOTOES DE ESTUDO ----------
    def criar_botoes_estudo(self):
        self.botoes_estudo = []
        x0, y0 = 30, 165
        cols = 3
        largura_btn = 305
        altura_btn = 40
        espaco_x = 320
        espaco_y = 44
        for i, (arq, rotulo) in enumerate(CONTRACOES):
            cx = x0 + (i % cols) * espaco_x
            cy = y0 + (i // cols) * espaco_y
            cor_bg = 'azul' if arq == 'modais' else 'botao'
            btn = Botao(cx, cy, largura_btn, altura_btn, rotulo,
                        lambda a=arq, r=rotulo: self.abrir_frases(a, r),
                        cor_bg=cor_bg,
                        fonte=self.f_normal, alinhamento='left')
            self.botoes_estudo.append(btn)

    # ---------- ABRIR CENAS ----------
    def abrir_frases(self, nome_arq, titulo):
        frases = carregar_frases(nome_arq)
        if not frases:
            self.add_status(f"ERRO: {nome_arq}.txt nao encontrado!")
            return
        self.cena_frases = CenaFrases(self, titulo, frases, nome_arq=nome_arq)
        self.progresso['stats_globais']['estudos'] += 1
        self.progresso['contracoes_abertas'][nome_arq] = \
            self.progresso['contracoes_abertas'].get(nome_arq, 0) + 1
        salvar_progresso(self.progresso)
        self.estado = 'frases'
        self.add_status(f"{titulo} ({len(frases)} frases)")

    def abrir_revisao(self):
        todas = []
        for arq, _ in CONTRACOES:
            for f in carregar_frases(arq):
                f['_contracao'] = arq
                todas.append(f)
        vencidas = frases_para_revisar(self.progresso, todas)
        if not vencidas:
            self.add_status("Nada para revisar hoje!")
            return
        self.cena_revisao = CenaRevisao(self, vencidas)
        self.estado = 'revisao'
        self.add_status(f"Revisao: {len(vencidas)} frases")

    def abrir_dashboard(self):
        self.cena_dashboard = CenaDashboard(self)
        self.estado = 'dashboard'

    def abrir_quiz(self):
        self.cena_quiz = CenaQuiz(self)
        self.estado = 'quiz'
        self.add_status("Quiz adaptativo iniciado.")

    def abrir_pronuncia(self):
        if not self.reconhecedor:
            self.add_status("Microfone indisponivel.")
            return
        if self.cena_frases and self.cena_frases.frases:
            frases = self.cena_frases.frases
        else:
            frases = carregar_frases("gotta")
        if not frases:
            self.add_status("Nenhuma frase carregada.")
            return
        self.cena_pronuncia = CenaPronuncia(self, frases, origem="pronuncia")
        self.estado = 'pronuncia'
        self.add_status("PRONUNCIA. ESPACO=gravar, O=ouvir")

    def abrir_chat(self):
        if not self.llm_ok:
            self.add_status("LLM nao disponivel. Inicie o Ollama.")
            return
        self.cena_chat = CenaChat(self)
        self.estado = 'chat'
        self.add_status("Chat com IA. ESC volta ao menu.")

    def abrir_gerador(self):
        if not self.llm_ok:
            self.add_status("LLM nao disponivel. Inicie o Ollama.")
            return
        self.cena_gerador = CenaGerador(self)
        self.estado = 'gerador'
        self.add_status("Gerador de frases com IA.")

    # ---------- DESENHAR ----------
    def desenhar_header(self):
        pygame.draw.rect(self.tela, Tema.get('header'), (0, 0, LARGURA, 90))
        titulo = self.f_titulo.render("SPEAK ENGLISH v4.0", True, Tema.get('verde'))
        self.tela.blit(titulo, (30, 22))
        sub = self.f_sub.render(
            "SRS | Quiz | Voz | IA | Backup | Relatorio | Noturno",
            True, Tema.get('suave'))
        self.tela.blit(sub, (32, 56))

        prog = self.f_normal.render(self.atualizar_progresso_label(),
                                    True, Tema.get('texto'))
        self.tela.blit(prog, (450, 40))

        self.btn_tema.desenhar(self.tela)

    def desenhar_rodape(self):
        y0 = ALTURA - 100
        pygame.draw.rect(self.tela, Tema.get('painel'), (0, y0, LARGURA, 100))
        titulo = self.f_normal.render("STATUS", True, Tema.get('azul'))
        self.tela.blit(titulo, (20, y0 + 6))

        cx = pygame.Rect(20, y0 + 26, LARGURA - 40, 65)
        pygame.draw.rect(self.tela, Tema.get('console'), cx, border_radius=4)
        pygame.draw.rect(self.tela, Tema.get('suave'), cx, 1, border_radius=4)
        for i, linha in enumerate(self.status_log[-3:]):
            txt = self.f_pequena.render(linha, True, Tema.get('verde'))
            self.tela.blit(txt, (cx.x + 10, cx.y + 6 + i * 19))

    def rect_tab(self, alvo):
        # Layout: [ESTUDO][REVISAO][DASH][PRON][QUIZ][CHAT][GERAR][RELATORIO]
        if alvo == 'estudo':     return pygame.Rect( 30, 100, 110, 32)
        if alvo == 'revisao':    return pygame.Rect(145, 100, 110, 32)
        if alvo == 'dashboard':  return pygame.Rect(260, 100, 110, 32)
        if alvo == 'pronuncia':  return pygame.Rect(375, 100, 110, 32)
        if alvo == 'quiz':       return pygame.Rect(490, 100,  90, 32)
        if alvo == 'chat':       return pygame.Rect(585, 100,  90, 32)
        if alvo == 'gerador':    return pygame.Rect(680, 100, 110, 32)
        if alvo == 'relatorio':  return pygame.Rect(795, 100, 175, 32)
        return None

    def desenhar_nav(self):
        tabs = [
            ('estudo',    "ESTUDO",    'azul'),
            ('revisao',   "REVISAO",   'roxo'),
            ('dashboard', "DASH",      'laranja'),
            ('pronuncia', "PRON",      'verde'),
            ('quiz',      "QUIZ",      'azul'),
            ('chat',      "CHAT IA",   'roxo'),
            ('gerador',   "GERAR IA",  'laranja'),
        ]
        for alvo, txt, cor in tabs:
            ativo = (self.estado == alvo
                     or (alvo == 'estudo' and self.estado == 'frases'))
            c = cor if ativo else 'botao'
            Botao(*self.rect_tab(alvo), texto=txt, cor_bg=c,
                  fonte=self.f_mini).desenhar(self.tela)

        # Botao RELATORIO (acao, nao navegacao)
        Botao(*self.rect_tab('relatorio'), texto="RELATORIO/BACKUP",
              cor_bg='botao', fonte=self.f_mini).desenhar(self.tela)

        if self.estado == 'estudo':
            subt = self.f_sub.render(
                "Escolha uma contracao. IA aprende com seus erros!",
                True, Tema.get('suave'))
            self.tela.blit(subt, (30, 142))

    def mudar_estado(self, novo):
        self.estado = novo
        self.cena_frases = None
        self.cena_quiz = None
        self.cena_revisao = None
        self.cena_dashboard = None
        self.cena_pronuncia = None
        self.cena_chat = None
        self.cena_gerador = None

    def gerar_relatorio_e_backup(self):
        """Chamado quando clica em RELATORIO/BACKUP."""
        if not UTILS_DISPONIVEL:
            self.add_status("utils.py nao carregado.")
            return
        bk = fazer_backup(BASE_DIR, ARQ_PROGRESSO_JSON)
        rel = exportar_relatorio(BASE_DIR, self.progresso, ARQ_PRONUNCIA)
        if bk:
            self.add_status(f"Backup: {os.path.basename(bk)}")
        if rel:
            self.add_status(f"Relatorio: {os.path.basename(rel)}")

    # ---------- LOOP ----------
    def rodar(self):
        rodando = True
        ultimo_check_tema = datetime.now()

        while rodando:
            mouse_pos = pygame.mouse.get_pos()

            # Tema noturno automatico (a cada 60s)
            if (datetime.now() - ultimo_check_tema).seconds > 60:
                if UTILS_DISPONIVEL:
                    if aplicar_tema_noturno_se_necessario(Tema):
                        self.add_status(f"Tema auto: {'escuro' if Tema.escuro else 'claro'}")
                ultimo_check_tema = datetime.now()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    rodando = False
                    continue

                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    if self.estado != 'estudo':
                        self.mudar_estado('estudo')
                        self.add_status("Menu inicial.")
                        continue

                if ev.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                                   pygame.MOUSEMOTION, pygame.MOUSEWHEEL,
                                   pygame.KEYDOWN):
                    continue

                # TEMA
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    self.btn_tema.atualizar(ev.pos)
                    if self.btn_tema.clicou(ev):
                        self.btn_tema.executar()
                        continue

                # NAV
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if self.rect_tab('estudo').collidepoint(ev.pos):
                        self.mudar_estado('estudo'); continue
                    if self.rect_tab('revisao').collidepoint(ev.pos):
                        self.abrir_revisao(); continue
                    if self.rect_tab('dashboard').collidepoint(ev.pos):
                        self.abrir_dashboard(); continue
                    if self.rect_tab('pronuncia').collidepoint(ev.pos):
                        self.abrir_pronuncia(); continue
                    if self.rect_tab('quiz').collidepoint(ev.pos):
                        self.abrir_quiz(); continue
                    if self.rect_tab('chat').collidepoint(ev.pos):
                        self.abrir_chat(); continue
                    if self.rect_tab('gerador').collidepoint(ev.pos):
                        self.abrir_gerador(); continue
                    if self.rect_tab('relatorio').collidepoint(ev.pos):
                        self.gerar_relatorio_e_backup(); continue

                # CENA ATUAL
                if self.estado == 'estudo':
                    if ev.type == pygame.MOUSEBUTTONDOWN:
                        for b in self.botoes_estudo:
                            b.atualizar(ev.pos)
                            if b.clicou(ev):
                                b.executar()
                                break
                elif self.estado == 'frases' and self.cena_frases:
                    self.cena_frases.tratar_evento(ev)
                elif self.estado == 'quiz' and self.cena_quiz:
                    self.cena_quiz.tratar_evento(ev)
                elif self.estado == 'revisao' and self.cena_revisao:
                    self.cena_revisao.tratar_evento(ev)
                elif self.estado == 'dashboard' and self.cena_dashboard:
                    self.cena_dashboard.tratar_evento(ev)
                elif self.estado == 'pronuncia' and self.cena_pronuncia:
                    self.cena_pronuncia.tratar_evento(ev)
                elif self.estado == 'chat' and self.cena_chat:
                    self.cena_chat.tratar_evento(ev)
                elif self.estado == 'gerador' and self.cena_gerador:
                    self.cena_gerador.tratar_evento(ev)

            # ---- DESENHAR ----
            self.tela.fill(Tema.get('fundo'))
            self.desenhar_header()
            self.desenhar_nav()

            if self.estado == 'estudo':
                for b in self.botoes_estudo:
                    b.atualizar(mouse_pos)
                    b.desenhar(self.tela)
            elif self.estado == 'frases' and self.cena_frases:
                self.cena_frases.desenhar(self.tela)
            elif self.estado == 'quiz' and self.cena_quiz:
                self.cena_quiz.desenhar(self.tela)
            elif self.estado == 'revisao' and self.cena_revisao:
                self.cena_revisao.desenhar(self.tela)
            elif self.estado == 'dashboard' and self.cena_dashboard:
                self.cena_dashboard.desenhar(self.tela)
            elif self.estado == 'pronuncia' and self.cena_pronuncia:
                self.cena_pronuncia.desenhar(self.tela)
            elif self.estado == 'chat' and self.cena_chat:
                self.cena_chat.desenhar(self.tela)
            elif self.estado == 'gerador' and self.cena_gerador:
                self.cena_gerador.desenhar(self.tela)

            self.desenhar_rodape()
            pygame.display.flip()
            self.clock.tick(FPS)

        # ---- FECHANDO: backup automatico ----
        salvar_progresso(self.progresso)
        salvar_notas(ARQ_PRONUNCIA, self.notas_pronuncia)
        if UTILS_DISPONIVEL:
            bk = fazer_backup(BASE_DIR, ARQ_PROGRESSO_JSON)
            if bk:
                print(f"[fechando] Backup salvo: {bk}")
        pygame.quit()
        sys.exit()


# ============================================================
# CENA FRASES
# ============================================================
class CenaFrases:
    def __init__(self, jogo, titulo, frases, nome_arq=None):
        self.jogo = jogo
        self.titulo = titulo
        self.frases = frases
        self.nome_arq = nome_arq or titulo
        self.indice = 0
        self.scroll = 0

        f = jogo.f_normal
        self.btn_ouvir    = Botao(320, 600, 290, 44, "Ouvir",
                                  self.ouvir, cor_bg='azul', fonte=f)
        self.btn_devagar  = Botao(320, 650, 290, 44, "Ouvir devagar",
                                  self.ouvir_devagar, cor_bg='azul', fonte=f)
        self.btn_anterior = Botao( 20, 625, 290, 50, "< Anterior",
                                  self.anterior, fonte=f)
        self.btn_proximo  = Botao(690, 625, 290, 50, "Proximo >",
                                  self.proximo, fonte=f)
        self.btn_entendi  = Botao( 20, 555, 145, 60, "ENTENDI",
                                  lambda: self.marcar(True),
                                  cor_bg='verde', fonte=f)
        self.btn_nao_ent  = Botao(175, 555, 145, 60, "NAO ENTENDI",
                                  lambda: self.marcar(False),
                                  cor_bg='vermelho', fonte=f)
        self.btn_voltar   = Botao(620, 600, 360, 44, "VOLTAR AO MENU",
                                  self.voltar, cor_bg='botao', fonte=f)

    def ouvir(self):
        falar(self.frases[self.indice]['ing'], devagar=False)

    def ouvir_devagar(self):
        falar(self.frases[self.indice]['ing'], devagar=True)

    def anterior(self):
        self.indice = (self.indice - 1) % len(self.frases)
        self.scroll_lista()

    def proximo(self):
        self.indice = (self.indice + 1) % len(self.frases)
        self.scroll_lista()

    def marcar(self, acertou):
        f = self.frases[self.indice]
        estado = self.jogo.progresso
        srs_atualizar(estado, f['ing'], acertou)
        est = estatisticas_por_contracao(estado, self.nome_arq)
        if acertou:
            est['acertos'] += 1
            self.jogo.add_status(f"SRS ok: {f['ing'][:30]}")
        else:
            est['erros'] += 1
            self.jogo.add_status(f"SRS errou: {f['ing'][:30]}")
        salvar_progresso(estado)
        self.proximo()

    def scroll_lista(self):
        visiveis = 5
        if self.indice < self.scroll:
            self.scroll = self.indice
        elif self.indice >= self.scroll + visiveis:
            self.scroll = self.indice - visiveis + 1

    def voltar(self):
        self.jogo.estado = 'estudo'
        self.jogo.cena_frases = None
        self.jogo.add_status("Menu de estudo.")

    def desenhar(self, surface):
        f = self.frases[self.indice]
        j = self.jogo

        titulo = j.f_titulo.render(self.titulo, True, Tema.get('azul'))
        surface.blit(titulo, (30, 145))

        srs_info = j.progresso['srs'].get(f['ing'])
        if srs_info:
            prox = srs_info.get('proxima', '?')
            facil = srs_info.get('facilidade', 2.5)
            ac = srs_info.get('acertos', 0)
            er = srs_info.get('erros', 0)
            info = j.f_mini.render(
                f"SRS: acertos={ac} erros={er} facilidade={facil:.1f} proxima={prox}",
                True, Tema.get('roxo'))
            surface.blit(info, (30, 172))

        caixa = pygame.Rect(30, 195, 940, 350)
        pygame.draw.rect(surface, Tema.get('painel'), caixa, border_radius=8)
        pygame.draw.rect(surface, Tema.get('suave'), caixa, 1, border_radius=8)

        ing = j.f_frase.render(f['ing'], True, Tema.get('verde'))
        surface.blit(ing, (caixa.x + 25, caixa.y + 30))

        pygame.draw.line(surface, Tema.get('suave'),
                         (caixa.x + 25, caixa.y + 100),
                         (caixa.right - 25, caixa.y + 100), 1)

        lbl_por = j.f_sub.render("TRADUCAO", True, Tema.get('suave'))
        surface.blit(lbl_por, (caixa.x + 25, caixa.y + 115))
        por = j.f_normal.render(f['por'], True, Tema.get('texto'))
        surface.blit(por, (caixa.x + 25, caixa.y + 140))

        lbl_fon = j.f_sub.render("FONETICA", True, Tema.get('suave'))
        surface.blit(lbl_fon, (caixa.x + 25, caixa.y + 190))
        fon = j.f_normal.render(f['fon'], True, Tema.get('amarelo'))
        surface.blit(fon, (caixa.x + 25, caixa.y + 215))

        cont = j.f_sub.render(
            f"Frase {self.indice + 1} de {len(self.frases)}",
            True, Tema.get('suave'))
        surface.blit(cont, (caixa.x + 25, caixa.bottom - 35))

        area = pygame.Rect(caixa.right - 350, caixa.y + 120, 325, 210)
        pygame.draw.rect(surface, Tema.get('fundo'), area, border_radius=6)
        pygame.draw.rect(surface, Tema.get('suave'), area, 1, border_radius=6)
        old_clip = surface.get_clip()
        surface.set_clip(area)
        visiveis = 5
        for i in range(self.scroll, min(self.scroll + visiveis, len(self.frases))):
            fr = self.frases[i]
            y = area.y + (i - self.scroll) * 40
            destaque = (i == self.indice)
            c = Tema.get('verde') if destaque else Tema.get('suave')
            prefixo = "> " if destaque else "  "
            texto = fr['ing']
            if len(texto) > 38:
                texto = texto[:35] + "..."
            item = j.f_pequena.render(prefixo + texto, True, c)
            surface.blit(item, (area.x + 10, y + 10))
        surface.set_clip(old_clip)

        self.btn_ouvir.desenhar(surface)
        self.btn_devagar.desenhar(surface)
        self.btn_anterior.desenhar(surface)
        self.btn_proximo.desenhar(surface)
        self.btn_entendi.desenhar(surface)
        self.btn_nao_ent.desenhar(surface)
        self.btn_voltar.desenhar(surface)

    def tratar_evento(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key in (pygame.K_SPACE, pygame.K_RETURN): self.ouvir(); return
            if ev.key == pygame.K_d: self.ouvir_devagar(); return
            if ev.key == pygame.K_RIGHT: self.proximo(); return
            if ev.key == pygame.K_LEFT: self.anterior(); return
            if ev.key == pygame.K_1: self.marcar(True); return
            if ev.key == pygame.K_2: self.marcar(False); return
            return
        if ev.type == pygame.MOUSEWHEEL:
            self.scroll -= ev.y
            max_scroll = max(0, len(self.frases) - 5)
            self.scroll = max(0, min(max_scroll, self.scroll))
            return
        if ev.type != pygame.MOUSEBUTTONDOWN:
            return
        for b in (self.btn_ouvir, self.btn_devagar, self.btn_anterior,
                  self.btn_proximo, self.btn_entendi, self.btn_nao_ent,
                  self.btn_voltar):
            b.atualizar(ev.pos)
            if b.clicou(ev):
                b.executar()
                break


# ============================================================
# CENA REVISAO
# ============================================================
class CenaRevisao(CenaFrases):
    def __init__(self, jogo, frases):
        super().__init__(jogo, "REVISAO ESPACADA", frases, nome_arq="revisao")

    def marcar(self, acertou):
        f = self.frases[self.indice]
        srs_atualizar(self.jogo.progresso, f['ing'], acertou)
        salvar_progresso(self.jogo.progresso)
        if acertou:
            self.jogo.add_status(f"OK: {f['ing'][:35]}")
        else:
            self.jogo.add_status(f"ERRO: {f['ing'][:35]}")
        self.frases.pop(self.indice)
        if not self.frases:
            self.jogo.add_status("Revisao concluida!")
            self.voltar()
            return
        if self.indice >= len(self.frases):
            self.indice = 0
        self.scroll_lista()

    def voltar(self):
        self.jogo.estado = 'estudo'
        self.jogo.cena_revisao = None


# ============================================================
# CENA QUIZ
# ============================================================
class CenaQuiz:
    def __init__(self, jogo):
        self.jogo = jogo
        self.perguntas = self.sortear_adaptativo(10)
        self.idx = 0
        self.acertos = 0
        self.erros = 0
        self.respondida = False
        self.escolhida = None
        self.fim = False
        self.nivel = ""
        self.perc = 0
        self.tempo_inicio = datetime.now()
        self.historico_respostas = []

        f = jogo.f_normal
        self.btn_opcoes = [
            Botao(30,  260, 440, 55, "", lambda: self.responder("A"),
                  fonte=f, alinhamento='left'),
            Botao(530, 260, 440, 55, "", lambda: self.responder("B"),
                  fonte=f, alinhamento='left'),
            Botao(30,  330, 440, 55, "", lambda: self.responder("C"),
                  fonte=f, alinhamento='left'),
            Botao(530, 330, 440, 55, "", lambda: self.responder("D"),
                  fonte=f, alinhamento='left'),
        ]
        self.btn_prox = Botao(320, 520, 360, 50, "PROXIMA PERGUNTA",
                              self.proxima, cor_bg='azul', fonte=f)
        self.btn_prox.visivel = False
        self.btn_reiniciar = Botao(200, 520, 280, 50, "JOGAR DE NOVO",
                                   self.reiniciar, cor_bg='verde', fonte=f)
        self.btn_reiniciar.visivel = False
        self.btn_menu = Botao(520, 520, 280, 50, "VOLTAR AO MENU",
                              self.voltar_menu, fonte=f)
        self.btn_menu.visivel = False

    def sortear_adaptativo(self, n):
        estado = self.jogo.progresso
        pesos = []
        for p in PERGUNTAS_QUIZ:
            peso = 1.0
            for frase, info in estado['srs'].items():
                if p['corr'] and p[p['corr']].lower() in frase.lower():
                    peso += info.get('erros', 0) * 2.0
                    peso -= info.get('acertos', 0) * 0.2
            pesos.append(max(0.5, peso))
        escolhidas = []
        pool = list(zip(PERGUNTAS_QUIZ, pesos))
        for _ in range(min(n, len(pool))):
            total = sum(p for _, p in pool)
            r = random.uniform(0, total)
            acumulado = 0
            for i, (perg, peso) in enumerate(pool):
                acumulado += peso
                if r <= acumulado:
                    escolhidas.append(perg)
                    pool.pop(i)
                    break
        return escolhidas

    def responder(self, letra):
        if self.respondida or self.fim:
            return
        p = self.perguntas[self.idx]
        self.escolhida = letra
        self.respondida = True
        acertou = (letra == p['corr'])
        self.historico_respostas.append((p, acertou))
        if acertou:
            self.acertos += 1
            self.jogo.progresso['stats_globais']['acertos'] += 1
            self.jogo.add_status(f"CORRETO ({letra})")
        else:
            self.erros += 1
            self.jogo.progresso['stats_globais']['erros'] += 1
            self.jogo.add_status(f"ERRADO. Correta: {p['corr']}")
        srs_atualizar(self.jogo.progresso, p[p['corr']], acertou)
        salvar_progresso(self.jogo.progresso)
        self.btn_prox.visivel = True

    def proxima(self):
        self.idx += 1
        self.respondida = False
        self.escolhida = None
        self.btn_prox.visivel = False
        if self.idx >= len(self.perguntas):
            self.finalizar()

    def finalizar(self):
        self.fim = True
        self.perc = round(self.acertos * 100 / max(1, len(self.perguntas)))
        if self.perc >= 90:   self.nivel = "EXCELENTE!"
        elif self.perc >= 70: self.nivel = "BOM!"
        elif self.perc >= 50: self.nivel = "EM DESENVOLVIMENTO"
        else:                 self.nivel = "PRECISA ESTUDAR MAIS"
        dur = (datetime.now() - self.tempo_inicio).total_seconds()
        self.jogo.progresso['stats_globais']['tempo_total_seg'] += int(dur)
        self.jogo.add_status(f"Quiz: {self.acertos}/{len(self.perguntas)} ({self.perc}%)")
        salvar_progresso(self.jogo.progresso)
        self.btn_reiniciar.visivel = True
        self.btn_menu.visivel = True

    def reiniciar(self):
        self.__init__(self.jogo)

    def voltar_menu(self):
        self.jogo.estado = 'estudo'
        self.jogo.cena_quiz = None

    def desenhar(self, surface):
        if self.fim:
            self.desenhar_fim(surface)
            return
        p = self.perguntas[self.idx]
        f = self.jogo
        t = f.f_grande.render(
            f"QUIZ - PERGUNTA {self.idx + 1} DE {len(self.perguntas)}",
            True, Tema.get('azul'))
        surface.blit(t, (30, 145))

        box = pygame.Rect(30, 190, 940, 55)
        pygame.draw.rect(surface, Tema.get('painel'), box, border_radius=6)
        pygame.draw.rect(surface, Tema.get('suave'), box, 1, border_radius=6)
        perg = f.f_normal.render(f'"{p["perg"]}"', True, Tema.get('amarelo'))
        surface.blit(perg, (box.x + 15, box.centery - perg.get_height() // 2))

        for i, b in enumerate(self.btn_opcoes):
            letra = "ABCD"[i]
            b.texto = f"{letra})   {p[letra]}"
            b.desenhar(surface)

        if self.respondida:
            correta = p['corr']
            if self.escolhida == correta:
                msg = f"CORRETO ({correta})"; c = Tema.get('verde')
            else:
                msg = f"ERRADO. Correta: {correta}"; c = Tema.get('vermelho')
            fb = f.f_grande.render(msg, True, c)
            surface.blit(fb, (30, 450))
            self.btn_prox.desenhar(surface)

    def desenhar_fim(self, surface):
        f = self.jogo
        titulo = f.f_grande.render("FIM DO QUIZ", True, Tema.get('azul'))
        surface.blit(titulo, (380, 130))
        card = pygame.Rect(200, 190, 600, 300)
        pygame.draw.rect(surface, Tema.get('painel'), card, border_radius=10)
        pygame.draw.rect(surface, Tema.get('suave'), card, 1, border_radius=10)
        linhas = [
            ("Acertos:",        f"{self.acertos} / {len(self.perguntas)}"),
            ("Erros:",          f"{self.erros} / {len(self.perguntas)}"),
            ("Aproveitamento:", f"{self.perc}%"),
            ("Nivel:",          self.nivel),
        ]
        y = card.y + 30
        for rotulo, valor in linhas:
            r = f.f_normal.render(rotulo, True, Tema.get('suave'))
            v = f.f_titulo.render(valor, True, Tema.get('verde'))
            surface.blit(r, (card.x + 40, y))
            surface.blit(v, (card.x + 320, y - 5))
            y += 50
        self.btn_reiniciar.desenhar(surface)
        self.btn_menu.desenhar(surface)

    def tratar_evento(self, ev):
        if ev.type == pygame.KEYDOWN and not self.fim:
            mapa = {pygame.K_a: "A", pygame.K_b: "B",
                    pygame.K_c: "C", pygame.K_d: "D",
                    pygame.K_1: "A", pygame.K_2: "B",
                    pygame.K_3: "C", pygame.K_4: "D"}
            if ev.key in mapa and not self.respondida:
                self.responder(mapa[ev.key]); return
            if ev.key in (pygame.K_RETURN, pygame.K_SPACE) and self.respondida:
                self.proxima(); return
            return
        if ev.type != pygame.MOUSEBUTTONDOWN:
            return
        if self.fim:
            for b in (self.btn_reiniciar, self.btn_menu):
                b.atualizar(ev.pos)
                if b.clicou(ev):
                    b.executar()
            return
        for b in self.btn_opcoes:
            b.atualizar(ev.pos)
            if b.clicou(ev) and not self.respondida:
                b.executar()
                return
        if self.btn_prox.visivel:
            self.btn_prox.atualizar(ev.pos)
            if self.btn_prox.clicou(ev):
                self.btn_prox.executar()


# ============================================================
# CENA DASHBOARD
# ============================================================
class CenaDashboard:
    def __init__(self, jogo):
        self.jogo = jogo
        self.btn_voltar = Botao(30, ALTURA - 130, 200, 40,
                                "< VOLTAR", self.voltar,
                                cor_bg='botao', fonte=jogo.f_normal)
        self.btn_reset = Botao(750, ALTURA - 130, 220, 40,
                               "RESETAR SRS", self.resetar_srs,
                               cor_bg='vermelho', fonte=jogo.f_normal)

    def voltar(self):
        self.jogo.estado = 'estudo'
        self.jogo.cena_dashboard = None

    def resetar_srs(self):
        self.jogo.progresso['srs'] = {}
        self.jogo.progresso['por_contracao'] = {}
        self.jogo.progresso['contracoes_abertas'] = {}
        salvar_progresso(self.jogo.progresso)
        self.jogo.add_status("SRS resetado.")

    def desenhar(self, surface):
        j = self.jogo
        estado = j.progresso
        t = j.f_grande.render("DASHBOARD", True, Tema.get('laranja'))
        surface.blit(t, (30, 145))

        g = estado['stats_globais']
        cards = [
            ("Acertos", g['acertos'], Tema.get('verde')),
            ("Erros", g['erros'], Tema.get('vermelho')),
            ("Estudos", g['estudos'], Tema.get('azul')),
            ("Streak", f"{estado['streak_dias']}d", Tema.get('amarelo')),
        ]
        cx = 30
        for rot, val, cor in cards:
            card = pygame.Rect(cx, 190, 220, 80)
            pygame.draw.rect(surface, Tema.get('painel'), card, border_radius=8)
            pygame.draw.rect(surface, Tema.get('suave'), card, 1, border_radius=8)
            r = j.f_sub.render(rot, True, Tema.get('suave'))
            v = j.f_grande.render(str(val), True, cor)
            surface.blit(r, (card.x + 15, card.y + 10))
            surface.blit(v, (card.x + 15, card.y + 32))
            cx += 240

        y = 300
        titulo = j.f_titulo.render("TOP 5 - Contracoes mais estudadas", True,
                                   Tema.get('roxo'))
        surface.blit(titulo, (30, y))
        y += 35
        abertas = sorted(estado.get('contracoes_abertas', {}).items(),
                         key=lambda x: -x[1])[:5]
        if not abertas:
            msg = j.f_pequena.render("(sem dados)", True, Tema.get('suave'))
            surface.blit(msg, (40, y))
        for nome, qtd in abertas:
            barra_w = min(400, qtd * 30)
            pygame.draw.rect(surface, Tema.get('painel'),
                             (40, y, 400, 22), border_radius=4)
            pygame.draw.rect(surface, Tema.get('roxo'),
                             (40, y, barra_w, 22), border_radius=4)
            txt = j.f_pequena.render(f"{nome}  ({qtd}x)", True, Tema.get('texto'))
            surface.blit(txt, (450, y + 3))
            y += 28

        y += 20
        titulo2 = j.f_titulo.render("TOP 5 - Frases que voce mais erra", True,
                                    Tema.get('vermelho'))
        surface.blit(titulo2, (30, y))
        y += 35
        erros = sorted(
            [(fr, inf) for fr, inf in estado.get('srs', {}).items()
             if inf.get('erros', 0) > 0],
            key=lambda x: -x[1]['erros']
        )[:5]
        if not erros:
            msg = j.f_pequena.render("(nenhum erro! continue assim)",
                                     True, Tema.get('verde'))
            surface.blit(msg, (40, y))
        for fr, inf in erros:
            linha = fr[:55] + ("..." if len(fr) > 55 else "")
            txt = j.f_pequena.render(
                f"{inf['erros']}x  {linha}", True, Tema.get('texto'))
            surface.blit(txt, (40, y))
            y += 22

        y = ALTURA - 210
        pygame.draw.rect(surface, Tema.get('painel'),
                         (30, y, 940, 70), border_radius=8)
        pygame.draw.rect(surface, Tema.get('laranja'),
                         (30, y, 940, 70), 2, border_radius=8)
        sug = self.gerar_sugestao()
        s1 = j.f_normal.render("SUGESTAO DO DIA:", True, Tema.get('laranja'))
        s2 = j.f_pequena.render(sug, True, Tema.get('texto'))
        surface.blit(s1, (50, y + 12))
        surface.blit(s2, (50, y + 38))

        self.btn_voltar.desenhar(surface)
        self.btn_reset.desenhar(surface)

    def gerar_sugestao(self):
        estado = self.jogo.progresso
        erros = [(fr, inf) for fr, inf in estado.get('srs', {}).items()
                 if inf.get('erros', 0) >= 2]
        if erros:
            fr, inf = max(erros, key=lambda x: x[1]['erros'])
            return f"Revise '{fr[:60]}' (errou {inf['erros']}x). Use REVISAO."
        abertas = estado.get('contracoes_abertas', {})
        todas = [c[0] for c in CONTRACOES]
        menos = min(todas, key=lambda c: abertas.get(c, 0))
        if abertas.get(menos, 0) == 0:
            return f"Voce ainda nao abriu '{menos}'."
        vencidas = sum(1 for inf in estado.get('srs', {}).values()
                       if srs_vencida(inf))
        if vencidas > 0:
            return f"{vencidas} frases para revisar. Use REVISAO."
        return "Tudo em dia! Faca um QUIZ ou use o CHAT IA."

    def tratar_evento(self, ev):
        if ev.type != pygame.MOUSEBUTTONDOWN:
            return
        for b in (self.btn_voltar, self.btn_reset):
            b.atualizar(ev.pos)
            if b.clicou(ev):
                b.executar()


# ============================================================
# CENA PRONUNCIA (com LLM explicando erros)
# ============================================================
class CenaPronuncia:
    def __init__(self, jogo, frases, origem="pronuncia"):
        self.jogo = jogo
        self.frases = frases
        self.indice = 0
        self.origem = origem

        self.gravando = False
        self.resultado = None
        self.erro = None
        self.thread_gravacao = None

        # LLM
        self.explicacao_llm = None       # texto
        self.carregando_llm = False
        self.thread_llm = None

        f = jogo.f_normal
        f_mini = jogo.f_mini

        self.btn_ouvir    = Botao(30,  460, 220, 42, "OUVIR (O)",
                                  self.ouvir, cor_bg='azul', fonte=f)
        self.btn_devagar  = Botao(260, 460, 220, 42, "DEVAGAR (D)",
                                  self.ouvir_devagar, cor_bg='azul', fonte=f)
        self.btn_gravar   = Botao(490, 460, 480, 42, "FALAR (ESPACO)",
                                  self.gravar, cor_bg='verde', fonte=f)

        self.btn_anterior = Botao( 30, 510, 300, 40, "< Anterior (LEFT)",
                                  self.anterior, fonte=f)
        self.btn_voltar   = Botao(340, 510, 320, 40, "VOLTAR (ESC)",
                                  self.voltar, cor_bg='botao', fonte=f)
        self.btn_proximo  = Botao(670, 510, 300, 40, "Proximo > (RIGHT)",
                                  self.proximo, fonte=f)

        self.btn_repetir  = Botao( 30, 558, 300, 36, "REPETIR (R)",
                                  self.repetir, cor_bg='laranja', fonte=f_mini)
        self.btn_aleat    = Botao(340, 558, 320, 36, "ALEATORIA",
                                  self.aleatoria, cor_bg='roxo', fonte=f_mini)
        self.btn_explicar = Botao(670, 558, 300, 36, "IA: EXPLICAR ERRO (E)",
                                  self.explicar_llm, cor_bg='azul', fonte=f_mini)

    # ---------- ACOES ----------
    def ouvir(self):
        falar(self.frases[self.indice]['ing'], devagar=False)

    def ouvir_devagar(self):
        falar(self.frases[self.indice]['ing'], devagar=True)

    def gravar(self):
        if self.gravando or not self.jogo.reconhecedor:
            return
        self.gravando = True
        self.resultado = None
        self.erro = None
        self.explicacao_llm = None
        self.jogo.add_status("Gravando... fale!")

        def _run():
            try:
                resp = self.jogo.reconhecedor.ouvir(timeout=6, phrase_limit=8)
                if "erro" in resp:
                    self.erro = resp["erro"]
                    self.jogo.add_status(f"ERRO: {resp['erro']}")
                    return
                esperado = self.frases[self.indice]['ing']
                res = comparar(resp["texto"], esperado)
                acertou = res["nota"] >= 70
                estado = self.jogo.progresso
                srs_atualizar(estado, esperado, acertou)
                est = estatisticas_por_contracao(estado, self.origem)
                if acertou:
                    est['acertos'] += 1
                else:
                    est['erros'] += 1
                salvar_progresso(estado)
                media = registrar_nota(
                    self.jogo.notas_pronuncia, esperado, res["nota"])
                salvar_notas(ARQ_PRONUNCIA, self.jogo.notas_pronuncia)
                res["media_historica"] = media
                res["fonte"] = resp.get("fonte", "?")
                self.resultado = res
                self.jogo.add_status(
                    f"Nota: {res['nota']}% ({resp.get('fonte','?')})")
            except Exception as e:
                self.erro = f"Erro: {e}"
                self.jogo.add_status(f"ERRO: {e}")
            finally:
                self.gravando = False

        self.thread_gravacao = threading.Thread(target=_run, daemon=True)
        self.thread_gravacao.start()

    def explicar_llm(self):
        """Pede ao LLM para explicar o erro da ultima tentativa."""
        if not self.resultado:
            self.jogo.add_status("Grave uma frase primeiro.")
            return
        if not (self.jogo.llm_ok and LLM_DISPONIVEL):
            self.jogo.add_status("LLM indisponivel.")
            return
        if self.carregando_llm:
            return
        self.carregando_llm = True
        self.explicacao_llm = "(pensando...)"
        esperado = self.resultado['esperado']
        falado = self.resultado['falado']
        contracao = self.origem

        def _run():
            try:
                texto, err = llm.explicar_erro(esperado, falado, contracao)
                if err and not texto:
                    self.explicacao_llm = f"(erro LLM: {err})"
                else:
                    self.explicacao_llm = texto
                    self.jogo.add_status("IA explicou seu erro.")
            except Exception as e:
                self.explicacao_llm = f"(erro: {e})"
            finally:
                self.carregando_llm = False

        self.thread_llm = threading.Thread(target=_run, daemon=True)
        self.thread_llm.start()

    def anterior(self):
        self.indice = (self.indice - 1) % len(self.frases)
        self.resultado = None; self.erro = None; self.explicacao_llm = None

    def proximo(self):
        self.indice = (self.indice + 1) % len(self.frases)
        self.resultado = None; self.erro = None; self.explicacao_llm = None

    def repetir(self):
        self.resultado = None; self.erro = None; self.explicacao_llm = None

    def aleatoria(self):
        self.indice = random.randint(0, len(self.frases) - 1)
        self.resultado = None; self.erro = None; self.explicacao_llm = None

    def voltar(self):
        self.jogo.estado = 'estudo'
        self.jogo.cena_pronuncia = None

    # ---------- DESENHO ----------
    def desenhar(self, surface):
        j = self.jogo
        f = self.frases[self.indice]

        titulo = j.f_grande.render("PRONUNCIA + IA", True, Tema.get('verde'))
        surface.blit(titulo, (30, 138))

        # Caixa da frase
        box = pygame.Rect(30, 172, 940, 100)
        pygame.draw.rect(surface, Tema.get('painel'), box, border_radius=8)
        pygame.draw.rect(surface, Tema.get('suave'), box, 1, border_radius=8)
        lbl = j.f_sub.render("FALE ESTA FRASE:", True, Tema.get('suave'))
        surface.blit(lbl, (box.x + 20, box.y + 8))

        y_palavra = box.y + 36
        x_palavra = box.x + 20
        palavras_status = (self.resultado['palavras'] if self.resultado
                           else [{"palavra": p, "status": "neutro"}
                                 for p in f['ing'].split()])
        cores = {
            "ok":       Tema.get('verde'),
            "aprox":    Tema.get('amarelo'),
            "errado":   Tema.get('vermelho'),
            "faltando": Tema.get('vermelho'),
            "neutro":   Tema.get('texto'),
        }
        for item in palavras_status:
            pal = item['palavra']
            cor = cores.get(item['status'], Tema.get('texto'))
            surf = j.f_frase.render(pal + " ", True, cor)
            if x_palavra + surf.get_width() > box.right - 20:
                x_palavra = box.x + 20; y_palavra += 38
            surface.blit(surf, (x_palavra, y_palavra))
            x_palavra += surf.get_width()

        por = j.f_normal.render(f['por'], True, Tema.get('suave'))
        surface.blit(por, (30, 280))
        fon = j.f_normal.render(f['fon'], True, Tema.get('amarelo'))
        surface.blit(fon, (30, 302))
        cont = j.f_pequena.render(f"Frase {self.indice+1}/{len(self.frases)}",
                                  True, Tema.get('suave'))
        surface.blit(cont, (700, 280))

        # Resultado
        res_box = pygame.Rect(30, 328, 940, 120)
        pygame.draw.rect(surface, Tema.get('painel'), res_box, border_radius=8)
        pygame.draw.rect(surface, Tema.get('suave'), res_box, 1, border_radius=8)

        if self.gravando:
            t = j.f_grande.render("GRAVANDO...", True, Tema.get('vermelho'))
            surface.blit(t, (res_box.centerx - t.get_width()//2, res_box.y + 40))
        elif self.erro:
            t = j.f_normal.render(f"Atencao: {self.erro}", True, Tema.get('vermelho'))
            surface.blit(t, (res_box.x + 20, res_box.y + 15))
        elif self.resultado:
            r = self.resultado
            nota = r['nota']
            cor_nota = (Tema.get('verde') if nota >= 80
                        else Tema.get('amarelo') if nota >= 60
                        else Tema.get('vermelho'))
            nota_txt = j.f_grande.render(f"{nota}%", True, cor_nota)
            surface.blit(nota_txt, (res_box.x + 20, res_box.y + 10))

            barra = pygame.Rect(res_box.x + 20, res_box.y + 50, 380, 18)
            pygame.draw.rect(surface, Tema.get('fundo'), barra, border_radius=10)
            prog = pygame.Rect(barra.x, barra.y,
                               int(barra.width * nota / 100), barra.height)
            pygame.draw.rect(surface, cor_nota, prog, border_radius=10)

            fb_txt = ("PERFEITO!" if nota >= 90 else "MUITO BOM!" if nota >= 75
                      else "BOM!" if nota >= 60 else "REGULAR" if nota >= 40
                      else "PRECISA MELHORAR")
            fb = j.f_normal.render(fb_txt, True, cor_nota)
            surface.blit(fb, (res_box.x + 20, res_box.y + 78))

            lbl_eu = j.f_pequena.render("Voce falou:", True, Tema.get('suave'))
            surface.blit(lbl_eu, (res_box.x + 450, res_box.y + 10))
            txt_eu = j.f_normal.render(f'"{r["falado"]}"', True, Tema.get('texto'))
            surface.blit(txt_eu, (res_box.x + 450, res_box.y + 28))
            fonte = j.f_pequena.render(
                f"Backend: {r.get('fonte','?')}", True, Tema.get('suave'))
            surface.blit(fonte, (res_box.x + 450, res_box.y + 55))

            # Explicacao LLM
            if self.explicacao_llm:
                exp_box = pygame.Rect(res_box.x + 450, res_box.y + 78, 480, 34)
                pygame.draw.rect(surface, Tema.get('fundo'), exp_box, border_radius=4)
                pygame.draw.rect(surface, Tema.get('roxo'), exp_box, 1, border_radius=4)
                linhas = self.explicacao_llm.split("\n")[:2]
                for i, linha in enumerate(linhas):
                    t = j.f_mini.render(linha[:70], True, Tema.get('roxo'))
                    surface.blit(t, (exp_box.x + 5, exp_box.y + 3 + i * 15))
        else:
            t = j.f_normal.render(
                'FALAR (ESPACO), depois "IA: EXPLICAR ERRO (E)" se quiser.',
                True, Tema.get('suave'))
            surface.blit(t, (res_box.x + 20, res_box.y + 45))

        # Botoes
        if self.gravando:
            self.btn_gravar.texto = "GRAVANDO..."; self.btn_gravar.cor_bg = 'vermelho'
        else:
            self.btn_gravar.texto = "FALAR (ESPACO)"; self.btn_gravar.cor_bg = 'verde'

        # Habilitar botao explicar apenas com resultado
        self.btn_explicar.habilitado = bool(self.resultado) and self.jogo.llm_ok

        for b in (self.btn_ouvir, self.btn_devagar, self.btn_gravar,
                  self.btn_anterior, self.btn_voltar, self.btn_proximo,
                  self.btn_repetir, self.btn_aleat, self.btn_explicar):
            b.desenhar(surface)

    def tratar_evento(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_SPACE: self.gravar(); return
            if ev.key == pygame.K_o: self.ouvir(); return
            if ev.key == pygame.K_d: self.ouvir_devagar(); return
            if ev.key == pygame.K_RIGHT: self.proximo(); return
            if ev.key == pygame.K_LEFT: self.anterior(); return
            if ev.key == pygame.K_r: self.repetir(); return
            if ev.key == pygame.K_e: self.explicar_llm(); return
            return
        if ev.type != pygame.MOUSEBUTTONDOWN:
            return
        for b in (self.btn_ouvir, self.btn_devagar, self.btn_gravar,
                  self.btn_anterior, self.btn_voltar, self.btn_proximo,
                  self.btn_repetir, self.btn_aleat, self.btn_explicar):
            b.atualizar(ev.pos)
            if b.clicou(ev):
                b.executar()
                break


# ============================================================
# CENA CHAT IA (conversacao livre)
# ============================================================
class CenaChat:
    def __init__(self, jogo):
        self.jogo = jogo
        self.historico = []          # [{'role': 'user'|'assistant', 'content': str}]
        self.entrada = ""
        self.carregando = False
        self.thread_llm = None
        self.scroll = 0

        f = jogo.f_normal
        self.btn_enviar = Botao(800, 630, 170, 40, "ENVIAR (ENTER)",
                                self.enviar, cor_bg='verde', fonte=f)
        self.btn_limpar = Botao(30, 630, 200, 40, "LIMPAR CHAT",
                                self.limpar, cor_bg='vermelho', fonte=jogo.f_mini)
        self.btn_voltar = Botao(600, 630, 180, 40, "VOLTAR (ESC)",
                                self.voltar, cor_bg='botao', fonte=jogo.f_mini)

        # Mensagem inicial do bot
        self.historico.append({
            "role": "assistant",
            "content": "Hey! I'm your English buddy. Wanna chat? "
                       "(Ola! Sou seu amigo de ingles. Quer conversar?)"
        })

    def enviar(self):
        if self.carregando or not self.entrada.strip():
            return
        msg = self.entrada.strip()
        self.entrada = ""
        self.historico.append({"role": "user", "content": msg})
        self.carregando = True
        self.jogo.add_status(f"Voce: {msg[:40]}")

        def _run():
            try:
                texto, err = llm.conversar(self.historico, msg)
                if err and not texto:
                    self.historico.append({
                        "role": "assistant",
                        "content": f"(erro LLM: {err})"
                    })
                else:
                    self.historico.append({
                        "role": "assistant", "content": texto
                    })
                    self.jogo.add_status(f"IA: {texto[:40]}")
            except Exception as e:
                self.historico.append({
                    "role": "assistant", "content": f"(erro: {e})"
                })
            finally:
                self.carregando = False
                self.scroll = 9999

        self.thread_llm = threading.Thread(target=_run, daemon=True)
        self.thread_llm.start()

    def limpar(self):
        self.historico = [{
            "role": "assistant",
            "content": "Chat limpo. Vamos comecar de novo! (Let's start over!)"
        }]
        self.entrada = ""
        self.jogo.add_status("Chat limpo.")

    def voltar(self):
        self.jogo.estado = 'estudo'
        self.jogo.cena_chat = None

    def desenhar(self, surface):
        j = self.jogo
        titulo = j.f_grande.render("CHAT COM IA (conversacao livre)", True,
                                   Tema.get('roxo'))
        surface.blit(titulo, (30, 138))

        # Area do chat
        area = pygame.Rect(30, 175, 940, 440)
        pygame.draw.rect(surface, Tema.get('painel'), area, border_radius=8)
        pygame.draw.rect(surface, Tema.get('suave'), area, 1, border_radius=8)

        # Renderiza mensagens (com quebra de linha)
        y = area.y + 10
        for msg in self.historico:
            is_user = msg['role'] == 'user'
            cor_bg = Tema.get('azul') if is_user else Tema.get('roxo')
            cor_txt = Tema.get('texto')
            prefixo = "Voce: " if is_user else "IA: "

            # quebra em varias linhas de ~90 chars
            texto_completo = prefixo + msg['content']
            linhas = []
            while len(texto_completo) > 90:
                corte = texto_completo[:90].rfind(' ')
                if corte < 20: corte = 90
                linhas.append(texto_completo[:corte])
                texto_completo = texto_completo[corte:].strip()
            linhas.append(texto_completo)

            altura = 20 * len(linhas) + 8
            x_box = area.x + 15 if is_user else area.x + 60
            largura = area.width - 75
            box = pygame.Rect(x_box, y, largura, altura)
            pygame.draw.rect(surface, Tema.get('fundo'), box, border_radius=6)
            pygame.draw.rect(surface, cor_bg, box, 1, border_radius=6)
            for i, linha in enumerate(linhas):
                t = j.f_chat.render(linha, True, cor_txt)
                surface.blit(t, (box.x + 8, box.y + 4 + i * 20))
            y += altura + 6
            if y > area.bottom - 30:
                break

        # Caixa de entrada
        entrada_box = pygame.Rect(30, 630, 760, 40)
        pygame.draw.rect(surface, Tema.get('console'), entrada_box, border_radius=6)
        pygame.draw.rect(surface, Tema.get('suave'), entrada_box, 1, border_radius=6)
        texto_mostrar = self.entrada + ("|" if (pygame.time.get_ticks() // 500) % 2 else "")
        t = j.f_normal.render(texto_mostrar or "Digite em ingles...",
                              True, Tema.get('texto') if self.entrada else Tema.get('suave'))
        surface.blit(t, (entrada_box.x + 10, entrada_box.y + 10))

        if self.carregando:
            t = j.f_mini.render("IA pensando...", True, Tema.get('amarelo'))
            surface.blit(t, (800, 615))

        self.btn_enviar.desenhar(surface)
        self.btn_limpar.desenhar(surface)
        self.btn_voltar.desenhar(surface)

    def tratar_evento(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_RETURN:
                self.enviar(); return
            if ev.key == pygame.K_BACKSPACE:
                self.entrada = self.entrada[:-1]; return
            # Texto simples (sem acentos)
            if ev.unicode and ev.unicode.isprintable() and len(self.entrada) < 120:
                self.entrada += ev.unicode
                return
            return
        if ev.type != pygame.MOUSEBUTTONDOWN:
            return
        for b in (self.btn_enviar, self.btn_limpar, self.btn_voltar):
            b.atualizar(ev.pos)
            if b.clicou(ev):
                b.executar()
                break


# ============================================================
# CENA GERADOR IA (gerar frases novas)
# ============================================================
class CenaGerador:
    def __init__(self, jogo):
        self.jogo = jogo
        self.contracao_idx = 0
        self.geradas = []
        self.carregando = False
        self.thread_llm = None

        f = jogo.f_normal
        self.btn_gerar = Botao(30, 200, 300, 45, "GERAR 5 FRASES (G)",
                               self.gerar, cor_bg='verde', fonte=f)
        self.btn_prox_cont = Botao(345, 200, 300, 45, "TROCAR CONTRACAO (T)",
                                   self.trocar_contracao, cor_bg='azul', fonte=f)
        self.btn_ouvir_todas = Botao(660, 200, 310, 45, "OUVIR TODAS",
                                     self.ouvir_todas, cor_bg='azul', fonte=f)
        self.btn_voltar = Botao(30, 630, 200, 40, "VOLTAR (ESC)",
                                self.voltar, cor_bg='botao', fonte=f)

    def gerar(self):
        if self.carregando:
            return
        self.carregando = True
        self.geradas = []
        contracao = CONTRACOES[self.contracao_idx][0]
        self.jogo.add_status(f"IA gerando frases com '{contracao}'...")

        def _run():
            try:
                frases, err = llm.gerar_frases(contracao, quantidade=5)
                if err and not frases:
                    self.geradas = [{
                        "ing": f"(erro: {err})",
                        "por": "Verifique se o Ollama esta rodando",
                        "fon": "ollama serve"
                    }]
                else:
                    self.geradas = frases
                    self.jogo.add_status(f"IA gerou {len(frases)} frases.")
            except Exception as e:
                self.geradas = [{"ing": f"(erro: {e})", "por": "", "fon": ""}]
            finally:
                self.carregando = False

        self.thread_llm = threading.Thread(target=_run, daemon=True)
        self.thread_llm.start()

    def trocar_contracao(self):
        self.contracao_idx = (self.contracao_idx + 1) % len(CONTRACOES)
        self.geradas = []
        self.jogo.add_status(f"Contracao: {CONTRACOES[self.contracao_idx][0]}")

    def ouvir_todas(self):
        for f in self.geradas:
            falar(f['ing'], devagar=False)

    def voltar(self):
        self.jogo.estado = 'estudo'
        self.jogo.cena_gerador = None

    def desenhar(self, surface):
        j = self.jogo
        titulo = j.f_grande.render("GERADOR DE FRASES COM IA", True,
                                   Tema.get('laranja'))
        surface.blit(titulo, (30, 138))

        contracao = CONTRACOES[self.contracao_idx][0]
        subt = j.f_normal.render(
            f"Contracao atual: {contracao.upper()}    "
            f"(clique em TROCAR para mudar)", True, Tema.get('amarelo'))
        surface.blit(subt, (30, 172))

        # Lista de frases
        area = pygame.Rect(30, 260, 940, 355)
        pygame.draw.rect(surface, Tema.get('painel'), area, border_radius=8)
        pygame.draw.rect(surface, Tema.get('suave'), area, 1, border_radius=8)

        if self.carregando:
            t = j.f_grande.render("IA esta gerando...", True, Tema.get('amarelo'))
            surface.blit(t, (area.centerx - t.get_width()//2, area.centery - 20))
        elif not self.geradas:
            t = j.f_normal.render(
                'Clique em "GERAR 5 FRASES" para comecar.',
                True, Tema.get('suave'))
            surface.blit(t, (area.x + 20, area.y + 20))
        else:
            y = area.y + 15
            for i, f in enumerate(self.geradas[:5]):
                ing = j.f_normal.render(f"{i+1}. {f['ing']}", True, Tema.get('verde'))
                surface.blit(ing, (area.x + 20, y))
                y += 24
                por = j.f_pequena.render(f"   {f['por']}", True, Tema.get('texto'))
                surface.blit(por, (area.x + 20, y))
                y += 20
                fon = j.f_mini.render(f"   [{f['fon']}]", True, Tema.get('amarelo'))
                surface.blit(fon, (area.x + 20, y))
                y += 28

        # Botoes
        self.btn_gerar.desenhar(surface)
        self.btn_prox_cont.desenhar(surface)
        self.btn_ouvir_todas.desenhar(surface)
        self.btn_voltar.desenhar(surface)

    def tratar_evento(self, ev):
        if ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_g: self.gerar(); return
            if ev.key == pygame.K_t: self.trocar_contracao(); return
            return
        if ev.type != pygame.MOUSEBUTTONDOWN:
            return
        for b in (self.btn_gerar, self.btn_prox_cont,
                  self.btn_ouvir_todas, self.btn_voltar):
            b.atualizar(ev.pos)
            if b.clicou(ev):
                b.executar()
                break


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    if not os.path.exists(PASTA_DADOS):
        print(f"AVISO: pasta de dados nao encontrada -> {PASTA_DADOS}")
    jogo = Jogo()
    jogo.rodar()