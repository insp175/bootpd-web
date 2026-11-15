#!/bin/sh
set -eu
[ "$(uname -s)" = Darwin ] || { echo 'macOS is required'; exit 1; }
[ "$(id -u)" = 0 ] || { echo 'Run: sudo ./install.sh'; exit 1; }
owner_uid=${SUDO_UID:-0}
[ "$owner_uid" -gt 0 ] || { echo 'Run sudo from a regular user account'; exit 1; }
/usr/bin/python3 --version
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
install_dir='/Library/BootpdPanel'
[ ! -L "$install_dir" ] || { echo 'Installation path must not be a symbolic link'; exit 1; }
if [ -e /var/run/bootpd-panel.sock ]; then echo 'Stop the helper first'; exit 1; fi
mkdir -p "$install_dir"
chown root:wheel "$install_dir"
chmod 755 "$install_dir"
for name in helper.py core.py; do
  rm -f "$install_dir/$name"
  install -o root -g wheel -m 644 "$project_dir/$name" "$install_dir/$name"
done
printf '%s\n' "Installed. Run in a separate terminal:" "sudo /usr/bin/python3 -I /Library/BootpdPanel/helper.py --uid $owner_uid"
