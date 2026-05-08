#!/usr/bin/env bash
# Register a single self-hosted GitHub Actions runner on THIS machine
# for pyadi-iio hardware tests.  The runner drives every labgrid place
# remotely via the coordinator, so a single host with private-lab
# network access (and Python + labgrid installable) is sufficient — no
# need for per-board runners.
#
# Prereqs on the machine running this script:
#   - gh CLI authenticated with admin scope on analogdevicesinc/pyadi-iio
#   - sudo available (will prompt once for `svc.sh install/start`)
#   - Network reach to the labgrid coordinator at $COORDINATOR
#   - Local tools: gh, jq, curl, tar
#
# Run via the Claude Code `!` prefix so prompts go to the live terminal:
#   ! bash .github/scripts/register-hw-runners.sh
#
# Idempotent: re-running re-registers (replaces) the existing runner
# under the same name without disturbing other runners on this host.

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────
REPO="analogdevicesinc/pyadi-iio"

# Label that .github/workflows/hardware-test.yml's `runs-on:` references.
LABEL="hw-pyadi-iio"

# Runner identity in the GitHub UI.  Suffixed with the host so it's
# distinguishable from any other self-hosted runners on the same box
# (e.g. pyadi-dt's per-host runner already in ~/actions-runner/).
NAME="$(hostname -s)-pyadi-iio"

# Per-repo runner directory.  Distinct from pyadi-dt's default
# ~/actions-runner/ so both runners can coexist on the same host.
RUNNER_DIR="$HOME/actions-runner-pyadi-iio"

# Runner release.  Bump as newer versions ship:
# https://github.com/actions/runner/releases
RUNNER_VERSION="2.333.1"

# ─────────────────────────────────────────────────────────────────────
RUNNER_TARBALL="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
RUNNER_URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_TARBALL}"

die() { echo "error: $*" >&2; exit 1; }

for tool in gh jq curl tar; do
    command -v "$tool" >/dev/null || die "missing required tool: $tool"
done

gh auth status -h github.com >/dev/null 2>&1 \
    || die "gh is not authenticated against github.com — run 'gh auth login' first"

if ! gh api "/repos/${REPO}" --jq '.permissions.admin' 2>/dev/null | grep -qx true; then
    die "the authenticated gh user lacks admin on ${REPO} — cannot mint registration tokens"
fi

echo "Registering pyadi-iio runner on $(hostname):"
echo "  repo:    $REPO"
echo "  label:   self-hosted,$LABEL"
echo "  name:    $NAME"
echo "  dir:     $RUNNER_DIR"
echo "  version: $RUNNER_VERSION"
echo

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

if [[ ! -f "$RUNNER_TARBALL" ]]; then
    echo "-- downloading $RUNNER_TARBALL"
    curl --fail -sSL -o "$RUNNER_TARBALL" "$RUNNER_URL"
fi

if [[ ! -x ./config.sh ]]; then
    echo "-- extracting runner"
    tar xzf "$RUNNER_TARBALL"
fi

echo "-- minting registration token"
TOKEN=$(gh api -X POST "/repos/${REPO}/actions/runners/registration-token" --jq .token)
[[ -n "$TOKEN" ]] || die "failed to mint registration token"

if [[ -f .runner ]]; then
    echo "-- runner already configured; removing old registration"
    ./config.sh remove --token "$TOKEN" || true
fi

echo "-- configuring runner"
./config.sh \
    --url "https://github.com/$REPO" \
    --token "$TOKEN" \
    --name "$NAME" \
    --labels "self-hosted,$LABEL" \
    --unattended --replace

echo "-- installing service (sudo will prompt)"
sudo ./svc.sh install "$USER"
sudo ./svc.sh start
sudo ./svc.sh status | head -5

echo
echo "Waiting 30s for runner to phone home..."
for i in $(seq 30 -5 5); do
    printf '  %ss remaining...\r' "$i"
    sleep 5
done
printf '                       \r'

ROW=$(gh api --paginate "/repos/${REPO}/actions/runners" \
    | jq -r --arg n "$NAME" \
        '.runners[] | select(.name == $n) | "\(.status)\t\(.busy)\t\([.labels[].name] | join(","))"' \
    | head -1)

if [[ -z "$ROW" ]]; then
    echo "Runner $NAME is not yet listed by GitHub.  Check:"
    echo "  sudo $RUNNER_DIR/svc.sh status"
    echo "  journalctl -u 'actions.runner.*' -n 100 --no-pager"
    exit 1
fi

IFS=$'\t' read -r status busy labels <<<"$ROW"
if [[ "$status" == "online" ]]; then
    printf 'Runner %s is online (busy=%s, labels=%s)\n' "$NAME" "$busy" "$labels"
else
    printf 'Runner %s status: %s (labels=%s)\n' "$NAME" "$status" "$labels"
    echo "If this stays offline, troubleshoot with:"
    echo "  sudo $RUNNER_DIR/svc.sh status"
    echo "  journalctl -u 'actions.runner.*' -n 100 --no-pager"
    exit 1
fi
