#!/bin/sh

# stop on failure
set -e

[ -z "${TMPDIR}" ] && TMPDIR="/tmp"

# do not allow undefined variables anymore
set -u
WEBOOB_TMPDIR=$(mktemp -d "${TMPDIR}/weboob_lint.XXXXX")

# path to sources
WEBOOB_DIR=$(readlink -e $(dirname $0)/..)
touch "${WEBOOB_TMPDIR}/backends"
chmod 600 "${WEBOOB_TMPDIR}/backends"
echo "file://$WEBOOB_DIR/modules" > "${WEBOOB_TMPDIR}/sources.list"

export WEBOOB_WORKDIR="${WEBOOB_TMPDIR}"
export PYTHONPATH="${WEBOOB_DIR}"
"${WEBOOB_DIR}/scripts/weboob-config" update

"${WEBOOB_DIR}/tools/weboob_lint.py"

# allow failing commands past this point
STATUS=$?

rm -rf "${WEBOOB_TMPDIR}"

exit $STATUS
