#!/bin/bash
#
# pwdreset-wrapper.sh — Restricted password reset script
# Runs as root (via sudo) but enforces admin protection
# Only the pwdreset Linux user is allowed to invoke this via sudo
#
# Usage: pwdreset-wrapper.sh <username> <new_password>
#

# --- ADMIN BLOCKLIST ---
# These accounts can NEVER be reset through this script
ADMIN_ACCOUNTS=(
    "Administrator"
    "user"
    "admin"
    "ai-agent"
    "pwdreset"
    "krbtgt"
    "Guest"
)

# --- VALIDATION ---
if [ "$#" -ne 2 ]; then
    echo "ERROR: Usage: pwdreset-wrapper.sh <username> <new_password>"
    exit 1
fi

USERNAME="$1"
NEW_PASSWORD="$2"

# Check against admin blocklist
for admin in "${ADMIN_ACCOUNTS[@]}"; do
    if [ "$USERNAME" = "$admin" ]; then
        echo "ERROR: Cannot reset password for admin account '$USERNAME'. This action is blocked by policy."
        logger "PWDRESET BLOCKED: Attempt to reset admin account '$USERNAME' by $(whoami)"
        exit 2
    fi
done

# Verify the user exists in Samba
if ! samba-tool user show "$USERNAME" > /dev/null 2>&1; then
    echo "ERROR: User '$USERNAME' does not exist in the domain."
    exit 3
fi

# Verify the user is NOT a Domain Admin (defense in depth — even if blocklist is incomplete)
if samba-tool group listmembers "Domain Admins" 2>/dev/null | grep -qw "$USERNAME"; then
    echo "ERROR: User '$USERNAME' is a member of Domain Admins. Password reset blocked by policy."
    logger "PWDRESET BLOCKED: Attempt to reset Domain Admin '$USERNAME' by $(whoami)"
    exit 4
fi

# --- EXECUTE PASSWORD RESET ---
echo "Resetting password for user '$USERNAME'..."
if samba-tool user setpassword "$USERNAME" --newpassword="$NEW_PASSWORD" 2>&1; then
    echo "SUCCESS: Password reset for user '$USERNAME'"
    logger "PWDRESET SUCCESS: Password reset for '$USERNAME' by $(whoami)"
    exit 0
else
    echo "ERROR: Failed to reset password for user '$USERNAME'"
    logger "PWDRESET FAILED: Password reset attempt for '$USERNAME' by $(whoami)"
    exit 5
fi