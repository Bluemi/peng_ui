#!/bin/bash

case "$1" in
	r)
		shift
		python3 PROJECT_NAME/main.py
		;;
	*)
		shift
		echo "invalid option: $@"
esac
