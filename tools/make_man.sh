#!/bin/sh

# stop on failure
set -e

# Use C local to avoid local dates in headers
export LANG=en_US.utf8

# disable termcolor
export ANSI_COLORS_DISABLED=1

[ -z "${TMPDIR}" ] && TMPDIR="/tmp"

# do not allow undefined variables anymore
set -u
WEBOOB_TMPDIR=$(mktemp -d "${TMPDIR}/weboob_man.XXXXX")

# path to sources
WEBOOB_DIR=$(readlink -e $(dirname $0)/..)
touch "${WEBOOB_TMPDIR}/backends"
chmod 600 "${WEBOOB_TMPDIR}/backends"
echo "file://$WEBOOB_DIR/modules" > "${WEBOOB_TMPDIR}/sources.list"

export WEBOOB_WORKDIR="${WEBOOB_TMPDIR}"
export PYTHONPATH="${WEBOOB_DIR}"
"${WEBOOB_DIR}/scripts/weboob-config" update

"${WEBOOB_DIR}/tools/make_man.py"

# allow failing commands past this point
STATUS=$?

rm -rf "${WEBOOB_TMPDIR}"

exit $STATUS
