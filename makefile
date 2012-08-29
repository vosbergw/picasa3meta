
# create the docs

all: docs/index.html

docs/index.html: picasa3meta/*.py
	epydoc --html --verbose picasa3meta -o docs

