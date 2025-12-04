#!/bin/bash

case "$1" in
	r)
		shift
		python3 peng_ui/cli/main.py "$@"
		;;
	t)
		shift
		pytest "$@"
		;;
	*)
		shift
		echo "invalid option: $@"
esac
