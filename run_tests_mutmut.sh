#!/usr/bin/env bash

DEBUG=${DEBUG:-}

if [ -z "$VIRTUAL_ENV" ]; then
  . venv/bin/activate
fi

if [ -z "$@" ]; then
  $DEBUG mutmut --use-coverage run
else
  UNTESTED=$(sqlite3 .mutmut-cache -cmd 'select id from mutant where status="untested";' < /dev/null)

  echo "Evaluating these untested mutations:"
  echo $UNTESTED | xargs

  for index in $UNTESTED
  do
    $DEBUG mutmut --use-coverage run $index
  done
fi
