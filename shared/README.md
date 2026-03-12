# 🤝 CogniWatch Collaboration Space

**For Clawdia + Neo to collaborate on CogniWatch features**

---

## 📁 HOW TO USE

### For Clawdia (on winclaw/WSL):

**Read files:**
```bash
# Copy from dellclaw to winclaw
scp neo@192.168.0.245:/home/neo/cogniwatch/shared/* ~/cogniwatch-collab/
```

**Write/Update:**
1. Edit files locally on winclaw
2. Copy back to dellclaw:
```bash
scp ~/cogniwatch-collab/* neo@192.168.0.245:/home/neo/cogniwatch/shared/
```

### For Neo (on dellclaw):

Files live at: `/home/neo/cogniwatch/shared/`

Just edit directly!

---

## 📄 FILES

| File | Purpose |
|------|---------|
| `discord-integration.md` | Discord integration ideas + spec |
| `design-notes.md` | General design discussions |
| `todo-collab.md` | Shared TODO list |

---

## 🚀 BETTER WAY Coming Soon

We'll move to a **GitHub private repo** soon:
- Proper version control
- Both can edit simultaneously
- Change history
- Issue tracking

For now, SCP works!

---

## 🎯 CURRENT PROJECTS

1. **Discord Integration** (Clawdia's idea)
2. **Authentication** (in progress)
3. **Framework Logos** (pending)
4. **Public Launch** (after auth done)

---

*Questions? Ask in Discord #neo channel!*
