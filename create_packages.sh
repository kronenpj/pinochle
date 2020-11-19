#!/usr/bin/env bash

if [ -x /usr/bin/podman ]; then
  DOCKER=${DOCKER:-podman}
else
  DOCKER=${DOCKER:-docker}
fi
OPTS="--privileged --rm"
#DEBUG_OPTS="-d all"
CTR_WIN="cdrx/pyinstaller-windows"
CTR_LIN="cdrx/pyinstaller-linux"

function build() {
  #  echo "Image: $1"
  #  echo "Executable: $2"
  case "${1}" in
  "${CTR_LIN}")
    mv -f dist/${2} dist/${2}-prev ;;
  "${CTR_WIN}")
    mv -f dist/${2}.exe dist/${2}-prev.exe ;;
  esac

  capture=`${DOCKER} run ${OPTS} -v "$(pwd):/src/" ${1} \
             "pyinstaller -F ${DEBUG_OPTS} -c ${2}.py" 2>&1`

  if [ $? != 0 ]; then
    echo "Build was not successful, rolling back."
    case "${1}" in
    "${CTR_LIN}")
      mv -f dist/${2}-prev dist/${2};;
    "${CTR_WIN}")
      mv -f dist/${2}-prev.exe dist/${2}.exe;;
    esac
    echo "Process output:"
    echo $capture
  else
    echo "Build of ${2} successful on ${1}"
  fi
}

if [ -z "$1" ]; then
  for p in $CTR_LIN $CTR_WIN; do
    ${DOCKER} pull $p
    for a in pinochle ; do
      build $p $a
    done
  done
else
  for p in $CTR_LIN $CTR_WIN; do
    build $p $1
  done
fi
