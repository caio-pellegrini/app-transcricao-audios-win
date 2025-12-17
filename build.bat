@echo off
echo Ativando ambiente virtual...
call .\env\Scripts\activate.bat

echo.
echo Gerando executavel...
pyinstaller AppTranscricao.spec

echo.
echo ========================================
echo Executavel gerado em: dist\AppTranscricao.exe
echo ========================================
pause



