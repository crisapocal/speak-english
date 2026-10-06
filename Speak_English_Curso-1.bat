@echo off
chcp 65001 >nul
title CURSO DE INGLES - SPEAK ENGLISH
color 0A
setlocal EnableDelayedExpansion

:: ============================================================
:: CURSO DE INGLES - SPEAK ENGLISH v3.1
:: Traducao + Fonetica + Quiz com 30 perguntas
:: ============================================================

set "PASTA=%~dp0"
set "DADOS=%PASTA%dados"
set "DATA=%PASTA%progresso.txt"

if not exist "%DATA%" (
    >"%DATA%" echo ACERTOS=0
    >>"%DATA%" echo ERROS=0
    >>"%DATA%" echo ESTUDOS=0
)
call :loadStats

:MENU
cls
color 0A
echo.
echo ============================================================
echo                  SPEAK ENGLISH - CURSO
echo ============================================================
echo.
echo   [1] CONTRACOES E INGLES INFORMAL
echo   [2] VERBOS MODAIS
echo   [3] PRONUNCIA E REPETICAO
echo   [4] QUIZ (30 perguntas)
echo   [5] PROGRESSO
echo   [6] SOBRE
echo   [0] SAIR
echo.
echo ------------------------------------------------------------
echo   Acertos: !ACERTOS!    Erros: !ERROS!    Estudos: !ESTUDOS!
echo ============================================================
echo.
set /p "op=Escolha uma opcao: "
if "%op%"=="1" goto CONTRACOES
if "%op%"=="2" goto MODAIS
if "%op%"=="3" goto PRONUNCIA
if "%op%"=="4" goto QUIZ
if "%op%"=="5" goto PROGRESSO
if "%op%"=="6" goto SOBRE
if "%op%"=="0" exit /b
goto MENU

:: ============================================================
:: CONTRACOES
:: ============================================================
:CONTRACOES
cls
color 0B
echo.
echo ============================================================
echo              CONTRACOES E INGLES INFORMAL
echo ============================================================
echo.
echo   [1] GOTTA      [2] GONNA      [3] WANNA
echo   [4] GIMME      [5] LEMME      [6] KINDA
echo   [7] SORTA      [8] OUTTA      [9] HAFTA
echo   [10] SHOULDA   [11] COULDA    [12] WOULDA
echo   [13] MUSTA     [14] AIN'T     [15] DON'TCHA
echo   [16] C'MON      [17] GOTCHA    [18] BETCHA
echo   [19] DUNNO     [20] I'MMA
echo   [0] VOLTAR
echo.
set /p "c=Escolha: "

if "%c%"=="1"  call :LerArquivo gotta    "GOTTA - have got to / have to"
if "%c%"=="2"  call :LerArquivo gonna    "GONNA - going to"
if "%c%"=="3"  call :LerArquivo wanna    "WANNA - want to"
if "%c%"=="4"  call :LerArquivo gimme    "GIMME - give me"
if "%c%"=="5"  call :LerArquivo lemme    "LEMME - let me"
if "%c%"=="6"  call :LerArquivo kinda    "KINDA - kind of"
if "%c%"=="7"  call :LerArquivo sorta    "SORTA - sort of"
if "%c%"=="8"  call :LerArquivo outta    "OUTTA - out of"
if "%c%"=="9"  call :LerArquivo hafta    "HAFTA - have to"
if "%c%"=="10" call :LerArquivo shoulda  "SHOULDA - should have"
if "%c%"=="11" call :LerArquivo coulda   "COULDA - could have"
if "%c%"=="12" call :LerArquivo woulda   "WOULDA - would have"
if "%c%"=="13" call :LerArquivo musta    "MUSTA - must have"
if "%c%"=="14" call :LerArquivo aint     "AIN'T - negacao informal"
if "%c%"=="15" call :LerArquivo dontcha  "DON'TCHA - don't you"
if "%c%"=="16" call :LerArquivo cmon     "C'MON - come on"
if "%c%"=="17" call :LerArquivo gotcha   "GOTCHA - got you"
if "%c%"=="18" call :LerArquivo betcha   "BETCHA - bet you"
if "%c%"=="19" call :LerArquivo dunno    "DUNNO - don't know"
if "%c%"=="20" call :LerArquivo imma     "I'MMA - I'm going to"
if "%c%"=="0"  goto MENU
goto CONTRACOES

:LerArquivo
set "ARQ=%~1"
set "TITULO=%~2"
if not exist "%DADOS%\%ARQ%.txt" (
    cls
    color 0C
    echo.
    echo ============================================================
    echo   ATENCAO: Arquivo nao encontrado!
    echo ============================================================
    echo.
    echo   Caminho esperado:
    echo   %DADOS%\%ARQ%.txt
    echo.
    echo   Verifique se o arquivo "%ARQ%.txt" existe na pasta "dados".
    echo.
    pause
    exit /b
)
call :LerFrases "%DADOS%\%ARQ%.txt" "%TITULO%" ""
exit /b

:: ============================================================
:: MODAIS
:: ============================================================
:MODAIS
cls
color 0E
echo.
echo ============================================================
echo                       VERBOS MODAIS
echo ============================================================
echo.
echo [1] CAN  [2] COULD  [3] MAY  [4] MIGHT
echo [5] SHOULD  [6] MUST  [7] WILL  [8] SHALL
echo [0] VOLTAR
echo.
set /p "m=Escolha: "
if "%m%"=="1" call :LerModais CAN    "MODAIS - CAN"
if "%m%"=="2" call :LerModais COULD  "MODAIS - COULD"
if "%m%"=="3" call :LerModais MAY    "MODAIS - MAY"
if "%m%"=="4" call :LerModais MIGHT  "MODAIS - MIGHT"
if "%m%"=="5" call :LerModais SHOULD "MODAIS - SHOULD"
if "%m%"=="6" call :LerModais MUST   "MODAIS - MUST"
if "%m%"=="7" call :LerModais WILL   "MODAIS - WILL"
if "%m%"=="8" call :LerModais SHALL  "MODAIS - SHALL"
if "%m%"=="0" goto MENU
goto MODAIS

:LerModais
set "ARQ=%~1"
set "TITULO=%~2"
if not exist "%DADOS%\modais.txt" (
    cls
    color 0C
    echo.
    echo ATENCAO: %DADOS%\modais.txt nao encontrado!
    echo Crie o arquivo na pasta dados.
    echo.
    pause
    exit /b
)
call :LerFrases "%DADOS%\modais.txt" "%TITULO%" "%ARQ%"
exit /b

:: ============================================================
:: LEITOR DE FRASES (com traducao e fonetica)
:: ============================================================
:LerFrases
cls
color 0B
set "ARQ=%~1"
set "TITULO=%~2"
set "FILTRO=%~3"

echo.
echo ============================================================
echo   %TITULO%
echo ============================================================
echo.
echo   #    INGLES                            PORTUGUES                         FONETICA
echo   ---  --------------------------------  --------------------------------  --------------------
echo.

set /a N=0
for /f "usebackq tokens=1,2,3 delims=|" %%A in ("%ARQ%") do (
    set "ING=%%A"
    set "POR=%%B"
    set "FON=%%C"

    set "MOSTRAR=1"
    if not "%FILTRO%"=="" (
        set "MOSTRAR=0"
        echo !ING! | findstr /I /C:"%FILTRO% " >nul && set "MOSTRAR=1"
    )

    if !MOSTRAR!==1 (
        set /a N+=1
        call :MostrarLinha "!N!" "!ING!" "!POR!" "!FON!"
    )
)

echo.
echo   Total: !N! frases
echo ============================================================
echo.
echo   [1] Ouvir todas as frases
echo   [2] Praticar uma frase (digitar numero)
echo   [3] Voltar
echo.
set /p "op=Escolha: "
if "%op%"=="1" call :OuvirTodas "%ARQ%" "%FILTRO%" & goto LerFrases
if "%op%"=="2" call :PraticarFrase "%ARQ%" "%FILTRO%" & goto LerFrases
if "%op%"=="3" exit /b
goto LerFrases

:: ============================================================
:: MOSTRAR LINHA FORMATADA (com alinhamento)
:: ============================================================
:MostrarLinha
set "LN=%~1"
set "ING=%~2"
set "POR=%~3"
set "FON=%~4"

:: Alinha em 32 caracteres
set "ING_T=!ING!                                "
set "ING_T=!ING_T:~0,32!"

set "POR_T=!POR!                                "
set "POR_T=!POR_T:~0,32!"

echo   !LN!    !ING_T!  !POR_T!  !FON!
exit /b

:: ============================================================
:: OUVIR TODAS
:: ============================================================
:OuvirTodas
set "ARQ=%~1"
set "FILTRO=%~2"
cls
color 0B
echo.
echo ============================================================
echo   OUVINDO TODAS AS FRASES
echo ============================================================
echo.
echo   #    INGLES                            PORTUGUES
echo   ---  --------------------------------  --------------------------------
echo.

set /a N=0
for /f "usebackq tokens=1,2,3 delims=|" %%A in ("%ARQ%") do (
    set "ING=%%A"
    set "POR=%%B"
    set "FON=%%C"

    set "MOSTRAR=1"
    if not "%FILTRO%"=="" (
        set "MOSTRAR=0"
        echo !ING! | findstr /I /C:"%FILTRO% " >nul && set "MOSTRAR=1"
    )

    if !MOSTRAR!==1 (
        set /a N+=1
        set "ING_T=!ING!                                "
        set "ING_T=!ING_T:~0,32!"
        set "POR_T=!POR!                                "
        set "POR_T=!POR_T:~0,32!"
        echo   !N!    !ING_T!  !POR_T!
        call :speak "!ING!" 0
    )
)
echo.
echo   Total: !N! frases reproduzidas.
echo ============================================================
pause
exit /b

:: ============================================================
:: PRATICAR UMA FRASE (com traducao e fonetica)
:: ============================================================
:PraticarFrase
set "ARQ=%~1"
set "FILTRO=%~2"
set /p "num=Numero da frase: "
set /a N=0
set "ENCONTRADA=0"

for /f "usebackq tokens=1,2,3 delims=|" %%A in ("%ARQ%") do (
    set "ING=%%A"
    set "POR=%%B"
    set "FON=%%C"

    set "MOSTRAR=1"
    if not "%FILTRO%"=="" (
        set "MOSTRAR=0"
        echo !ING! | findstr /I /C:"%FILTRO% " >nul && set "MOSTRAR=1"
    )

    if !MOSTRAR!==1 (
        set /a N+=1
        if !N!==%num% (
            set "ENCONTRADA=1"
            cls
            color 0B
            echo.
            echo ============================================================
            echo   FRASE !N!
            echo ============================================================
            echo.
            echo   INGLES:
            echo   !ING!
            echo.
            echo   PORTUGUES:
            echo   !POR!
            echo.
            echo   FONETICA:
            echo   !FON!
            echo.
            echo ============================================================
            echo.
            call :speak "!ING!" 0
            echo.
            echo   [1] Ouvir novamente
            echo   [2] Ouvir devagar
            echo   [3] Voltar
            echo.
            set /p "op=Escolha: "
            if "!op!"=="1" call :speak "!ING!" 0 & goto PraticarFrase
            if "!op!"=="2" call :speak "!ING!" -4 & goto PraticarFrase
            if "!op!"=="3" exit /b
        )
    )
)

if !ENCONTRADA!==0 (
    echo.
    echo   Frase nao encontrada!
    pause
)
exit /b

:: ============================================================
:: PRONUNCIA
:: ============================================================
:PRONUNCIA
cls
color 0D
echo.
echo ============================================================
echo                    PRATICA DE PRONUNCIA
echo ============================================================
echo.
echo Digite uma frase em ingles para ouvir:
echo.
set /p "txt=Frase: "
if "%txt%"=="" goto MENU
call :speak "%txt%" 0
echo.
echo Repita em voz alta!
echo.
pause
goto MENU

:: ============================================================
:: QUIZ - 30 PERGUNTAS COM SORTEIO ALEATORIO
:: ============================================================
:QUIZ
cls
color 0E
set /a QNUM=0
set /a QACERTOS=0
set /a QERROS=0

:: Sorteia 10 numeros unicos de 1 a 30
set "SORTEADOS="
set /a COUNT=0
:LoopSorteio
if !COUNT! GEQ 10 goto InicioQuiz
set /a R=!random! %% 30 + 1
echo !SORTEADOS! | findstr /C:",!R!," >nul
if !errorlevel!==0 goto LoopSorteio
set "SORTEADOS=!SORTEADOS!,!R!"
set /a COUNT+=1
goto LoopSorteio

:InicioQuiz
for %%S in (%SORTEADOS%) do (
    set "S=%%S"
    call :Pergunta !S!
)

:QuizFim
cls
color 0A
set /a QPERC=QACERTOS*100/10
echo.
echo ============================================================
echo                    FIM DO QUIZ
echo ============================================================
echo.
echo   Acertos: !QACERTOS! de 10
echo   Erros:   !QERROS! de 10
echo   Aproveitamento: !QPERC!%%
echo.
if !QPERC! GEQ 90 echo   Nivel: EXCELENTE!
if !QPERC! GEQ 70 if !QPERC! LSS 90 echo   Nivel: BOM!
if !QPERC! GEQ 50 if !QPERC! LSS 70 echo   Nivel: EM DESENVOLVIMENTO
if !QPERC! LSS 50 echo   Nivel: PRECISA ESTUDAR MAIS
echo.
echo ============================================================
echo   [1] Jogar de novo
echo   [2] Voltar ao menu
echo ============================================================
set /p "op=Escolha: "
if "%op%"=="1" goto QUIZ
if "%op%"=="2" goto MENU
goto QuizFim

:: ============================================================
:: FUNCAO PERGUNTA
:: ============================================================
:Pergunta
set /a QNUM+=1
cls
color 0E
echo.
echo ============================================================
echo              QUIZ - PERGUNTA !QNUM! DE 10
echo ============================================================
echo.

set "PERG=%~1"
set "CORR="

if "%PERG%"=="1"  set "CORR=B" & echo   "Eu quero ir." & echo. & echo    A) I gonna go. & echo    B) I wanna go. & echo    C) I gotta go. & echo    D) I shoulda go.
if "%PERG%"=="2"  set "CORR=B" & echo   "Eu tenho que ir." & echo. & echo    A) I wanna go. & echo    B) I gotta go. & echo    C) I'm gonna go. & echo    D) I dunno go.
if "%PERG%"=="3"  set "CORR=C" & echo   "Eu vou viajar amanha." & echo. & echo    A) I gotta travel tomorrow. & echo    B) I wanna travel tomorrow. & echo    C) I'm gonna travel tomorrow. & echo    D) I shoulda travel tomorrow.
if "%PERG%"=="4"  set "CORR=B" & echo   "Deixa eu ver." & echo. & echo    A) Gimme see. & echo    B) Lemme see. & echo    C) Gonna see. & echo    D) Gotta see.
if "%PERG%"=="5"  set "CORR=C" & echo   "Me de uma chance." & echo. & echo    A) Lemme a chance. & echo    B) Gonna a chance. & echo    C) Gimme a chance. & echo    D) Wanna a chance.
if "%PERG%"=="6"  set "CORR=B" & echo   "Eu deveria ter te ligado." & echo. & echo    A) I coulda called you. & echo    B) I shoulda called you. & echo    C) I woulda called you. & echo    D) I musta called you.
if "%PERG%"=="7"  set "CORR=C" & echo   "Eu poderia ter ido." & echo. & echo    A) I shoulda gone. & echo    B) I woulda gone. & echo    C) I coulda gone. & echo    D) I musta gone.
if "%PERG%"=="8"  set "CORR=A" & echo   "Eu nao sei." & echo. & echo    A) I dunno. & echo    B) I wanna. & echo    C) I gotta. & echo    D) I'mma.
if "%PERG%"=="9"  set "CORR=A" & echo   "Voce nao gosta disso?" & echo. & echo    A) Don'tcha like it? & echo    B) Betcha like it? & echo    C) Gotcha like it? & echo    D) Dunno like it?
if "%PERG%"=="10" set "CORR=C" & echo   "Eu vou ir." & echo. & echo    A) I gotta go. & echo    B) I wanna go. & echo    C) I'mma go. & echo    D) I shoulda go.
if "%PERG%"=="11" set "CORR=B" & echo   "Ela vai ligar mais tarde." & echo. & echo    A) She gotta call later. & echo    B) She's gonna call later. & echo    C) She wanna call later. & echo    D) She shoulda call later.
if "%PERG%"=="12" set "CORR=A" & echo   "Estou sem tempo." & echo. & echo    A) I'm outta time. & echo    B) I'm gonna time. & echo    C) I'm gotta time. & echo    D) I'm wanna time.
if "%PERG%"=="13" set "CORR=C" & echo   "Voce tem que provar isso." & echo. & echo    A) You wanna try this. & echo    B) You gonna try this. & echo    C) You gotta try this. & echo    D) You shoulda try this.
if "%PERG%"=="14" set "CORR=B" & echo   "Aposto que voce esta certo." & echo. & echo    A) Gotcha you're right. & echo    B) Betcha you're right. & echo    C) Dunno you're right. & echo    D) Lemme you're right.
if "%PERG%"=="15" set "CORR=A" & echo   "Te peguei!" & echo. & echo    A) Gotcha! & echo    B) Betcha! & echo    C) Dunno! & echo    D) Gimme!
if "%PERG%"=="16" set "CORR=C" & echo   "Nos temos que conversar." & echo. & echo    A) We gonna talk. & echo    B) We wanna talk. & echo    C) We gotta talk. & echo    D) We shoulda talk.
if "%PERG%"=="17" set "CORR=B" & echo   "Eu quero aprender ingles." & echo. & echo    A) I gotta learn English. & echo    B) I wanna learn English. & echo    C) I'm gonna learn English. & echo    D) I shoulda learn English.
if "%PERG%"=="18" set "CORR=A" & echo   "Estou meio cansado." & echo. & echo    A) I'm kinda tired. & echo    B) I'm gonna tired. & echo    C) I'm gotta tired. & echo    D) I'm wanna tired.
if "%PERG%"=="19" set "CORR=D" & echo   "Ele deve ter saido." & echo. & echo    A) He shoulda left. & echo    B) He coulda left. & echo    C) He woulda left. & echo    D) He musta left.
if "%PERG%"=="20" set "CORR=A" & echo   "Vamos, bora!" & echo. & echo    A) C'mon, let's go! & echo    B) Gotcha, let's go! & echo    C) Betcha, let's go! & echo    D) Dunno, let's go!
if "%PERG%"=="21" set "CORR=C" & echo   "Voce pode me ajudar?" & echo. & echo    A) May you help me? & echo    B) Must you help me? & echo    C) Can you help me? & echo    D) Should you help me?
if "%PERG%"=="22" set "CORR=B" & echo   "Voce deveria estudar mais." & echo. & echo    A) You could study more. & echo    B) You should study more. & echo    C) You must study more. & echo    D) You may study more.
if "%PERG%"=="23" set "CORR=D" & echo   "Voce deve usar o cinto." & echo. & echo    A) You can wear a seatbelt. & echo    B) You should wear a seatbelt. & echo    C) You may wear a seatbelt. & echo    D) You must wear a seatbelt.
if "%PERG%"=="24" set "CORR=A" & echo   "Posso entrar?" & echo. & echo    A) May I come in? & echo    B) Must I come in? & echo    C) Should I come in? & echo    D) Could I come in?
if "%PERG%"=="25" set "CORR=B" & echo   "Ela talvez esteja cansada." & echo. & echo    A) She must be tired. & echo    B) She might be tired. & echo    C) She can be tired. & echo    D) She should be tired.
if "%PERG%"=="26" set "CORR=C" & echo   "Deixa eu te ajudar." & echo. & echo    A) Gimme help you. & echo    B) Gonna help you. & echo    C) Lemme help you. & echo    D) Gotta help you.
if "%PERG%"=="27" set "CORR=A" & echo   "Nao sei o que fazer." & echo. & echo    A) Dunno what to do. & echo    B) Gonna what to do. & echo    C) Gotta what to do. & echo    D) Wanna what to do.
if "%PERG%"=="28" set "CORR=D" & echo   "Isso nao e verdade." & echo. & echo    A) That don't true. & echo    B) That won't true. & echo    C) That can't true. & echo    D) That ain't true.
if "%PERG%"=="29" set "CORR=B" & echo   "Eu vou comer pizza." & echo. & echo    A) I gotta eat pizza. & echo    B) I'm gonna eat pizza. & echo    C) I shoulda eat pizza. & echo    D) I wanna eat pizza.
if "%PERG%"=="30" set "CORR=A" & echo   "Me de um minuto." & echo. & echo    A) Gimme a minute. & echo    B) Lemme a minute. & echo    C) Gonna a minute. & echo    D) Gotta a minute.

echo.
set /p "q=Sua resposta: "

if /I "%q%"=="%CORR%" (
    call :win
    set /a QACERTOS+=1
    echo.
    echo   CORRETO! Resposta: %CORR%
) else (
    call :lose
    set /a QERROS+=1
    echo.
    echo   ERRADO! Resposta correta: %CORR%
)
timeout /t 2 >nul
exit /b

:: ============================================================
:: PROGRESSO
:: ============================================================
:PROGRESSO
cls
color 0A
set /a TOTAL=ACERTOS+ERROS
set /a PERC=0
if !TOTAL! GTR 0 set /a PERC=ACERTOS*100/TOTAL
echo.
echo ============================================================
echo                        PROGRESSO
echo ============================================================
echo.
echo   Acertos : !ACERTOS!
echo   Erros   : !ERROS!
echo   Estudos : !ESTUDOS!
echo   Questoes: !TOTAL!
echo   Aproveitamento: !PERC!%%
echo.
pause
goto MENU

:: ============================================================
:: SOBRE
:: ============================================================
:SOBRE
cls
color 0A
echo.
echo ============================================================
echo                       SOBRE O CURSO
echo ============================================================
echo.
echo SPEAK ENGLISH v3.1
echo Curso offline de ingles informal com audio, quiz e progresso.
echo.
echo Dados lidos de arquivos .txt na pasta dados.
echo Quiz com 30 perguntas e sorteio aleatorio.
echo.
pause
goto MENU

:: ============================================================
:: FUNCAO SPEAK - TTS do Windows
:: ============================================================
:speak
powershell -NoProfile -Command "$ErrorActionPreference='SilentlyContinue'; Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate=%~2; $s.Volume=100; try {$s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::NotSet,[System.Speech.Synthesis.VoiceAge]::NotSet,0,[System.Globalization.CultureInfo]::GetCultureInfo('en-US'))} catch {}; $s.Speak('%~1'); $s.Dispose()" >nul 2>&1
exit /b

:: ============================================================
:: ESTATISTICAS
:: ============================================================
:loadStats
set "ACERTOS=0"
set "ERROS=0"
set "ESTUDOS=0"
for /f "tokens=1,* delims==" %%A in (%DATA%) do (
    if /I "%%A"=="ACERTOS" set "ACERTOS=%%B"
    if /I "%%A"=="ERROS" set "ERROS=%%B"
    if /I "%%A"=="ESTUDOS" set "ESTUDOS=%%B"
)
exit /b

:saveStats
>"%DATA%" echo ACERTOS=!ACERTOS!
>>"%DATA%" echo ERROS=!ERROS!
>>"%DATA%" echo ESTUDOS=!ESTUDOS!
exit /b

:win
set /a ACERTOS+=1
call :saveStats
exit /b

:lose
set /a ERROS+=1
call :saveStats
exit /b