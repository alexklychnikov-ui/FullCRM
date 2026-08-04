#!/bin/bash
set -eu

# Step 3: deploy user (keep root SSH)
if ! id deploy >/dev/null 2>&1; then
  useradd -m -s /bin/bash deploy
  usermod -aG docker deploy
fi

install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
if [ -f /root/.ssh/authorized_keys ]; then
  cp /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
  chown deploy:deploy /home/deploy/.ssh/authorized_keys
  chmod 600 /home/deploy/.ssh/authorized_keys
fi

SUDOERS=/etc/sudoers.d/deploy
cat > "$SUDOERS" <<'EOF'
deploy ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker compose, /usr/local/bin/docker-compose
EOF
chmod 440 "$SUDOERS"

# Verify deploy can run docker
su - deploy -c "docker ps --format '{{.Names}}' | head -3"
echo "deploy_user=ok"
