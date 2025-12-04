#!/bin/bash

case "$1" in
	r)
		shift
		python3 peng_ui/main.py
		;;
	*)
		shift
		echo "invalid option: $@"
esac
