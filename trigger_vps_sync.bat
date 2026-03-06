#!/bin/bash
# Trigger VPS Brain Sync
# =====================
# Runs sync on VPS manually

echo "Triggering Brain sync on VPS..."

ssh -o ConnectTimeout=10 root@164.68.111.47 "/root/brain_sync.sh"

echo "Done! Check VPS log: ssh root@164.68.111.47 'tail -f /var/log/brain_sync.log'"
