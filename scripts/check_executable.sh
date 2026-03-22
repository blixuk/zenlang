#!/bin/sh

printf "File: $1\n"
printf "\n"
file $1
printf "\n"
printf "LDd: \n"
ldd $1