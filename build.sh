rm -rf dist
python3 setup.py sdist
twine upload --skip-existing dist/*