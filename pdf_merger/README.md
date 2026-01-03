# 📄 Secure PDF Interleave Merger (Web App)

A modern, secure web application to merge scanned PDF documents. It specifically handles the common use case of scanning a stack of papers twice (once for fronts, once for backs in reverse order) and interleaving them into a single, correct PDF.

This application is designed to be **self-hosted** on a private network using **Tailscale**, ensuring that your documents never leave your secure environment.

## 🎯 Goal
To provide a simple, browser-based interface for merging "Fronts" and "Backs" PDF scans without sending data to third-party cloud PDF services.

![PDF Interleave Merger screencast](pdf_merger.gif)

## 🏗 Technical Stack

* **Language:** Python 3.13
* **Web Framework:** [Streamlit](https://streamlit.io/) (Reactive UI)
* **PDF Engine:** `pypdf` (High-performance PDF manipulation)
* **Deployment:** Docker & Docker Compose (Multi-stage builds)
* **Networking:** [Tailscale](https://tailscale.com/) (Sidecar pattern for private, secure access)

## 📋 Requirements

* **Docker Desktop** (or Docker Engine + Compose plugin) installed on the host machine.
* A **Tailscale** account (Free tier works perfectly).
* No public IP or port forwarding required (thanks to Tailscale).

## 🚀 Setup & Deployment

### 1. Clone the Project
Ensure you have the following files in your directory:
* `merge_pdf_web.py` (The application logic)
* `Dockerfile` (System-install configuration)
* `docker-compose.yml` (Sidecar orchestration)
* `pyproject.toml` (Dependency definitions)

### 2. Generate a Tailscale Auth Key
1.  Go to the [Tailscale Admin Console > Settings > Keys](https://login.tailscale.com/admin/settings/keys).
2.  Click **Generate auth key**.
3.  **Critical Configuration**:
    * ✅ **Reusable**: Enabled (Prevents "invalid key" errors on restarts).
    * ✅ **Ephemeral**: Enabled (Automatically cleans up the machine when Docker stops).
    * ✅ **Tags** (Optional): Apply tags if you use ACLs.

### 3. Configure Environment
Create a file named `.env` in the project root:

```bash
# .env file
TS_AUTHKEY=tskey-auth-YOUR-GENERATED-KEY-HERE
```

### 4. Deploy

Start the application stack:

```bash
docker compose up -d
```

## 🌐 Usage

### Accessing the App

Since the app runs inside a private Tailnet, you cannot access it via `localhost`.

1. Open your [Tailscale Admin Console](https://login.tailscale.com/admin/machines).
2. Find the machine named `pdf-merger`.
3. Copy its IP address (e.g., `100.x.y.z`) or MagicDNS name.
4. Visit `http://100.x.y.z:8501` in your browser.

### 🔒 Enabling HTTPS (Recommended)

You can provision a valid SSL certificate automatically using Tailscale. This command configures the sidecar proxy to accept secure connections on port 443 and forward them to your app.

Run this command **once** while the container is running:

```bash
docker exec ts-pdf-merger tailscale serve --https=443 8501
```

Once enabled, you can access the app securely at:
**`https://pdf-merger.your-tailnet.ts.net`**

*(Note: You can find your full Tailnet URL in the Tailscale admin console).*

## 🛠 Troubleshooting

**Container Crash Loop (Invalid Key)**
If the Tailscale container keeps restarting with `backend error: invalid key`:

1. Stop the stack: `docker compose down`
2. **Delete the corrupted state volume:**
```bash
docker volume rm pdf-merger-web_ts-state
```


3. Ensure your key in `.env` is **Reusable**.
4. Restart: `docker compose up -d`

**Build Errors (DNS)**
If the build fails with `failed to lookup address information`:

```bash
# Build using host network
docker build --network=host -t pdf-merger-web .
```

## 📄 License

**MIT License**

Copyright (c) 2025 Pietro F. Maggi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
