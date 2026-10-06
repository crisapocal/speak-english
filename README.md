# 🎓 SPEAK ENGLISH - Curso de Inglês com IA Local

Curso completo de inglês informal focado em contrações (gonna, wanna, gotta, ain't) com IA local offline, reconhecimento de voz e quiz adaptativo.

## ✨ Funcionalidades

- 📚 **21 contrações** (gotta, gonna, wanna, gimme, lemme, kinda, sorta, outta, hafta, shoulda, coulda, woulda, musta, ain't, don'tcha, c'mon, gotcha, betcha, dunno, imma, modais)
- 🧠 **SRS (Repetição Espaçada)** — o bot lembra o que você erra e revisa
- 📈 **Quiz Adaptativo** — perguntas com peso baseado nos seus erros
- 🎤 **Reconhecimento de Voz** — nota de pronúncia de 0-100% com destaque por palavra
- 🔊 **Text-to-Speech** — ouça frases em velocidade normal e devagar
- 🤖 **IA Local (Llama 3.2)** — explica erros, gera frases novas e conversa livremente
- 📊 **Dashboard** — top erros, sugestão do dia, streak de dias consecutivos
- 💾 **Backup automático** e **relatórios em texto**
- 🌙 **Tema noturno automático**
- ⌨️ **Atalhos de teclado** completos

## 🖼️ Screenshots

![Menu Principal](screenshots/menu.png)
![Prática de Pronúncia](screenshots/pronuncia.png)
![Chat com IA](screenshots/chat.png)

## 🚀 Instalação

### Requisitos
- Python 3.10+
- Ollama (para a IA local): https://ollama.com

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/SEU-USUARIO/speak-english.git
cd speak-english

# 2. Instale as dependências
pip install pygame pyttsx3 SpeechRecognition pyaudio requests

# 3. Baixe o modelo de IA local
ollama pull llama3.2:1b

# 4. Rode o bot
python main.py
