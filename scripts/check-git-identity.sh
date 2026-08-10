#!/bin/sh
# Aborta el commit si la identidad de git resuelta es la corporativa.
# Version versionada del check. Ver CLAUDE.md, seccion 3.1.

EMAIL="$(git config user.email)"

case "$EMAIL" in
  *@ispnexus.co)
    echo "ABORTADO: identidad corporativa ($EMAIL) detectada en un repo del portafolio."
    echo "Revisa ~/.gitconfig y ~/.gitconfig-personal antes de continuar."
    exit 1
    ;;
esac

exit 0
