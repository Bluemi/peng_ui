#!/bin/bash

case "$1" in
	r)
		shift
		python3 scripts/main.py "$@"
		;;
	t)
		shift
		pytest "$@"
		;;
	c)
		if [ -d dist ]; then
			rm -r dist
		fi
		python -m build
		;;
	u)
		twine upload dist/*
		;;
	*)
		shift
		echo "invalid option: $@"
esac
