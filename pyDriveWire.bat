@ECHO OFF
PATH=%PATH%;C:\Users\Administrator\Downloads\pypy2-v6.0.0-win32\pypy2-v6.0.0-win32
where /q pypy
IF ERRORLEVEL 0 (
  REM do something here to address the error
  SET python=pypy
) ELSE (
  ECHO "pypy not found. pypy is recommended for best performance, see README"
  where /q python
  IF ERRORLEVEL 1 (
    ECHO Ensure that pypy or python is installed and in your path
    EXIT
   )
   set python=python
)

SHIFT
%python% pyDriveWire.py %*