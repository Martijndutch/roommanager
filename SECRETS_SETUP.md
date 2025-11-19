# Secrets Management Setup - sv ARC Room Booking

## ✅ Current Configuration

The application now uses **environment variables** for all secrets, stored securely in `/etc/arcrooms/secrets.env`.

### File Locations

1. **Secrets File**: `/etc/arcrooms/secrets.env`
   - Permissions: `600` (root only)
   - Loaded automatically by systemd on service start
   - Persists across reboots

2. **Systemd Service**: `/etc/systemd/system/arcrooms.service`
   - Configured with `EnvironmentFile=/etc/arcrooms/secrets.env`

3. **Application**: `/home/martijn/arcRooms/app.py`
   - Reads from environment variables: `os.getenv('AZURE_TENANT_ID')`, etc.

### Environment Variables

```bash
AZURE_TENANT_ID       # Azure AD tenant ID
AZURE_CLIENT_ID       # Azure AD application client ID
AZURE_CLIENT_SECRET   # Azure AD application secret
FLASK_SECRET_KEY      # Flask session encryption key (persistent)
REDIRECT_URI          # OAuth callback URL
```

## 🔒 Security Features

✅ **Secrets not in code repository**
- `config.json` added to `.gitignore`
- Backup kept at `config.json.backup` (not tracked)

✅ **File permissions secured**
- `/etc/arcrooms/` directory: `700` (only root access)
- `secrets.env` file: `600` (only root can read/write)

✅ **Session secret persists**
- Sessions remain valid across application restarts
- No more user logouts on service restart

✅ **Automatic restart**
- Service starts automatically on boot
- No manual intervention required

## 🔄 How to Update Secrets

### 1. Edit the secrets file (requires sudo):
```bash
sudo nano /etc/arcrooms/secrets.env
```

### 2. Restart the service:
```bash
sudo systemctl restart arcrooms.service
```

### 3. Verify it's working:
```bash
sudo systemctl status arcrooms.service
curl http://localhost:5010/arcrooms/
```

## 🚨 IMPORTANT: Rotate Azure Client Secret

⚠️ **The current `AZURE_CLIENT_SECRET` was previously exposed in git.**

You should rotate it in Azure Portal:

1. Go to Azure Portal → Azure Active Directory
2. Navigate to App registrations → your application
3. Go to "Certificates & secrets"
4. Delete the old secret
5. Create a new client secret
6. Update `/etc/arcrooms/secrets.env` with the new value:
   ```bash
   sudo nano /etc/arcrooms/secrets.env
   # Update AZURE_CLIENT_SECRET=<new_secret>
   ```
7. Restart the service:
   ```bash
   sudo systemctl restart arcrooms.service
   ```

## 📋 View Current Configuration (without exposing secrets)

```bash
# View service configuration
cat /etc/systemd/system/arcrooms.service

# Check which environment variables are set (values hidden)
sudo grep -o '^[A-Z_]*' /etc/arcrooms/secrets.env

# View service status
sudo systemctl status arcrooms.service
```

## 🔐 Backup and Recovery

### Create backup of secrets:
```bash
sudo cp /etc/arcrooms/secrets.env /etc/arcrooms/secrets.env.backup
sudo chmod 600 /etc/arcrooms/secrets.env.backup
```

### Restore from backup:
```bash
sudo cp /etc/arcrooms/secrets.env.backup /etc/arcrooms/secrets.env
sudo systemctl restart arcrooms.service
```

## 🧪 Testing After Reboot

To verify the system works automatically after reboot:

```bash
# Reboot the system
sudo reboot

# After reboot, check service status
sudo systemctl status arcrooms.service

# Test the application
curl http://localhost:5010/arcrooms/
```

The service should start automatically and work without any manual intervention.

## 📝 Summary of Changes

| Before | After |
|--------|-------|
| Secrets in `config.json` (tracked in git) | Secrets in `/etc/arcrooms/secrets.env` (secure) |
| Session secret regenerated on restart | Session secret persists across restarts |
| Manual configuration needed | Fully automated, survives reboots |
| Security risk: exposed credentials | Security: root-only access to secrets |

## ✅ Security Checklist

- [x] Secrets moved to environment variables
- [x] Secrets file secured with 600 permissions
- [x] config.json added to .gitignore
- [x] Session secret persists across restarts
- [x] Service auto-starts on boot
- [ ] **TODO: Rotate Azure client secret** (see warning above)
- [ ] **TODO: Remove config.json from git history** (if committed previously)

## 🗑️ Removing Secrets from Git History (if needed)

If `config.json` with secrets was previously committed to git:

```bash
# Install git-filter-repo (safer than filter-branch)
sudo apt install git-filter-repo

# Remove config.json from entire git history
cd /home/martijn/arcRooms
git filter-repo --path config.json --invert-paths

# Force push (be careful!)
git push origin --force --all
```

**Note**: This rewrites git history. Coordinate with team members if applicable.
