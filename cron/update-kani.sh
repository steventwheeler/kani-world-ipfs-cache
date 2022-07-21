#!/usr/bin/env bash

CREATOR_ADDRESS="${CREATOR_ADDRESS:-KANIGZX2NQKJKYJ425BWYKCT5EUHSPBRLXEJLIT2JHGTWOJ2MLYCNIVHFI}"
IPFS_NODE="http://${IPFS_HOST:-ipfs}:${IPFS_PORT:-5001}"

set -Eeuo pipefail
trap cleanup SIGINT SIGTERM ERR EXIT

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)

usage() {
  cat << EOF # remove the space between << and EOF, this is due to web plugin issue
Usage: $(basename "${BASH_SOURCE[0]}") [-h] [-v]

Pin the Kani World ASA images to this IPFS node.

Available options:

-h, --help      Print this help and exit
-v, --verbose   Print script debug info
EOF
  exit
}

cleanup() {
  trap - SIGINT SIGTERM ERR EXIT
}

setup_colors() {
  if [[ -t 2 ]] && [[ -z "${NO_COLOR-}" ]] && [[ "${TERM-}" != "dumb" ]]; then
    NOFORMAT='\033[0m' RED='\033[0;31m' GREEN='\033[0;32m' ORANGE='\033[0;33m' BLUE='\033[0;34m' PURPLE='\033[0;35m' CYAN='\033[0;36m' YELLOW='\033[1;33m'
  else
    NOFORMAT='' RED='' GREEN='' ORANGE='' BLUE='' PURPLE='' CYAN='' YELLOW=''
  fi
}

msg() {
  echo >&2 -e "${1-}"
}

die() {
  local msg=$1
  local code=${2-1} # default exit status 1
  msg "$msg"
  exit "$code"
}

parse_params() {
  while :; do
    case "${1-}" in
    -h | --help) usage ;;
    -v | --verbose) set -x ;;
    --no-color) NO_COLOR=1 ;;
    -?*) die "Unknown option: $1" ;;
    *) break ;;
    esac
    shift
  done

  args=("$@")

  return 0
}

function load_ipfs_cids() {
  next="0"
  while [[ "${next}" != "null" ]]; do
    json="$(curl -sSL "${INDEXER_HOST:-https://algoindexer.algoexplorerapi.io}/v2/assets?limit=1000&creator=${CREATOR_ADDRESS}&next=${next}")"
    next="$(echo "${json}" | jq -r '."next-token"')"
    echo "${json}" | jq -r '.assets[] | .params.url' | sed -E 's!(^https://gateway.pinata.cloud/ipfs/|^ipfs://|#i$|\?.*$)!!g'
  done
}

function exists() {
  json="$(curl -sSL -X POST "${IPFS_NODE}/api/v0/files/ls?arg=%2F${1}")"
  if [[ "$(echo "${json}" | jq -r '.Type')" == "error" ]]; then
    return 1
  fi
  return 0
}
function cp() {
  curl -sSL -X POST "${IPFS_NODE}/api/v0/files/cp?arg=%2Fipfs%2F${1}&arg=%2F${1}" > /dev/null
}
function pin() {
  curl -sSL -X POST "${IPFS_NODE}/api/v0/pin/add?recursive=true&arg=${1}" > /dev/null
}

parse_params "$@"
setup_colors


msg "${CYAN}Loading ASAs for ${CREATOR_ADDRESS}:${NOFORMAT}"

for cid in $(load_ipfs_cids); do
  msg "${CYAN}Pinning: ${cid}${NOFORMAT}"
  if exists "${cid}"; then
    msg "${GREEN}  Already exists.${NOFORMAT}"
    continue
  fi

  msg "${CYAN}  Copying to local node...${NOFORMAT}"
  cp "${cid}" || exit 1
  msg "${CYAN}  Pinning to local node...${NOFORMAT}"
  pin "${cid}" || exit 1
done
