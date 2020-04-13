#!/usr/bin/env bash
# CGI script to query RPM about *.rpm files online
# Authors:
# - Mikhail Novosyolov <mikhailnov@nixtux.ru>, 2020

set -e #fail on any unexpected error
set -f #disable globbing
#set -u # BAH01215: ./bashlib: line 82: value: unbound variable

# source bashlib (https://github.com/mikhailnov/bashlib)
. bashlib

# source config
. /etc/rpm-info-web-api.conf

# Preserve extantibility for other repo structures
# For now only rosa is supported, feel free to PR others
readonly STRUCTURE="rosa"
readonly platform="$(safe_param platform)"
readonly arch="$(safe_param arch)"
readonly repo="$(safe_param repo)"
readonly package="$(safe_param package)"
# Examples:
# query_fields=VERSION -> rpm -q --qf '%{VERSION}'
# query_fields=VERSION,SOURCERPM -> rpm -q --qf '%{VERSION};%{SOURCERPM}'
readonly query_fields="$(safe_param query_fields)"

_responce(){
    echo -n "
    <html>
    <body>
    $1
    </body>
    </html>"
}

repo_tpl=""
case "$STRUCTURE" in
# http://abf-downloads.rosalinux.ru/rosa2019.1/repository/x86_64/main/release/
	rosa )
		# repo = main/release
		repo_tpl="${ROOT_PATH}/%platform%/repository/%arch%/%repo%/"
	;;
	* )
		_responce "Unknown structure"
		exit
	;;
esac

for i in "$platform" "$arch" "$repo" "$package" "$query_fields"
do
	if [ -z "$i" ]; then
		_responce "Error: some fields are empty!"
		exit
	fi
done

rpm_q_cli=""
echo "$query_fields" | sed -e 's#,#\n#g' | while read -r line
do
	# prohibit any non alphanum characters here
	if echo "$line" | grep -qE '[[:alpha:].-]' ; then
		_responce "Non alphanum characters in query_fields are not allowed!"
		exit
	fi
	if [ -z "$rpm_q_cli" ]
		then rpm_q_cli="%{${line}}"
		else rpm_q_cli="${rpm_q_cli};%{${line}}"
	fi
done

if [ -z "$rpm_q_cli" ] ; then
	_responce "Resulting rpm query cli is empty!"
	exit
fi

repo_dir="$(echo "$repo_tpl" | sed -e "s,%platform%,${platform},g" -e "s,%arch%,${arch},g" -e "s,%repo%,${repo},g")"
if [ ! -d "$repo_dir" ]; then
	_responce "Target directory not found!"
	exit
fi
# Assume that package name starts with its name and a '-' symbol follows it
# Remember: shell globbing is offed by 'set -f'
# TODO: somehow better deal with multiple versions of one package being in the repo
pkg_file="${repo_dir}/$(ls -1v "$repo_dir" | grep "^${package}-" | head -n 1)"
if [ ! -f "$pkg_file" -o ! -r "$pkg_file" ]; then
	_responce "Package file is not accessible or does not exist!"
	exit
fi

readonly amon="/usr/local/lib/amon_rpm-info-web-api.so"
if [ ! -f "$amon" -o ! -r "amon" ]; then
	_responce "No amon found!"
	exit
fi

# We do not trust:
# - input data
# - rpm packages
# - macros in host rpm that is used to make queries
# We prevent any child code execution by amon
# If a binary rpm package tries to exploit rpm, it must not work
# If an RPM tag has a strange value like package=$(cat /etc/passwd),
# it must not work, to prevent shell expansion, we fork the shell under amon
# tr is from safe_param() of bashlib
rpm_answer="$(LD_PRELOAD="$amon" sh -c "/usr/bin/rpm -qp --qf "$rpm_q_cli" "$pkg_file"" | tr -d '$`<>"%;)(&+'"'")"

_responce "$rpm_answer"
