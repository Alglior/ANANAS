# Medium Risk Security Findings

## 1. Alembic Fallback Default Credentials
**File:** `alembic/env.py` (lines 6–10)

When `SQLALCHEMY_DATABASE_URI` is not set, Alembic falls back to hardcoded defaults:
```python
pg_user = os.environ.get("POSTGRES_USER", "ananas_user")
pg_pass = os.environ.get("POSTGRES_PASSWORD", "password")
```
If environment variables are missing or misconfigured in production, Alembic will connect using `ananas_user`/`password`, which an attacker could exploit if they can trigger migrations.

**Recommendation:** Raise an explicit error instead of falling back to defaults:
```python
if not db_uri:
    raise RuntimeError("SQLALCHEMY_DATABASE_URI environment variable is required")
```

---

## 2. Database SSL Not Enforced
**File:** `app.py` (line 120)

When client certificates are not all provided, the connection falls back to `sslmode=prefer`:
```python
db_uri = f"{db_uri}{separator}sslmode=prefer"
```
`prefer` allows unencrypted connections. An attacker on the network could intercept credentials and queries in plaintext.

**Recommendation:** Use `sslmode=require` or `sslmode=verify-full` for production:
```python
db_uri = f"{db_uri}{separator}sslmode=require"
```

---

## 3. No HTTPS / TLS Configured
**File:** `nginx/nginx.conf` (line 37)

Nginx only listens on port 80 with no SSL/TLS termination:
```nginx
listen 80 default_server;
```
The `nginx/certs/` directory exists but is empty. All traffic — including login credentials and session cookies — travels in plaintext.

**Recommendation:** 
- Populate `nginx/certs/` with Let's Encrypt certificates (e.g., via Certbot or cert-manager).
- Add a redirect from HTTP to HTTPS, then use `listen 443 ssl` in nginx.conf.

---

## 4. Docker Port Exposure on All Interfaces
**File:** `docker-compose.yml` (line 15)

Port 80 is bound to `0.0.0.0` by default:
```yaml
ports:
  - "80:80"
```
This exposes the application on every network interface of the host, including public-facing ones if the server has them.

**Recommendation:** Restrict to localhost if using an external reverse proxy (Traefik, Cloudflare, etc.):
```yaml
ports:
  - "127.0.0.1:80:80"
```

---

## 5. Predictable Passwords in Seed Script
**File:** `scripts/seed_users.py` (line 44)

Fake users are seeded with predictable passwords:
```python
password = generate_password_hash(f"password{i}")
# e.g., password1, password2, password3...
```
While hashed, if these users accidentally reach production, attackers can trivially brute-force login.

**Recommendation:** Either remove the seed script in production builds or use cryptographically random passwords:
```python
import secrets
password = generate_password_hash(secrets.token_hex(16))
```
Alternatively, exclude `scripts/seed_users.py` from production Docker images via `.dockerignore`.

---

## 6. Admin Ban Endpoint Lacks Dedicated Rate Limiting
**File:** `src/admin_routes.py` (line 68)

The ban/unban endpoint relies only on the global rate limiter (`100 requests/hour per IP`). For a high-privilege action, this is too permissive. An attacker with admin access could flood the endpoint.

**Recommendation:** Add a stricter rate limit:
```python
@limiter.limit("20 per hour")
@bp.route("/api/users/<int:user_id>/ban", methods=["POST"])
@login_required
def ban_user(user_id):
    ...
```
