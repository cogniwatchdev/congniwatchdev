# CogniWatch UI Deployment - Manual Steps for Jannie

**Date:** 2026-03-08  
**Status:** SSH Authentication Blocked - Manual Deployment Required  
**VPS:** 45.63.21.236 (cogniwatch.dev)

---

## 🚨 The Problem

SSH port 22 is OPEN but authentication is failing. The deployment package is ready at:
- **Local:** `/tmp/cogniwatch-templates.tar.gz` (28KB)
- **Contains:** 10 HTML templates + server.py + static files

---

## ✅ Option 1: Copy-Paste Deployment (RECOMMENDED)

### Step 1: Connect to VPS Console

From your Windows machine:
1. Go to **Vultr Control Panel** → https://my.vultr.com/
2. Click on your VPS instance (cogniwatch)
3. Click **"Launch Console"** (web-based console)
4. Login as: `cogniwatch` (or `root` if needed)

### Step 2: Create Deployment Directory

```bash
mkdir -p /tmp/cogniwatch-upload
cd /tmp/cogniwatch-upload
```

### Step 3: Download Deployment Package

The package is already on the VPS from previous deployment. Check if it exists:

```bash
ls -la /home/cogniwatch/webui/
```

If the old files are there, we just need to replace them.

### Step 4: Upload New Files

**Method A: Using browser console copy-paste**

1. On your local machine, extract the tarball:
```bash
cd /home/neo/cogniwatch
tar -xzf /tmp/cogniwatch-templates.tar.gz -C /tmp/
```

2. Create a single base64-encoded file:
```bash
cd /home/neo/cogniwatch/webui
tar -czf /tmp/ui-deploy.tar.gz templates/ server.py static/
base64 /tmp/ui-deploy.tar.gz > /tmp/ui-deploy.b64
cat /tmp/ui-deploy.b64
```

3. **Copy the ENTIRE output** (it will be long base64 text)

4. **On VPS console**, paste and decode:
```bash
mkdir -p /tmp/ui-upload
cd /tmp/ui-upload
# Paste the base64 content here, then:
base64 -d > ui-deploy.tar.gz << 'EOF'
[PASTE BASE64 CONTENT HERE]
EOF

# Extract and deploy
tar -xzf ui-deploy.tar.gz
cp -r templates/* /home/cogniwatch/webui/templates/cogniwatch/
cp server.py /home/cogniwatch/webui/
cp -r static/* /home/cogniwatch/webui/static/
docker restart cogniwatch-webui
```

**Method B: Using Python one-liner HTTP upload**

1. **On VPS console**, start a simple receiver:
```bash
cd /home/cogniwatch
python3 -c "
import http.server, tarfile, os, shutil, subprocess
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        l = int(self.headers['Content-Length'])
        d = self.rfile.read(l)
        os.makedirs('/tmp/up', exist_ok=True)
        open('/tmp/up/d.tar.gz','wb').write(d)
        tarfile.open('/tmp/up/d.tar.gz','r:gz').extractall('/tmp/up')
        if os.path.exists('/home/cogniwatch/webui/templates/cogniwatch'):
            shutil.rmtree('/home/cogniwatch/webui/templates/cogniwatch')
        shutil.copytree('/tmp/up/templates/cogniwatch', '/home/cogniwatch/webui/templates/cogniwatch')
        if os.path.exists('/tmp/up/server.py'):
            shutil.copy('/tmp/up/server.py', '/home/cogniwatch/webui/server.py')
        if os.path.exists('/tmp/up/static'):
            shutil.rmtree('/home/cogniwatch/webui/static')
            shutil.copytree('/tmp/up/static', '/home/cogniwatch/webui/static')
        subprocess.run(['docker','restart','cogniwatch-webui'])
        self.send_response(200); self.end_headers(); self.wfile.write(b'Deployed!')
http.server.HTTPServer(('',8888), H).handle_request()
print('Waiting for upload on port 8888...')
" &
```

2. **On your local machine**, upload the file:
```bash
curl -X POST -F "file=@/tmp/cogniwatch-templates.tar.gz" http://45.63.21.236:8888/
```

3. **On VPS console**, check if it worked:
```bash
curl http://localhost:8888/
```

---

## ✅ Option 2: Fix SSH Access

### Check SSH Configuration

On VPS console:
```bash
sudo cat /etc/ssh/sshd_config | grep -E "PasswordAuthentication|PubkeyAuthentication|PermitRootLogin"
sudo systemctl status ssh
```

### Add Your SSH Key

1. **Generate SSH key** on Windows (if you don't have one):
```powershell
ssh-keygen -t ed25519 -C "cogniwatch-deploy"
```

2. **Copy public key** (`C:\Users\YourName\.ssh\id_ed25519.pub`)

3. **On VPS console**, add to authorized_keys:
```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# Paste your public key here
chmod 600 ~/.ssh/authorized_keys
chown -R $USER:$USER ~/.ssh
```

4. **Test SSH** from your machine:
```bash
ssh cogniwatch@45.63.21.236
```

---

## ✅ Option 3: Docker Volume Mount Workaround

If the container is running, we can use docker exec to copy files:

1. **On VPS console**, check container status:
```bash
docker ps | grep cogniwatch
```

2. **Create a file receiver inside container**:
```bash
docker exec -it cogniwatch-webui python3 -c "
import http.server, tarfile, os
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        l = int(self.headers['Content-Length'])
        tarfile.open(fileobj=self.rfile, mode='r:gz').extractall('/cogniwatch/webui')
        self.send_response(200); self.end_headers()
http.server.HTTPServer(('0.0.0.0', 8889), H).handle_request()
" &
```

3. **Upload from local**:
```bash
curl -X POST --data-binary @/tmp/cogniwatch-templates.tar.gz http://45.63.21.236:8889/
```

---

## 📋 Verification Steps (After Deployment)

1. **Check container status:**
```bash
docker ps | grep cogniwatch-webui
docker logs cogniwatch-webui --tail 50
```

2. **Test web pages:**
```bash
curl -I http://localhost:9000/
curl -I http://localhost:9000/scan
curl -I http://localhost:9000/agents
curl http://localhost:9000/api/agents | head -20
```

3. **Check file timestamps:**
```bash
ls -la /home/cogniwatch/webui/templates/cogniwatch/
ls -la /home/cogniwatch/webui/server.py
```

4. **Test from browser:**
   - https://cogniwatch.dev/
   - https://cogniwatch.dev/scan
   - https://cogniwatch.dev/agents

---

## 🆘 Emergency Contact

If stuck, screenshot the error and share in Discord.

---

## 📦 Deployment Package Contents

```
cogniwatch-templates.tar.gz (28KB)
├── templates/cogniwatch/
│   ├── base.html (Tabler UI base)
│   ├── dashboard.html (main page)
│   ├── scan.html (scan interface)
│   ├── agents.html (agent list - 254 agents)
│   ├── analytics.html
│   ├── security.html
│   ├── faq.html
│   ├── about.html
│   ├── help.html
│   └── settings.html
├── server.py (Flask server)
└── static/ (Tabler CSS/JS assets)
```

---

## 🎯 Success Criteria

- ✅ cogniwatch.dev loads new Tabler UI
- ✅ All 9 navigation pages work
- ✅ Dashboard shows 254 agents
- ✅ "Scan Now" button functional
- ✅ GitHub link works
