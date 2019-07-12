@echo off

:: ensure we are running from the script's directory
cd /D "%~dp0"

IF "%MALMO_PATH%"=="" (
    echo MALMO_PATH has not been set.
    GOTO END 
)

xcopy %MALMO_PATH%\Python_Examples\MalmoPython.pyd .\malmoext
:END