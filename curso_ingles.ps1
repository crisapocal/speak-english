# ============================================================
#  CURSO DE INGLES - INTERFACE GRAFICA v1.0
#  Baseado no Painel de Manutencao do Windows
# ============================================================

# Forca DPI awareness
try {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public class DPIHelper {
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
"@
    [DPIHelper]::SetProcessDPIAware() | Out-Null
} catch {}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Speech
[System.Windows.Forms.Application]::EnableVisualStyles()

# ---------- CAMINHOS ----------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pastaDados = Join-Path $scriptDir "dados"
$arqProgresso = Join-Path $scriptDir "progresso.txt"

if (-not (Test-Path $pastaDados)) { New-Item -ItemType Directory -Path $pastaDados | Out-Null }

# ---------- ESTADO ----------
$script:temaEscuro = $true
$script:acertos = 0
$script:erros = 0
$script:estudos = 0
$script:frasesAtuais = @()
$script:indiceFrase = 0

if (Test-Path $arqProgresso) {
    Get-Content $arqProgresso | ForEach-Object {
        if ($_ -match "^ACERTOS=(\d+)") { $script:acertos = [int]$matches[1] }
        if ($_ -match "^ERROS=(\d+)")   { $script:erros   = [int]$matches[1] }
        if ($_ -match "^ESTUDOS=(\d+)") { $script:estudos = [int]$matches[1] }
    }
}

function Save-Progresso {
    @(
        "ACERTOS=$script:acertos",
        "ERROS=$script:erros",
        "ESTUDOS=$script:estudos"
    ) | Out-File $arqProgresso -Encoding UTF8
}

# ---------- CORES ----------
function Get-Cor {
    param([string]$nome)
    if ($script:temaEscuro) {
        switch ($nome) {
            "Fundo"        { [System.Drawing.Color]::FromArgb(30, 30, 40) }
            "Painel"       { [System.Drawing.Color]::FromArgb(40, 42, 54) }
            "Header"       { [System.Drawing.Color]::FromArgb(20, 22, 30) }
            "Botao"        { [System.Drawing.Color]::FromArgb(75, 78, 100) }
            "BotaoHover"   { [System.Drawing.Color]::FromArgb(100, 105, 130) }
            "BotaoVerde"   { [System.Drawing.Color]::FromArgb(40, 140, 80) }
            "BotaoVerm"    { [System.Drawing.Color]::FromArgb(170, 55, 55) }
            "BotaoAzul"    { [System.Drawing.Color]::FromArgb(50, 110, 180) }
            "Verde"        { [System.Drawing.Color]::FromArgb(80, 200, 120) }
            "Azul"         { [System.Drawing.Color]::FromArgb(80, 160, 240) }
            "Vermelho"     { [System.Drawing.Color]::FromArgb(220, 80, 80) }
            "Amarelo"      { [System.Drawing.Color]::FromArgb(240, 190, 80) }
            "Texto"        { [System.Drawing.Color]::White }
            "TextoSuave"   { [System.Drawing.Color]::FromArgb(180, 180, 200) }
            "Console"      { [System.Drawing.Color]::FromArgb(15, 15, 20) }
            "ConsoleTexto" { [System.Drawing.Color]::FromArgb(180, 220, 180) }
            "GridLine"     { [System.Drawing.Color]::FromArgb(60, 62, 80) }
            default        { [System.Drawing.Color]::White }
        }
    } else {
        switch ($nome) {
            "Fundo"        { [System.Drawing.Color]::FromArgb(245, 246, 250) }
            "Painel"       { [System.Drawing.Color]::FromArgb(255, 255, 255) }
            "Header"       { [System.Drawing.Color]::FromArgb(230, 232, 240) }
            "Botao"        { [System.Drawing.Color]::FromArgb(230, 233, 240) }
            "BotaoHover"   { [System.Drawing.Color]::FromArgb(205, 212, 225) }
            "BotaoVerde"   { [System.Drawing.Color]::FromArgb(70, 180, 110) }
            "BotaoVerm"    { [System.Drawing.Color]::FromArgb(220, 100, 100) }
            "BotaoAzul"    { [System.Drawing.Color]::FromArgb(90, 150, 220) }
            "Verde"        { [System.Drawing.Color]::FromArgb(40, 160, 90) }
            "Azul"         { [System.Drawing.Color]::FromArgb(50, 120, 210) }
            "Vermelho"     { [System.Drawing.Color]::FromArgb(200, 60, 60) }
            "Amarelo"      { [System.Drawing.Color]::FromArgb(180, 130, 20) }
            "Texto"        { [System.Drawing.Color]::FromArgb(30, 30, 40) }
            "TextoSuave"   { [System.Drawing.Color]::FromArgb(90, 90, 110) }
            "Console"      { [System.Drawing.Color]::FromArgb(250, 250, 252) }
            "ConsoleTexto" { [System.Drawing.Color]::FromArgb(20, 80, 40) }
            "GridLine"     { [System.Drawing.Color]::FromArgb(210, 215, 225) }
            default        { [System.Drawing.Color]::Black }
        }
    }
}

# ---------- FONTES ----------
$fontePadrao = New-Object System.Drawing.Font("Segoe UI", 9)
$fonteTitulo = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$fonteGrande = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fonteMono   = New-Object System.Drawing.Font("Consolas", 9)

# ---------- TTS ----------
function Falar {
    param([string]$texto, [int]$rate = 0)
    try {
        $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
        $s.Rate = $rate
        $s.Volume = 100
        try { $s.SelectVoiceByHints("NotSet", "NotSet", 0, [System.Globalization.CultureInfo]::GetCultureInfo('en-US')) } catch {}
        $s.Speak($texto)
        $s.Dispose()
    } catch {}
}

# ============================================================
# JANELA PRINCIPAL
# ============================================================
$form = New-Object System.Windows.Forms.Form
$form.Text = "Curso de Ingles - SPEAK ENGLISH"
$form.ClientSize = New-Object System.Drawing.Size(1000, 780)
$form.StartPosition = "CenterScreen"
$form.BackColor = Get-Cor "Fundo"
$form.ForeColor = Get-Cor "Texto"
$form.Font = $fontePadrao
$form.FormBorderStyle = "FixedSingle"
$form.MaximizeBox = $false

# ---------- HEADER ----------
$header = New-Object System.Windows.Forms.Panel
$header.Size = New-Object System.Drawing.Size(1000, 130)
$header.Location = New-Object System.Drawing.Point(0, 0)
$header.BackColor = Get-Cor "Header"
$form.Controls.Add($header)

$titulo = New-Object System.Windows.Forms.Label
$titulo.Text = "SPEAK ENGLISH"
$titulo.Font = $fonteGrande
$titulo.ForeColor = Get-Cor "Verde"
$titulo.BackColor = [System.Drawing.Color]::Transparent
$titulo.Location = New-Object System.Drawing.Point(25, 20)
$titulo.AutoSize = $true
$header.Controls.Add($titulo)

$subtitulo = New-Object System.Windows.Forms.Label
$subtitulo.Text = "Contracoes  |  Modais  |  Quiz  |  Pronuncia"
$subtitulo.ForeColor = Get-Cor "TextoSuave"
$subtitulo.BackColor = [System.Drawing.Color]::Transparent
$subtitulo.Location = New-Object System.Drawing.Point(27, 50)
$subtitulo.AutoSize = $true
$header.Controls.Add($subtitulo)

$lblProgresso = New-Object System.Windows.Forms.Label
$lblProgresso.Font = $fonteTitulo
$lblProgresso.Location = New-Object System.Drawing.Point(600, 22)
$lblProgresso.Size = New-Object System.Drawing.Size(280, 25)
$lblProgresso.TextAlign = "MiddleRight"
$lblProgresso.BackColor = [System.Drawing.Color]::Transparent
$header.Controls.Add($lblProgresso)

$btnTema = New-Object System.Windows.Forms.Button
$btnTema.Text = "TEMA"
$btnTema.Font = $fonteTitulo
$btnTema.Size = New-Object System.Drawing.Size(80, 34)
$btnTema.Location = New-Object System.Drawing.Point(890, 15)
$btnTema.FlatStyle = "Flat"
$btnTema.FlatAppearance.BorderSize = 1
$btnTema.FlatAppearance.BorderColor = Get-Cor "TextoSuave"
$btnTema.BackColor = Get-Cor "Botao"
$btnTema.ForeColor = Get-Cor "Texto"
$btnTema.Cursor = "Hand"
$btnTema.FlatAppearance.MouseOverBackColor = Get-Cor "BotaoHover"
$header.Controls.Add($btnTema)

function Update-ProgressoLabel {
    $lblProgresso.Text = "Acertos: $script:acertos   Erros: $script:erros   Estudos: $script:estudos"
}
Update-ProgressoLabel

# ---------- PAINEL DE GRAFICOS ----------
$panelGraficos = New-Object System.Windows.Forms.Panel
$panelGraficos.Location = New-Object System.Drawing.Point(0, 130)
$panelGraficos.Size = New-Object System.Drawing.Size(1000, 100)
$panelGraficos.BackColor = Get-Cor "Painel"
$form.Controls.Add($panelGraficos)

function New-GaugeBlock {
    param([string]$icone, [string]$nome, [int]$x)
    $lblIcone = New-Object System.Windows.Forms.Label
    $lblIcone.Text = $icone
    $lblIcone.Font = $fonteTitulo
    $lblIcone.ForeColor = Get-Cor "Azul"
    $lblIcone.BackColor = [System.Drawing.Color]::Transparent
    $lblIcone.Location = New-Object System.Drawing.Point($x, 25)
    $lblIcone.Size = New-Object System.Drawing.Size(40, 20)
    $panelGraficos.Controls.Add($lblIcone)

    $lblNome = New-Object System.Windows.Forms.Label
    $lblNome.Text = $nome
    $lblNome.Font = $fonteTitulo
    $lblNome.ForeColor = Get-Cor "Texto"
    $lblNome.BackColor = [System.Drawing.Color]::Transparent
    $lblNome.Location = New-Object System.Drawing.Point(($x + 45), 12)
    $lblNome.AutoSize = $true
    $panelGraficos.Controls.Add($lblNome)

    $lblValor = New-Object System.Windows.Forms.Label
    $lblValor.Text = "--"
    $lblValor.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
    $lblValor.BackColor = [System.Drawing.Color]::Transparent
    $lblValor.Location = New-Object System.Drawing.Point(($x + 45), 34)
    $lblValor.AutoSize = $true
    $panelGraficos.Controls.Add($lblValor)

    $barra = New-Object System.Windows.Forms.ProgressBar
    $barra.Location = New-Object System.Drawing.Point(($x + 45), 70)
    $barra.Size = New-Object System.Drawing.Size(230, 14)
    $barra.Minimum = 0
    $barra.Maximum = 100
    $barra.Style = "Continuous"
    $panelGraficos.Controls.Add($barra)

    return @{ Valor = $lblValor; Barra = $barra }
}

$gaugeContracoes = New-GaugeBlock "ABC" "Contracoes" 30
$gaugeModais     = New-GaugeBlock "MOD" "Modais"     350
$gaugeQuiz       = New-GaugeBlock "QZ"  "Quiz"       670

$gaugeContracoes.Valor.Text = "20"
$gaugeContracoes.Barra.Value = 100
$gaugeContracoes.Valor.ForeColor = Get-Cor "Verde"
$gaugeModais.Valor.Text = "8"
$gaugeModais.Barra.Value = 100
$gaugeModais.Valor.ForeColor = Get-Cor "Verde"
$gaugeQuiz.Valor.Text = "30"
$gaugeQuiz.Barra.Value = 100
$gaugeQuiz.Valor.ForeColor = Get-Cor "Verde"

# ---------- TABS ----------
$tabs = New-Object System.Windows.Forms.TabControl
$tabs.Location = New-Object System.Drawing.Point(15, 240)
$tabs.Size = New-Object System.Drawing.Size(970, 390)
$tabs.Font = $fontePadrao
$form.Controls.Add($tabs)

$tabEstudo = New-Object System.Windows.Forms.TabPage
$tabEstudo.Text = "  Estudo  "
$tabEstudo.BackColor = Get-Cor "Fundo"
$tabEstudo.ForeColor = Get-Cor "Texto"
$tabEstudo.UseVisualStyleBackColor = $false
$tabs.Controls.Add($tabEstudo)

$tabFrases = New-Object System.Windows.Forms.TabPage
$tabFrases.Text = "  Frases  "
$tabFrases.BackColor = Get-Cor "Fundo"
$tabFrases.ForeColor = Get-Cor "Texto"
$tabFrases.UseVisualStyleBackColor = $false
$tabs.Controls.Add($tabFrases)

$tabQuiz = New-Object System.Windows.Forms.TabPage
$tabQuiz.Text = "  Quiz  "
$tabQuiz.BackColor = Get-Cor "Fundo"
$tabQuiz.ForeColor = Get-Cor "Texto"
$tabQuiz.UseVisualStyleBackColor = $false
$tabs.Controls.Add($tabQuiz)

# ============================================================
# HELPERS
# ============================================================
function New-MenuButton {
    param([string]$texto, [int]$x, [int]$y, [System.Windows.Forms.Control]$parent, [string]$estilo = "normal")
    $corFundo = switch ($estilo) {
        "verde" { Get-Cor "BotaoVerde" }
        "verm"  { Get-Cor "BotaoVerm" }
        "azul"  { Get-Cor "BotaoAzul" }
        default { Get-Cor "Botao" }
    }
    $btn = New-Object System.Windows.Forms.Button
    $btn.Text = $texto
    $btn.Size = New-Object System.Drawing.Size(295, 40)
    $btn.Location = New-Object System.Drawing.Point($x, $y)
    $btn.FlatStyle = "Flat"
    $btn.FlatAppearance.BorderSize = 1
    $btn.FlatAppearance.BorderColor = Get-Cor "TextoSuave"
    $btn.BackColor = $corFundo
    $btn.ForeColor = Get-Cor "Texto"
    $btn.Font = $fontePadrao
    $btn.TextAlign = "MiddleLeft"
    $btn.Padding = New-Object System.Windows.Forms.Padding(15, 0, 0, 0)
    $btn.Cursor = "Hand"
    $btn.FlatAppearance.MouseOverBackColor = Get-Cor "BotaoHover"
    $btn.UseVisualStyleBackColor = $false
    $btn.Tag = $estilo
    $parent.Controls.Add($btn)
    return $btn
}

function New-CatLabel {
    param([string]$texto, [int]$x, [int]$y, [System.Windows.Forms.Control]$parent)
    $lbl = New-Object System.Windows.Forms.Label
    $lbl.Text = $texto
    $lbl.Font = $fonteTitulo
    $lbl.ForeColor = Get-Cor "Amarelo"
    $lbl.BackColor = [System.Drawing.Color]::Transparent
    $lbl.Location = New-Object System.Drawing.Point($x, $y)
    $lbl.AutoSize = $true
    $parent.Controls.Add($lbl)
    return $lbl
}

# ============================================================
# ABA ESTUDO - CONTEUDO
# ============================================================
New-CatLabel "[ CONTRACOES ]"  15  10 $tabEstudo | Out-Null
New-CatLabel "[ MODAIS ]"      320 10 $tabEstudo | Out-Null
New-CatLabel "[ PRATICA ]"     625 10 $tabEstudo | Out-Null

$btnGotta   = New-MenuButton "GOTTA    (ter que)"         15  38  $tabEstudo
$btnGonna   = New-MenuButton "GONNA    (futuro)"          15  84  $tabEstudo
$btnWanna   = New-MenuButton "WANNA    (querer)"          15  130 $tabEstudo
$btnGimme   = New-MenuButton "GIMME    (me de)"           15  176 $tabEstudo
$btnLemme   = New-MenuButton "LEMME    (deixa eu)"        15  222 $tabEstudo
$btnKinda   = New-MenuButton "KINDA    (meio que)"        15  268 $tabEstudo
$btnSorta   = New-MenuButton "SORTA    (meio que)"        15  314 $tabEstudo
$btnOutta   = New-MenuButton "OUTTA    (fora/sem)"        15  360 $tabEstudo

$btnHafta   = New-MenuButton "HAFTA    (ter que)"         320 38  $tabEstudo
$btnShoulda = New-MenuButton "SHOULDA  (deveria ter)"     320 84  $tabEstudo
$btnCoulda  = New-MenuButton "COULDA   (poderia ter)"     320 130 $tabEstudo
$btnWoulda  = New-MenuButton "WOULDA   (teria)"           320 176 $tabEstudo
$btnMusta   = New-MenuButton "MUSTA    (deve ter)"        320 222 $tabEstudo
$btnAint    = New-MenuButton "AIN'T    (negacao)"         320 268 $tabEstudo
$btnDontcha = New-MenuButton "DON'TCHA (voce nao)"        320 314 $tabEstudo
$btnCmon    = New-MenuButton "C'MON    (vamos)"           320 360 $tabEstudo

$btnModais     = New-MenuButton "VERBOS MODAIS"           625 38  $tabEstudo "azul"
$btnPronuncia  = New-MenuButton "PRATICA DE PRONUNCIA"    625 84  $tabEstudo "azul"
$btnOuvirTodas = New-MenuButton "OUVIR TODAS"             625 130 $tabEstudo "azul"
$btnGotcha     = New-MenuButton "GOTCHA   (te peguei)"    625 176 $tabEstudo
$btnBetcha     = New-MenuButton "BETCHA   (aposto que)"   625 222 $tabEstudo
$btnDunno      = New-MenuButton "DUNNO    (nao sei)"      625 268 $tabEstudo
$btnImma       = New-MenuButton "I'MMA    (eu vou)"       625 314 $tabEstudo

# ============================================================
# ABA FRASES - CONTEUDO
# ============================================================
$lblFraseTitulo = New-Object System.Windows.Forms.Label
$lblFraseTitulo.Text = "Escolha uma contração na aba ESTUDO"
$lblFraseTitulo.Font = $fonteTitulo
$lblFraseTitulo.ForeColor = Get-Cor "Azul"
$lblFraseTitulo.BackColor = [System.Drawing.Color]::Transparent
$lblFraseTitulo.Location = New-Object System.Drawing.Point(15, 10)
$lblFraseTitulo.AutoSize = $true
$tabFrases.Controls.Add($lblFraseTitulo)

$lblIngles = New-Object System.Windows.Forms.Label
$lblIngles.Font = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)
$lblIngles.ForeColor = Get-Cor "Verde"
$lblIngles.BackColor = [System.Drawing.Color]::Transparent
$lblIngles.Location = New-Object System.Drawing.Point(15, 50)
$lblIngles.Size = New-Object System.Drawing.Size(925, 50)
$tabFrases.Controls.Add($lblIngles)

$lblPortugues = New-Object System.Windows.Forms.Label
$lblPortugues.Font = New-Object System.Drawing.Font("Segoe UI", 12)
$lblPortugues.ForeColor = Get-Cor "Texto"
$lblPortugues.BackColor = [System.Drawing.Color]::Transparent
$lblPortugues.Location = New-Object System.Drawing.Point(15, 110)
$lblPortugues.Size = New-Object System.Drawing.Size(925, 35)
$tabFrases.Controls.Add($lblPortugues)

$lblFonetica = New-Object System.Windows.Forms.Label
$lblFonetica.Font = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Italic)
$lblFonetica.ForeColor = Get-Cor "Amarelo"
$lblFonetica.BackColor = [System.Drawing.Color]::Transparent
$lblFonetica.Location = New-Object System.Drawing.Point(15, 150)
$lblFonetica.Size = New-Object System.Drawing.Size(925, 30)
$tabFrases.Controls.Add($lblFonetica)

$lblContador = New-Object System.Windows.Forms.Label
$lblContador.Font = $fonteTitulo
$lblContador.ForeColor = Get-Cor "TextoSuave"
$lblContador.BackColor = [System.Drawing.Color]::Transparent
$lblContador.Location = New-Object System.Drawing.Point(15, 190)
$lblContador.AutoSize = $true
$tabFrases.Controls.Add($lblContador)

$btnAnterior = New-MenuButton "< Anterior"    15  230 $tabFrases
$btnOuvir    = New-MenuButton "Ouvir"          320 230 $tabFrases "azul"
$btnOuvirDev = New-MenuButton "Ouvir devagar"  320 276 $tabFrases "azul"
$btnProximo  = New-MenuButton "Proximo >"      625 230 $tabFrases

$btnAnterior.Size = New-Object System.Drawing.Size(295, 50)
$btnOuvir.Size = New-Object System.Drawing.Size(295, 40)
$btnOuvirDev.Size = New-Object System.Drawing.Size(295, 40)
$btnProximo.Size = New-Object System.Drawing.Size(295, 50)

# ============================================================
# ABA QUIZ - CONTEUDO
# ============================================================
$lblQuizTitulo = New-Object System.Windows.Forms.Label
$lblQuizTitulo.Text = "QUIZ - 10 perguntas aleatorias de 30"
$lblQuizTitulo.Font = $fonteGrande
$lblQuizTitulo.ForeColor = Get-Cor "Azul"
$lblQuizTitulo.BackColor = [System.Drawing.Color]::Transparent
$lblQuizTitulo.Location = New-Object System.Drawing.Point(15, 15)
$lblQuizTitulo.AutoSize = $true
$tabQuiz.Controls.Add($lblQuizTitulo)

$lblQuizPergunta = New-Object System.Windows.Forms.Label
$lblQuizPergunta.Font = New-Object System.Drawing.Font("Segoe UI", 13, [System.Drawing.FontStyle]::Bold)
$lblQuizPergunta.ForeColor = Get-Cor "Amarelo"
$lblQuizPergunta.BackColor = [System.Drawing.Color]::Transparent
$lblQuizPergunta.Location = New-Object System.Drawing.Point(15, 60)
$lblQuizPergunta.Size = New-Object System.Drawing.Size(925, 40)
$tabQuiz.Controls.Add($lblQuizPergunta)

$lblQuizNum = New-Object System.Windows.Forms.Label
$lblQuizNum.Font = $fonteTitulo
$lblQuizNum.ForeColor = Get-Cor "TextoSuave"
$lblQuizNum.BackColor = [System.Drawing.Color]::Transparent
$lblQuizNum.Location = New-Object System.Drawing.Point(15, 100)
$lblQuizNum.AutoSize = $true
$tabQuiz.Controls.Add($lblQuizNum)

$btnQuizA = New-MenuButton "A" 15  140 $tabQuiz
$btnQuizB = New-MenuButton "B" 320 140 $tabQuiz
$btnQuizC = New-MenuButton "C" 625 140 $tabQuiz
$btnQuizD = New-MenuButton "D" 15  190 $tabQuiz

$btnQuizA.Size = New-Object System.Drawing.Size(295, 40)
$btnQuizB.Size = New-Object System.Drawing.Size(295, 40)
$btnQuizC.Size = New-Object System.Drawing.Size(295, 40)
$btnQuizD.Size = New-Object System.Drawing.Size(295, 40)

$btnIniciarQuiz = New-MenuButton "INICIAR QUIZ" 320 190 $tabQuiz "verde"
$btnIniciarQuiz.Size = New-Object System.Drawing.Size(600, 40)

$btnQuizProx = New-MenuButton "PROXIMA PERGUNTA" 320 190 $tabQuiz "azul"
$btnQuizProx.Size = New-Object System.Drawing.Size(600, 40)
$btnQuizProx.Visible = $false

# ============================================================
# RODAPE
# ============================================================
$panelRodape = New-Object System.Windows.Forms.Panel
$panelRodape.Location = New-Object System.Drawing.Point(0, 645)
$panelRodape.Size = New-Object System.Drawing.Size(1000, 130)
$panelRodape.BackColor = Get-Cor "Painel"
$form.Controls.Add($panelRodape)

$lblStatusTitulo = New-Object System.Windows.Forms.Label
$lblStatusTitulo.Text = "STATUS"
$lblStatusTitulo.Font = $fonteTitulo
$lblStatusTitulo.ForeColor = Get-Cor "Azul"
$lblStatusTitulo.BackColor = [System.Drawing.Color]::Transparent
$lblStatusTitulo.Location = New-Object System.Drawing.Point(20, 8)
$lblStatusTitulo.AutoSize = $true
$panelRodape.Controls.Add($lblStatusTitulo)

$txtStatus = New-Object System.Windows.Forms.TextBox
$txtStatus.Multiline = $true
$txtStatus.ScrollBars = "Vertical"
$txtStatus.ReadOnly = $true
$txtStatus.BackColor = Get-Cor "Console"
$txtStatus.ForeColor = Get-Cor "ConsoleTexto"
$txtStatus.Font = $fonteMono
$txtStatus.Location = New-Object System.Drawing.Point(20, 35)
$txtStatus.Size = New-Object System.Drawing.Size(960, 60)
$txtStatus.BorderStyle = "FixedSingle"
$panelRodape.Controls.Add($txtStatus)

$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Location = New-Object System.Drawing.Point(20, 102)
$progress.Size = New-Object System.Drawing.Size(960, 10)
$progress.Style = "Marquee"
$progress.MarqueeAnimationSpeed = 0
$panelRodape.Controls.Add($progress)

# ============================================================
# FUNCOES UI
# ============================================================
function Set-Status {
    param([string]$msg)
    $txtStatus.AppendText("[$((Get-Date).ToString('HH:mm:ss'))] $msg`r`n")
    $txtStatus.SelectionStart = $txtStatus.TextLength
    $txtStatus.ScrollToCaret()
    [System.Windows.Forms.Application]::DoEvents()
}

function CarregarFrases {
    param([string]$nomeArquivo, [string]$titulo)
    $caminho = Join-Path $pastaDados "$nomeArquivo.txt"
    if (-not (Test-Path $caminho)) {
        Set-Status "Arquivo nao encontrado: $caminho"
        return
    }
    $script:frasesAtuais = @()
    Get-Content $caminho -Encoding UTF8 | ForEach-Object {
        if ($_ -match "^(.*?)\|(.*?)\|(.*)$") {
            $script:frasesAtuais += @{
                Ing = $matches[1].Trim()
                Por = $matches[2].Trim()
                Fon = $matches[3].Trim()
            }
        }
    }
    if ($script:frasesAtuais.Count -eq 0) {
        Set-Status "Nenhuma frase encontrada em $nomeArquivo"
        return
    }
    $script:indiceFrase = 0
    $lblFraseTitulo.Text = $titulo
    $script:estudos++
    Save-Progresso
    Update-ProgressoLabel
    MostrarFrase
    $tabs.SelectedTab = $tabFrases
    Set-Status "Carregado: $titulo ($($script:frasesAtuais.Count) frases)"
}

function MostrarFrase {
    if ($script:frasesAtuais.Count -eq 0) { return }
    $f = $script:frasesAtuais[$script:indiceFrase]
    $lblIngles.Text = $f.Ing
    $lblPortugues.Text = $f.Por
    $lblFonetica.Text = $f.Fon
    $lblContador.Text = "Frase $($script:indiceFrase + 1) de $($script:frasesAtuais.Count)"
}

# ============================================================
# EVENTOS - BOTOES DE ESTUDO
# ============================================================
$btnGotta.Add_Click({   CarregarFrases "gotta"   "GOTTA - have got to / have to" })
$btnGonna.Add_Click({   CarregarFrases "gonna"   "GONNA - going to" })
$btnWanna.Add_Click({   CarregarFrases "wanna"   "WANNA - want to" })
$btnGimme.Add_Click({   CarregarFrases "gimme"   "GIMME - give me" })
$btnLemme.Add_Click({   CarregarFrases "lemme"   "LEMME - let me" })
$btnKinda.Add_Click({   CarregarFrases "kinda"   "KINDA - kind of" })
$btnSorta.Add_Click({   CarregarFrases "sorta"   "SORTA - sort of" })
$btnOutta.Add_Click({   CarregarFrases "outta"   "OUTTA - out of" })
$btnHafta.Add_Click({   CarregarFrases "hafta"   "HAFTA - have to" })
$btnShoulda.Add_Click({ CarregarFrases "shoulda" "SHOULDA - should have" })
$btnCoulda.Add_Click({  CarregarFrases "coulda"  "COULDA - could have" })
$btnWoulda.Add_Click({  CarregarFrases "woulda"  "WOULDA - would have" })
$btnMusta.Add_Click({   CarregarFrases "musta"   "MUSTA - must have" })
$btnAint.Add_Click({    CarregarFrases "aint"    "AIN'T - negacao informal" })
$btnDontcha.Add_Click({ CarregarFrases "dontcha" "DON'TCHA - don't you" })
$btnCmon.Add_Click({    CarregarFrases "cmon"    "C'MON - come on" })
$btnGotcha.Add_Click({  CarregarFrases "gotcha"  "GOTCHA - got you" })
$btnBetcha.Add_Click({  CarregarFrases "betcha"  "BETCHA - bet you" })
$btnDunno.Add_Click({   CarregarFrases "dunno"   "DUNNO - don't know" })
$btnImma.Add_Click({    CarregarFrases "imma"    "I'MMA - I'm going to" })
$btnModais.Add_Click({  CarregarFrases "modais"  "VERBOS MODAIS" })

$btnAnterior.Add_Click({
    if ($script:frasesAtuais.Count -eq 0) { return }
    $script:indiceFrase--
    if ($script:indiceFrase -lt 0) { $script:indiceFrase = $script:frasesAtuais.Count - 1 }
    MostrarFrase
})

$btnProximo.Add_Click({
    if ($script:frasesAtuais.Count -eq 0) { return }
    $script:indiceFrase++
    if ($script:indiceFrase -ge $script:frasesAtuais.Count) { $script:indiceFrase = 0 }
    MostrarFrase
})

$btnOuvir.Add_Click({
    if ($script:frasesAtuais.Count -eq 0) { return }
    Falar $script:frasesAtuais[$script:indiceFrase].Ing 0
})

$btnOuvirDev.Add_Click({
    if ($script:frasesAtuais.Count -eq 0) { return }
    Falar $script:frasesAtuais[$script:indiceFrase].Ing -4
})

$btnOuvirTodas.Add_Click({
    if ($script:frasesAtuais.Count -eq 0) { Set-Status "Escolha uma contração primeiro!"; return }
    Set-Status "Ouvindo todas as frases..."
    foreach ($f in $script:frasesAtuais) {
        Set-Status "> $($f.Ing)"
        Falar $f.Ing 0
    }
    Set-Status "Fim!"
})

$btnPronuncia.Add_Click({
    $t = [Microsoft.VisualBasic.Interaction]::InputBox("Digite a frase em ingles:", "Pronuncia", "")
    if ($t) { Falar $t 0 }
})

# ============================================================
# QUIZ
# ============================================================
$script:quizPerguntas = @(
    @{ Perg="Eu quero ir."; A="I gonna go."; B="I wanna go."; C="I gotta go."; D="I shoulda go."; Corr="B" },
    @{ Perg="Eu tenho que ir."; A="I wanna go."; B="I gotta go."; C="I'm gonna go."; D="I dunno go."; Corr="B" },
    @{ Perg="Eu vou viajar amanha."; A="I gotta travel tomorrow."; B="I wanna travel tomorrow."; C="I'm gonna travel tomorrow."; D="I shoulda travel tomorrow."; Corr="C" },
    @{ Perg="Deixa eu ver."; A="Gimme see."; B="Lemme see."; C="Gonna see."; D="Gotta see."; Corr="B" },
    @{ Perg="Me de uma chance."; A="Lemme a chance."; B="Gonna a chance."; C="Gimme a chance."; D="Wanna a chance."; Corr="C" },
    @{ Perg="Eu deveria ter te ligado."; A="I coulda called you."; B="I shoulda called you."; C="I woulda called you."; D="I musta called you."; Corr="B" },
    @{ Perg="Eu poderia ter ido."; A="I shoulda gone."; B="I woulda gone."; C="I coulda gone."; D="I musta gone."; Corr="C" },
    @{ Perg="Eu nao sei."; A="I dunno."; B="I wanna."; C="I gotta."; D="I'mma."; Corr="A" },
    @{ Perg="Voce nao gosta disso?"; A="Don'tcha like it?"; B="Betcha like it?"; C="Gotcha like it?"; D="Dunno like it?"; Corr="A" },
    @{ Perg="Eu vou ir."; A="I gotta go."; B="I wanna go."; C="I'mma go."; D="I shoulda go."; Corr="C" },
    @{ Perg="Ela vai ligar mais tarde."; A="She gotta call later."; B="She's gonna call later."; C="She wanna call later."; D="She shoulda call later."; Corr="B" },
    @{ Perg="Estou sem tempo."; A="I'm outta time."; B="I'm gonna time."; C="I'm gotta time."; D="I'm wanna time."; Corr="A" },
    @{ Perg="Voce tem que provar isso."; A="You wanna try this."; B="You gonna try this."; C="You gotta try this."; D="You shoulda try this."; Corr="C" },
    @{ Perg="Aposto que voce esta certo."; A="Gotcha you're right."; B="Betcha you're right."; C="Dunno you're right."; D="Lemme you're right."; Corr="B" },
    @{ Perg="Te peguei!"; A="Gotcha!"; B="Betcha!"; C="Dunno!"; D="Gimme!"; Corr="A" },
    @{ Perg="Nos temos que conversar."; A="We gonna talk."; B="We wanna talk."; C="We gotta talk."; D="We shoulda talk."; Corr="C" },
    @{ Perg="Eu quero aprender ingles."; A="I gotta learn English."; B="I wanna learn English."; C="I'm gonna learn English."; D="I shoulda learn English."; Corr="B" },
    @{ Perg="Estou meio cansado."; A="I'm kinda tired."; B="I'm gonna tired."; C="I'm gotta tired."; D="I'm wanna tired."; Corr="A" },
    @{ Perg="Ele deve ter saido."; A="He shoulda left."; B="He coulda left."; C="He woulda left."; D="He musta left."; Corr="D" },
    @{ Perg="Vamos, bora!"; A="C'mon, let's go!"; B="Gotcha, let's go!"; C="Betcha, let's go!"; D="Dunno, let's go!"; Corr="A" },
    @{ Perg="Voce pode me ajudar?"; A="May you help me?"; B="Must you help me?"; C="Can you help me?"; D="Should you help me?"; Corr="C" },
    @{ Perg="Voce deveria estudar mais."; A="You could study more."; B="You should study more."; C="You must study more."; D="You may study more."; Corr="B" },
    @{ Perg="Voce deve usar o cinto."; A="You can wear a seatbelt."; B="You should wear a seatbelt."; C="You may wear a seatbelt."; D="You must wear a seatbelt."; Corr="D" },
    @{ Perg="Posso entrar?"; A="May I come in?"; B="Must I come in?"; C="Should I come in?"; D="Could I come in?"; Corr="A" },
    @{ Perg="Ela talvez esteja cansada."; A="She must be tired."; B="She might be tired."; C="She can be tired."; D="She should be tired."; Corr="B" },
    @{ Perg="Deixa eu te ajudar."; A="Gimme help you."; B="Gonna help you."; C="Lemme help you."; D="Gotta help you."; Corr="C" },
    @{ Perg="Nao sei o que fazer."; A="Dunno what to do."; B="Gonna what to do."; C="Gotta what to do."; D="Wanna what to do."; Corr="A" },
    @{ Perg="Isso nao e verdade."; A="That don't true."; B="That won't true."; C="That can't true."; D="That ain't true."; Corr="D" },
    @{ Perg="Eu vou comer pizza."; A="I gotta eat pizza."; B="I'm gonna eat pizza."; C="I shoulda eat pizza."; D="I wanna eat pizza."; Corr="B" },
    @{ Perg="Me de um minuto."; A="Gimme a minute."; B="Lemme a minute."; C="Gonna a minute."; D="Gotta a minute."; Corr="A" },
    @{ Perg="Eu preciso de ajuda."; A="I dunno help."; B="I gotta help."; C="I gotta have help."; D="I gotta get help."; Corr="D" }
)

$script:quizSorteadas = @()
$script:quizIdx = 0
$script:quizAcertos = 0
$script:quizErros = 0
$script:quizAtivo = $false

function IniciarQuiz {
    $script:quizSorteadas = @()
    $ids = 0..($script:quizPerguntas.Count - 1) | Get-Random -Count 10
    foreach ($i in $ids) { $script:quizSorteadas += $script:quizPerguntas[$i] }
    $script:quizIdx = 0
    $script:quizAcertos = 0
    $script:quizErros = 0
    $script:quizAtivo = $true
    $btnIniciarQuiz.Visible = $false
    $btnQuizProx.Visible = $false
    MostrarPergunta
}

function MostrarPergunta {
    if ($script:quizIdx -ge $script:quizSorteadas.Count) {
        FinalizarQuiz
        return
    }
    $p = $script:quizSorteadas[$script:quizIdx]
    $lblQuizNum.Text = "Pergunta $($script:quizIdx + 1) de 10"
    $lblQuizPergunta.Text = "`"$($p.Perg)`""
    $btnQuizA.Text = "A) $($p.A)"
    $btnQuizB.Text = "B) $($p.B)"
    $btnQuizC.Text = "C) $($p.C)"
    $btnQuizD.Text = "D) $($p.D)"
    $btnQuizA.Enabled = $true
    $btnQuizB.Enabled = $true
    $btnQuizC.Enabled = $true
    $btnQuizD.Enabled = $true
    $btnQuizProx.Visible = $false
    Set-Status "Quiz: pergunta $($script:quizIdx + 1)"
}

function Responder {
    param([string]$letra)
    if (-not $script:quizAtivo) { return }
    $p = $script:quizSorteadas[$script:quizIdx]
    if ($letra -eq $p.Corr) {
        $script:quizAcertos++
        $script:acertos++
        Set-Status "CORRETO! Resposta: $letra"
    } else {
        $script:quizErros++
        $script:erros++
        Set-Status "ERRADO! Resposta correta: $($p.Corr)"
    }
    Save-Progresso
    Update-ProgressoLabel
    $btnQuizA.Enabled = $false
    $btnQuizB.Enabled = $false
    $btnQuizC.Enabled = $false
    $btnQuizD.Enabled = $false
    $btnQuizProx.Visible = $true
}

function FinalizarQuiz {
    $script:quizAtivo = $false
    $perc = [math]::Round($script:quizAcertos * 100 / 10, 0)
    $nivel = "PRECISA ESTUDAR MAIS"
    if ($perc -ge 90) { $nivel = "EXCELENTE!" }
    elseif ($perc -ge 70) { $nivel = "BOM!" }
    elseif ($perc -ge 50) { $nivel = "EM DESENVOLVIMENTO" }
    [System.Windows.Forms.MessageBox]::Show(
        "FIM DO QUIZ`n`nAcertos: $script:quizAcertos de 10`nErros: $script:quizErros de 10`nAproveitamento: $perc%`nNivel: $nivel",
        "Resultado",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information) | Out-Null
    $btnIniciarQuiz.Visible = $true
    $btnQuizProx.Visible = $false
    Set-Status "Quiz finalizado: $script:quizAcertos/10 ($perc%)"
}

$btnIniciarQuiz.Add_Click({ IniciarQuiz })
$btnQuizA.Add_Click({ Responder "A" })
$btnQuizB.Add_Click({ Responder "B" })
$btnQuizC.Add_Click({ Responder "C" })
$btnQuizD.Add_Click({ Responder "D" })
$btnQuizProx.Add_Click({
    $script:quizIdx++
    MostrarPergunta
})

# ============================================================
# TEMA
# ============================================================
function Apply-Theme {
    $form.BackColor = Get-Cor "Fundo"
    $header.BackColor = Get-Cor "Header"
    $panelGraficos.BackColor = Get-Cor "Painel"
    $panelRodape.BackColor = Get-Cor "Painel"
    $titulo.ForeColor = Get-Cor "Verde"
    $subtitulo.ForeColor = Get-Cor "TextoSuave"
    $lblProgresso.ForeColor = Get-Cor "Texto"
    $lblStatusTitulo.ForeColor = Get-Cor "Azul"
    $txtStatus.BackColor = Get-Cor "Console"
    $txtStatus.ForeColor = Get-Cor "ConsoleTexto"
    $tabEstudo.BackColor = Get-Cor "Fundo"
    $tabFrases.BackColor = Get-Cor "Fundo"
    $tabQuiz.BackColor = Get-Cor "Fundo"
    $lblIngles.ForeColor = Get-Cor "Verde"
    $lblPortugues.ForeColor = Get-Cor "Texto"
    $lblFonetica.ForeColor = Get-Cor "Amarelo"
    $lblQuizPergunta.ForeColor = Get-Cor "Amarelo"
    $lblFraseTitulo.ForeColor = Get-Cor "Azul"
    $lblQuizTitulo.ForeColor = Get-Cor "Azul"

    foreach ($container in @($tabEstudo, $tabFrases, $tabQuiz)) {
        foreach ($ctrl in $container.Controls) {
            if ($ctrl -is [System.Windows.Forms.Button]) {
                $estilo = if ($ctrl.Tag) { $ctrl.Tag } else { "normal" }
                $ctrl.BackColor = switch ($estilo) {
                    "verde" { Get-Cor "BotaoVerde" }
                    "verm"  { Get-Cor "BotaoVerm" }
                    "azul"  { Get-Cor "BotaoAzul" }
                    default { Get-Cor "Botao" }
                }
                $ctrl.ForeColor = Get-Cor "Texto"
                $ctrl.FlatAppearance.BorderColor = Get-Cor "TextoSuave"
                $ctrl.FlatAppearance.MouseOverBackColor = Get-Cor "BotaoHover"
            }
            if ($ctrl -is [System.Windows.Forms.Label]) {
                if ($ctrl -eq $lblIngles) { $ctrl.ForeColor = Get-Cor "Verde" }
                elseif ($ctrl -eq $lblFonetica) { $ctrl.ForeColor = Get-Cor "Amarelo" }
                elseif ($ctrl -eq $lblQuizPergunta) { $ctrl.ForeColor = Get-Cor "Amarelo" }
                elseif ($ctrl -eq $lblFraseTitulo -or $ctrl -eq $lblQuizTitulo) { $ctrl.ForeColor = Get-Cor "Azul" }
                else { $ctrl.ForeColor = Get-Cor "Texto" }
            }
        }
    }
    $form.Invalidate($true)
    $form.Refresh()
}

$btnTema.Add_Click({
    $script:temaEscuro = -not $script:temaEscuro
    if ($script:temaEscuro) { $btnTema.Text = "TEMA" } else { $btnTema.Text = "TEMA" }
    Apply-Theme
    Set-Status "Tema alterado."
})

# ============================================================
# INICIALIZACAO
# ============================================================
Set-Status "Curso de Ingles iniciado."
Set-Status "Pasta de dados: $pastaDados"
Set-Status "Progresso: $script:acertos acertos / $script:erros erros / $script:estudos estudos"

[void]$form.ShowDialog()
$form.Dispose()