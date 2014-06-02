.PHONY: tests docs

docs:
	${MAKE} -C docs html


tests:
	py.test --pep8 --cov oscar_mws
	py.test -m integration
