# CogniWatch Authentication System

Simple, secure login system for CogniWatch dashboard.

## Quick Start

1. **Set admin credentials** in your `.env` file:
   ```bash
   COGNIWATCH_ADMIN_USER=admin
   COGNIWATCH_ADMIN_PASSWORD=your-secure-password
   ```

2. **Start the server** - the admin user is created automatically on first login attempt

3. **Access the dashboard** at `http://localhost:9000`
   - You'll be redirected to `/login` if not authenticated
   - Use your admin credentials to login

## Features

✅ Session-based authentication (Flask sessions + cookies)  
✅ Password hashing with bcrypt  
✅ Protected routes (all except `/login` and `/health`)  
✅ Logout functionality  
✅ Auto-create admin from environment variables  

## Protected Routes

**No authentication needed:**
- `/login` - Login page
- `/health` - Health check endpoint
- `/static/*` - Static files (CSS, JS, images)
- `/api/auth/*` - Authentication endpoints

**Authentication required:**
- `/` - Main dashboard
- `/api/*` - All API endpoints
- All other routes

## API Endpoints

### Login
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your-password"
}

# Response 200 OK (sets session cookie):
{
  "success": true,
  "user": "admin",
  "role": "admin"
}
```

### Logout
```bash
POST /api/auth/logout

# Response 200 OK (clears session cookie):
{
  "success": true
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COGNIWATCH_ADMIN_USER` | `admin` | Admin username |
| `COGNIWATCH_ADMIN_PASSWORD` | `admin123` | Admin password (CHANGE IN PRODUCTION!) |
| `COGNIWATCH_SECRET_KEY` | _(random)_ | Flask secret key (generate for production) |
| `COGNIWATCH_SECURE_COOKIES` | `false` | Set to `true` for HTTPS deployments |
| `COGNIWATCH_TOKEN_EXPIRY` | `24` | Session expiry in hours |

## Database Schema

A `users` table is automatically created in `data/cogniwatch.db`:

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'viewer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

## Security Notes

### For Production Deployment:

1. **Change default password** immediately:
   ```bash
   COGNIWATCH_ADMIN_PASSWORD=<strong-password>
   ```

2. **Generate a secret key**:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
   Add to `.env`: `COGNIWATCH_SECRET_KEY=<generated-key>`

3. **Enable secure cookies** (HTTPS only):
   ```bash
   COGNIWATCH_SECURE_COOKIES=true
   ```

4. **Use environment variables** for credentials (never commit `.env` to git)

5. **Add rate limiting** (planned for future release)

## Files Modified

- `/home/neo/cogniwatch/database/schema.py` — Added `users` table
- `/home/neo/cogniwatch/webui/server.py` — Added login routes, auth middleware
- `/home/neo/cogniwatch/webui/auth.py` — Added user validation, session management
- `/home/neo/cogniwatch/webui/templates/login.html` — New login page
- `/home/neo/cogniwatch/webui/templates/dashboard.html` — Added logout button
- `/home/neo/cogniwatch/docker-compose.yml` — Added auth env vars
- `/home/neo/cogniwatch/.env` — Environment configuration

## Testing

1. Start the server
2. Navigate to `http://localhost:9000`
3. You should be redirected to `/login`
4. Login with `admin` / `admin123` (or your custom credentials)
5. You should see the dashboard
6. Click "Logout" - you should be redirected back to login
7. Try accessing `/api/agents` without login - should return 401

## Troubleshooting

**Can't login?**
- Check `.env` file has correct `COGNIWATCH_ADMIN_USER` and `COGNIWATCH_ADMIN_PASSWORD`
- Restart the server after changing credentials
- Check server logs for error messages

**Getting 401 errors?**
- Your session may have expired (24 hours by default)
- Re-login to get a new session

**Database errors?**
- Ensure `data/` directory exists and is writable
- Run `python3 database/schema.py` to initialize database
