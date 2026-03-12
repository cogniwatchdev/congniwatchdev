# 🔥 CogniWatch Firewall Configuration

Complete firewall rules for securing CogniWatch deployments.

---

## ⚠️ Critical: SSH First

**BEFORE enabling any firewall:**

```bash
# Ensure SSH access is allowed
sudo ufw allow ssh
# OR if using custom SSH port
sudo ufw allow 2222/tcp
```

---

## 🎯 UFW (Uncomplicated Firewall) Rules

### Basic Configuration (Development)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow CogniWatch Web UI
sudo ufw allow 9000/tcp comment "CogniWatch Dashboard"
```

### Production Configuration (Recommended)

```bash
# Reset UFW (if needed)
sudo ufw --force reset

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (with rate limiting)
sudo ufw limit ssh comment "SSH with rate limiting"

# Allow HTTPS if using nginx
sudo ufw allow 'Nginx Full'

# Allow HTTP for Let's Encrypt (can disable after cert obtained)
sudo ufw allow 80/tcp comment "HTTP for Let's Encrypt"

# Allow Web UI from local network only
# Replace 192.168.0.0/24 with your trusted network
sudo ufw allow from 192.168.0.0/24 to any port 9000 proto tcp comment "CogniWatch - Local Network"

# If you need remote access from specific IP
# Replace 203.0.113.0/24 with your office/home IP
sudo ufw allow from 203.0.113.0/24 to any port 9000 proto tcp comment "CogniWatch - Remote Access"

# Enable UFW
sudo ufw enable

# Verify rules
sudo ufw status verbose
```

### Advanced Configuration (Maximum Security)

```bash
# Enable UFW with logging
sudo ufw logging on

# Deny all incoming by default
sudo ufw default deny incoming

# Allow established connections
sudo ufw allow out on any

# SSH from specific IPs only
sudo ufw allow from 203.0.113.5/32 to any port 22 proto tcp comment "SSH - Admin Only"
sudo ufw allow from 198.51.100.10/32 to any port 22 proto tcp comment "SSH - Admin 2"

# Web UI from VPN network only
sudo ufw allow from 10.8.0.0/24 to any port 9000 proto tcp comment "CogniWatch - VPN Access"

# Nginx (if using reverse proxy)
sudo ufw allow from 10.8.0.0/24 to any port 80 proto tcp
sudo ufw allow from 10.8.0.0/24 to any port 443 proto tcp

# Rate limit repeated connection attempts
sudo ufw limit 9000/tcp comment "Web UI rate limit"

# Enable
sudo ufw enable
```

### UFW Status Check

```bash
# Show all rules
sudo ufw status numbered

# Show verbose status
sudo ufw status verbose

# Check if active
sudo ufw status
```

### Managing Rules

```bash
# Delete a rule by number
sudo ufw delete 3

# Disable UFW
sudo ufw disable

# Reset UFW
sudo ufw --force reset
```

---

## 🔧 iptables Rules (Advanced)

### Basic iptables Configuration

```bash
# Flush existing rules
sudo iptables -F
sudo iptables -X

# Set default policies
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -m state --state NEW -j ACCEPT

# Allow CogniWatch Web UI from specific network
sudo iptables -A INPUT -p tcp --dport 9000 -s 192.168.0.0/24 -m state --state NEW -j ACCEPT

# Rate limit new connections to prevent DoS
sudo iptables -A INPUT -p tcp --dport 9000 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 9000 -m state --state NEW -m recent --update --seconds 60 --hitcount 10 -j DROP

# Allow ping (optional)
sudo iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# Log dropped packets (optional)
sudo iptables -A INPUT -j LOG --log-prefix "IPTables-Dropped: " --log-level 4
```

### Save iptables Rules

```bash
# Install persistence
sudo apt install -y iptables-persistent

# Save current rules
sudo netfilter-persistent save

# Rules saved to:
# /etc/iptables/rules.v4 (IPv4)
# /etc/iptables/rules.v6 (IPv6)
```

### iptables Status

```bash
# View all rules
sudo iptables -L -n -v

# View with line numbers
sudo iptables -L -n --line-numbers
```

---

## ☁️ Cloud Provider Firewall Rules

### DigitalOcean UFW Setup

```bash
# DigitalOcean has cloud firewall in addition to UFW
# Configure both!

# In DO Control Panel > Networking > Firewalls:
# Inbound Rules:
# - TCP 22 (SSH) from your IP
# - TCP 9000 from your network
# - TCP 80 from anywhere (if using nginx/letsencrypt)
# - TCP 443 from anywhere (if using nginx/letsencrypt)
```

### AWS Security Groups

**Security Group Rules:**

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | Your IP | Admin access |
| Custom | TCP | 9000 | 10.0.0.0/8 | CogniWatch Internal |
| HTTP | TCP | 80 | 0.0.0.0/0 | Let's Encrypt |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Web UI (nginx) |

```bash
# Using AWS CLI
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 9000 \
    --cidr 10.0.0.0/8

aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 22 \
    --cidr YOUR_IP/32
```

### Google Cloud Firewall

```bash
# Allow SSH from specific IP
gcloud compute firewall-rules create allow-ssh-admin \
    --allow tcp:22 \
    --source-ranges YOUR_IP/32 \
    --network default

# Allow CogniWatch from internal network
gcloud compute firewall-rules create allow-cogniwatch \
    --allow tcp:9000 \
    --source-ranges 10.128.0.0/9 \
    --network default

# Allow HTTP/HTTPS for nginx
gcloud compute firewall-rules create allow-http-https \
    --allow tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --network default
```

---

## 🚦 Rate Limiting Configuration

### UFW Rate Limiting

```bash
# SSH rate limiting (built-in)
sudo ufw limit ssh

# Custom rate limiting for web UI
# (Requires manual iptables, UFW doesn't support custom rate limits)
```

### Fail2ban Integration

Fail2ban works alongside firewalls to block malicious IPs:

```bash
# Install
sudo apt install -y fail2ban

# Create jail for CogniWatch
sudo nano /etc/fail2ban/jail.local
```

**Jail Configuration:**

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[cogniwatch-nginx]
enabled = true
port = http,https
filter = cogniwatch-nginx
logpath = /var/log/nginx/error.log
maxretry = 10

[cogniwatch-auth]
enabled = true
port = 9000
filter = cogniwatch-auth
logpath = /var/log/cogniwatch/*.log
maxretry = 5
bantime = 7200
```

**Filter Configuration:**

```bash
sudo nano /etc/fail2ban/filter.d/cogniwatch-auth.conf
```

```ini
[Definition]
failregex = ^.*Failed login attempt.*<HOST>.*$
            ^.*Invalid authentication.*<HOST>.*$
ignoreregex =
```

```bash
# Restart fail2ban
sudo systemctl restart fail2ban

# Check status
sudo fail2ban-client status cogniwatch-auth
```

---

## 🛡️ Port Scanning Protection

### Detect Port Scans

```bash
# Install psad (Port Scan Attack Detector)
sudo apt install -y psad

# Configure
sudo nano /etc/psad/psad.conf

# Enable
sudo systemctl enable psad
sudo systemctl start psad
```

### Kernel-Level Protection

```bash
# Enable SYN cookies (DoS protection)
echo "net.ipv4.tcp_syncookies = 1" | sudo tee -a /etc/sysctl.conf

# Disable IP source routing
echo "net.ipv4.conf.all.accept_source_route = 0" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.conf.default.accept_source_route = 0" | sudo tee -a /etc/sysctl.conf

# Enable IP spoofing protection
echo "net.ipv4.conf.all.rp_filter = 1" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.conf.default.rp_filter = 1" | sudo tee -a /etc/sysctl.conf

# Ignore ICMP redirects
echo "net.ipv4.conf.all.accept_redirects = 0" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.conf.default.accept_redirects = 0" | sudo tee -a /etc/sysctl.conf

# Log suspicious packets
echo "net.ipv4.conf.all.log_martians = 1" | sudo tee -a /etc/sysctl.conf

# Apply settings
sudo sysctl -p
```

---

## 🔍 Firewall Testing

### Test Port Access

```bash
# From remote machine, test if port 9000 is accessible
nc -zv YOUR_SERVER_IP 9000

# Or using nmap
nmap -Pn -p 9000 YOUR_SERVER_IP

# Test from server itself
curl http://localhost:9000/health
```

### Test Rate Limiting

```bash
# Test SSH rate limiting (from external)
for i in {1..10}; do
    ssh -o ConnectTimeout=2 user@YOUR_SERVER_IP exit
done

# Check if blocked
sudo ufw status
sudo fail2ban-client status
```

### Audit Firewall Rules

```bash
# Check all UFW rules
sudo ufw status verbose

# Check iptables rules
sudo iptables -L -n -v

# Check for open ports
sudo ss -tlnp

# External scan (from different machine)
nmap -sT -p- YOUR_SERVER_IP
```

---

## 📋 Checklist

### Pre-Deployment

- [ ] SSH access configured and tested
- [ ] Firewall rules documented
- [ ] Admin IPs identified for access
- [ ] Backup access method (console) available

### Post-Deployment

- [ ] SSH port accessible from admin IPs only
- [ ] Web UI (9000) accessible from trusted networks only
- [ ] Rate limiting enabled
- [ ] Fail2ban running
- [ ] Logging enabled
- [ ] Rules persisted (survive reboot)

### Regular Maintenance

- [ ] Review firewall logs weekly
- [ ] Update admin IP list as needed
- [ ] Test backup access quarterly
- [ ] Audit open ports monthly

---

## 🚨 Emergency Access

**If you lock yourself out:**

1. **Cloud Console Access:**
   - DigitalOcean: Recovery Console
   - AWS: EC2 Instance Connect / Serial Console
   - GCP: Serial Console
   - Linode: LISH Console

2. **Disable Firewall via Console:**
   ```bash
   sudo ufw disable
   # OR
   sudo iptables -F
   ```

3. **Restore Access:**
   ```bash
   sudo ufw allow ssh
   sudo ufw enable
   ```

---

**Remember: Always test firewall changes from an external location before closing your current session!**
