# ============================================================
#  UTILS - Backup, Relatorio, Tema Noturno
#  SPEAK ENGLISH v4.0
# ============================================================

import os
import json
import shutil
from datetime import datetime, date, timedelta


# ============================================================
# BACKUP AUTOMATICO
# ============================================================
def pasta_backups(base_dir):
    pasta = os.path.join(base_dir, "backups")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def fazer_backup(base_dir, arquivo_progresso):
    """Copia progresso.json para backups/progresso_YYYYMMDD_HHMMSS.json.
    Retorna o caminho do backup ou None se falhar."""
    if not os.path.exists(arquivo_progresso):
        return None
    try:
        pasta = pasta_backups(base_dir)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = os.path.join(pasta, f"progresso_{ts}.json")
        shutil.copy2(arquivo_progresso, destino)
        limpar_backups_antigos(pasta, manter=10)
        return destino
    except Exception as e:
        print(f"Erro no backup: {e}")
        return None


def limpar_backups_antigos(pasta, manter=10):
    """Mantem apenas os N backups mais recentes."""
    try:
        arquivos = [f for f in os.listdir(pasta) if f.startswith("progresso_") and f.endswith(".json")]
        arquivos.sort(reverse=True)
        for antigo in arquivos[manter:]:
            try:
                os.remove(os.path.join(pasta, antigo))
            except Exception:
                pass
    except Exception:
        pass


# ============================================================
# EXPORTAR RELATORIO EM TEXTO
# ============================================================
def exportar_relatorio(base_dir, progresso, arquivo_notas=None):
    """Gera relatorio_YYYYMMDD.txt com estatisticas detalhadas."""
    try:
        pasta = os.path.join(base_dir, "relatorios")
        os.makedirs(pasta, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        caminho = os.path.join(pasta, f"relatorio_{ts}.txt")

        g = progresso.get('stats_globais', {})
        srs = progresso.get('srs', {})
        abertas = progresso.get('contracoes_abertas', {})

        # --- Top 10 frases que mais erra ---
        erros_ordenados = sorted(
            [(fr, inf) for fr, inf in srs.items() if inf.get('erros', 0) > 0],
            key=lambda x: -x[1]['erros']
        )[:10]

        # --- Top 10 frases com melhor desempenho ---
        acertos_ordenados = sorted(
            [(fr, inf) for fr, inf in srs.items() if inf.get('acertos', 0) > 0],
            key=lambda x: -x[1]['acertos']
        )[:10]

        # --- Contracoes mais estudadas ---
        contracao_ord = sorted(abertas.items(), key=lambda x: -x[1])

        # --- Frases para revisar hoje ---
        hoje = date.today()
        vencidas = []
        for fr, inf in srs.items():
            try:
                prox = date.fromisoformat(inf.get('proxima', ''))
                if prox <= hoje:
                    vencidas.append((fr, inf))
            except Exception:
                vencidas.append((fr, inf))

        # --- Notas de pronuncia ---
        notas = {}
        if arquivo_notas and os.path.exists(arquivo_notas):
            try:
                with open(arquivo_notas, encoding='utf-8') as f:
                    notas = json.load(f)
            except Exception:
                pass
        notas_ordenadas = sorted(
            notas.items(),
            key=lambda x: x[1].get('media', 0),
            reverse=True
        )

        # --- Escrever arquivo ---
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("        SPEAK ENGLISH - RELATORIO DE PROGRESSO\n")
            f.write("=" * 70 + "\n")
            f.write(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

            # ----- GLOBAIS -----
            f.write("--- ESTATISTICAS GLOBAIS ---\n")
            f.write(f"  Acertos         : {g.get('acertos', 0)}\n")
            f.write(f"  Erros           : {g.get('erros', 0)}\n")
            f.write(f"  Estudos         : {g.get('estudos', 0)}\n")
            f.write(f"  Streak          : {progresso.get('streak_dias', 0)} dias\n")
            tempo = g.get('tempo_total_seg', 0)
            f.write(f"  Tempo total     : {tempo // 60} min {tempo % 60} s\n")
            total = g.get('acertos', 0) + g.get('erros', 0)
            if total > 0:
                f.write(f"  Aproveitamento  : {round(g['acertos'] * 100 / total, 1)}%\n")
            f.write(f"  Frases no SRS   : {len(srs)}\n\n")

            # ----- TOP 10 ERROS -----
            f.write("--- TOP 10 FRASES QUE VOCE MAIS ERRA ---\n")
            if not erros_ordenados:
                f.write("  (nenhum erro registrado - PARABENS!)\n")
            for i, (fr, inf) in enumerate(erros_ordenados, 1):
                f.write(f"  {i:2}. [{inf['erros']}x] {fr}\n")
            f.write("\n")

            # ----- TOP 10 ACERTOS -----
            f.write("--- TOP 10 FRASES QUE VOCE DOMINA ---\n")
            if not acertos_ordenados:
                f.write("  (estude mais para ver dados)\n")
            for i, (fr, inf) in enumerate(acertos_ordenados, 1):
                f.write(f"  {i:2}. [{inf['acertos']}x] {fr}\n")
            f.write("\n")

            # ----- REVISAO PENDENTE -----
            f.write(f"--- FRASES PARA REVISAR HOJE ({len(vencidas)}) ---\n")
            if not vencidas:
                f.write("  (nada pendente - tudo em dia!)\n")
            for fr, inf in vencidas[:20]:
                f.write(f"  - {fr}\n")
            if len(vencidas) > 20:
                f.write(f"  ... e mais {len(vencidas) - 20} frases\n")
            f.write("\n")

            # ----- CONTRACOES -----
            f.write("--- CONTRACOES MAIS ESTUDADAS ---\n")
            if not contracao_ord:
                f.write("  (sem dados)\n")
            for nome, qtd in contracao_ord[:15]:
                f.write(f"  {nome:15} {qtd}x\n")
            f.write("\n")

            # ----- NOTAS DE PRONUNCIA -----
            f.write("--- NOTAS DE PRONUNCIA (media) ---\n")
            if not notas_ordenadas:
                f.write("  (sem dados - use a aba PRONUNCIA)\n")
            for fr, info in notas_ordenadas[:15]:
                media = info.get('media', 0)
                tent = info.get('tentativas', 0)
                f.write(f"  {media:5.1f}%  ({tent}x)  {fr}\n")
            f.write("\n")

            # ----- EVOLUCAO (por dia) -----
            f.write("--- EVOLUCAO POR DIA (SRS) ---\n")
            dias = {}
            for fr, inf in srs.items():
                dia = inf.get('ultima', '?')
                if dia and dia != '?':
                    dias[dia] = dias.get(dia, 0) + 1
            for dia in sorted(dias.keys()):
                f.write(f"  {dia}: {dias[dia]} frases estudadas\n")
            f.write("\n")

            f.write("=" * 70 + "\n")
            f.write("Fim do relatorio.\n")
            f.write("=" * 70 + "\n")

        return caminho
    except Exception as e:
        print(f"Erro ao exportar relatorio: {e}")
        return None


# ============================================================
# MODO NOTURNO AUTOMATICO
# ============================================================
def hora_para_tema_noturno():
    """True se for noite (18h as 6h)."""
    h = datetime.now().hour
    return h >= 18 or h < 6


def aplicar_tema_noturno_se_necessario(tema_class):
    """Ajusta o tema baseado na hora, so se o usuario nao tiver
    mexido manualmente. Retorna True se mudou."""
    deve_ser_escuro = hora_para_tema_noturno()
    if tema_class.escuro != deve_ser_escuro:
        tema_class.escuro = deve_ser_escuro
        return True
    return False