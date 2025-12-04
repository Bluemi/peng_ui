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
	*)
		shift
		echo "invalid option: $@"
esac
