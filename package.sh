# Script for preparing the Python package and pushing it to PyPi
rm -rf dist
rm -rf malmoext.egg-info
python3 setup.py sdist
twine upload --skip-existing dist/*