@echo off
REM Script for preparing the Python package and pushing it to PyPi
rmdir /s /q dist
rmdir /s /q malmoext.egg-info
python3 setup.py sdist bdist_wheel
python3 -m twine upload --skip-existing dist/*