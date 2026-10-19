#!/usr/bin/env bash
# Install a safe, read-only coordinator on Ubuntu ARM64/x86_64 OCI Always Free.
# Run on a newly provisioned Ubuntu VM as root with sudo. No credentials needed.
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then echo "Use sudo to run the setup." >&2; exit 1; fi
if ! command -v apt-get >/dev/null; then echo "Supported distribution: Ubuntu/Debian with systemd." >&2; exit 1; fi
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 ca-certificates git
getent passwd lucia-factory >/dev/null || useradd --system --create-home --home-dir /var/lib/lucia-factory --shell /usr/sbin/nologin lucia-factory
install -d -m 0750 -o lucia-factory -g lucia-factory /var/lib/lucia-factory
install -d -m 0755 /opt/lucia-factory
source_dir="$(mktemp -d)"
trap 'rm -rf "$source_dir"' EXIT
git clone --depth 1 https://github.com/clucaina/NPL-CANONICAL.git "$source_dir/repo"
install -m 0644 "$source_dir/repo/cloud_factory/oci_supervisor.py" /opt/lucia-factory/oci_supervisor.py
python3 -m py_compile /opt/lucia-factory/oci_supervisor.py
cat >/etc/systemd/system/lucia-factory.service <<'UNIT'
[Unit]
Description=Lucia Lab Read-Only Cloud Coordinator (public projects)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=lucia-factory
Group=lucia-factory
WorkingDirectory=/var/lib/lucia-factory
ExecStart=/usr/bin/python3 /opt/lucia-factory/oci_supervisor.py
Restart=always
RestartSec=35
StartLimitIntervalSec=0
UMask=0077
Environment=LUCIA_FACTORY_HOME=/var/lib/lucia-factory
Environment=LUCIA_FACTORY_INTERVAL_SECONDS=7200
EnvironmentFile=-/etc/lucia-factory.env
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/lucia-factory
MemoryMax=7G
CPUQuota=80%
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6

[Install]
WantedBy=multi-user.target
UNIT
if [[ ! -f /etc/lucia-factory.env ]]; then
  printf '%s\n' '# Optional: LUCIA_OLLAMA_MODEL=qwen2.5-coder:3b (only after Ollama is installed locally)' > /etc/lucia-factory.env
  chmod 0600 /etc/lucia-factory.env
fi
systemctl daemon-reload
systemctl enable --now lucia-factory.service
systemctl --no-pager status lucia-factory.service || true
printf '%s\n' 'Coordinator installed. Runs only PUBLIC project checks. No inbound port opened.' \
 'View logs: sudo journalctl -u lucia-factory -n 30 --no-pager' \
 'Local state: /var/lib/lucia-factory/last_run.json' \
 'Privacy: do not add pericial data or access keys to public issue bodies.'
