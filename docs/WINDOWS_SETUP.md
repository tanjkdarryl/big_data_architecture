# Windows Setup Guide

Complete guide for setting up the Blockchain Data Ingestion System on Windows 10/11.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installing Docker Desktop](#installing-docker-desktop)
3. [Configuring WSL2](#configuring-wsl2)
4. [Project Setup](#project-setup)
5. [Running the Project](#running-the-project)
6. [Windows-Specific Commands](#windows-specific-commands)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Windows Version | Windows 10 (Build 19041+) | Windows 11 |
| RAM | 8 GB | 16 GB |
| Free Disk Space | 10 GB | 20 GB |
| Processor | 64-bit with virtualization | Modern multi-core |

### Required Software

1. **Docker Desktop for Windows** (includes Docker Compose)
2. **Git for Windows** (for cloning the repository)
3. **Windows Terminal** (recommended, comes with Windows 11)

### Check Your Windows Version

1. Press `Win + R`
2. Type `winver` and press Enter
3. Ensure you have Windows 10 Build 19041 or higher

---

## Installing Docker Desktop

### Step 1: Enable Virtualization

Docker requires hardware virtualization. Check if it's enabled:

1. Open **Task Manager** (`Ctrl + Shift + Esc`)
2. Go to the **Performance** tab
3. Look for "Virtualization: Enabled" at the bottom

If virtualization is disabled:
1. Restart your computer
2. Enter BIOS/UEFI (usually `F2`, `F12`, `Del`, or `Esc` during startup)
3. Find virtualization settings (Intel VT-x or AMD-V)
4. Enable it and save changes

### Step 2: Download Docker Desktop

1. Visit [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Click "Download for Windows"
3. Run the installer (`Docker Desktop Installer.exe`)

### Step 3: Install Docker Desktop

1. Run the installer
2. **Important:** Check "Use WSL 2 instead of Hyper-V" when prompted
3. Follow the installation wizard
4. Restart your computer when prompted

### Step 4: First Launch

1. Open Docker Desktop from the Start menu
2. Accept the terms of service
3. Wait for Docker to fully start (whale icon stops animating)
4. If prompted to install WSL2, follow the instructions

### Step 5: Verify Installation

Open **Command Prompt** or **PowerShell** and run:

```cmd
docker --version
docker compose version
```

Expected output:
```
Docker version 24.x.x, build xxxxxxx
Docker Compose version v2.x.x
```

---

## Configuring WSL2

Docker Desktop uses WSL2 (Windows Subsystem for Linux 2) as its backend.

### Enable WSL2 (if not already enabled)

Open **PowerShell as Administrator** and run:

```powershell
wsl --install
```

If WSL is already installed, ensure WSL2 is the default:

```powershell
wsl --set-default-version 2
```

### Configure Docker Desktop WSL Integration

1. Open Docker Desktop
2. Click the gear icon (Settings)
3. Go to **Resources** > **WSL Integration**
4. Enable "Enable integration with my default WSL distro"
5. Click "Apply & Restart"

---

## Project Setup

### Step 1: Clone the Repository

Open **Command Prompt**, **PowerShell**, or **Windows Terminal**:

```cmd
cd C:\Users\YourUsername\Documents
git clone https://github.com/your-repo/big_data_architecture.git
cd big_data_architecture
```

### Step 2: Configure Environment

Copy the environment template:

**Command Prompt:**
```cmd
copy .env.example .env
```

**PowerShell:**
```powershell
Copy-Item .env.example .env
```

### Step 3: Review Configuration (Optional)

Open `.env` in a text editor to review settings:

```cmd
notepad .env
```

Default settings work fine for most users.

---

## Running the Project

### Option 1: Using the Start Script (Recommended)

**Double-click method:**
1. Navigate to the `scripts` folder
2. Double-click `start.bat`

**Command Prompt:**
```cmd
cd scripts
start.bat
```

**PowerShell:**
```powershell
cd scripts
.\start.ps1
```

> **Note:** If PowerShell shows an execution policy error, run:
> ```powershell
> powershell -ExecutionPolicy Bypass -File start.ps1
> ```

### Option 2: Using Docker Compose Directly

```cmd
docker compose up --build -d
```

### Accessing the Services

After startup completes (wait ~30 seconds):

| Service | URL | Description |
|---------|-----|-------------|
| Dashboard | http://localhost:3001 | Monitoring interface |
| API | http://localhost:8000 | Collector REST API |
| ClickHouse | http://localhost:8123 | Database HTTP interface |

Open the dashboard:
```cmd
start http://localhost:3001
```

### Viewing Logs

```cmd
docker compose logs -f
```

Press `Ctrl + C` to stop viewing logs.

### Stopping the Project

```cmd
docker compose down
```

### Full Cleanup

To remove all data and start fresh:

**Command Prompt:**
```cmd
cd scripts
cleanup.bat
```

**PowerShell:**
```powershell
cd scripts
.\cleanup.ps1
```

---

## Windows-Specific Commands

### Command Reference

| Task | Windows Command | macOS/Linux Equivalent |
|------|-----------------|------------------------|
| Open URL in browser | `start http://localhost:3001` | `open http://localhost:3001` |
| Copy file | `copy .env.example .env` | `cp .env.example .env` |
| Delete folder | `rmdir /s /q folder` | `rm -rf folder` |
| List directory | `dir` | `ls -la` |
| Check disk space | `wmic logicaldisk get size,freespace,caption` | `df -h` |
| Find process on port | `netstat -ano \| findstr :3001` | `lsof -i :3001` |
| Kill process by PID | `taskkill /PID 12345 /F` | `kill -9 12345` |
| Environment variables | `set` | `env` |

### Docker Commands (Same on All Platforms)

```cmd
# View running containers
docker ps

# View all containers
docker ps -a

# View container logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild and start
docker compose up --build -d

# Enter ClickHouse shell
docker exec -it clickhouse clickhouse-client

# Check container resource usage
docker stats
```

### ClickHouse Queries via Command Line

```cmd
# Connect to ClickHouse
docker exec -it clickhouse clickhouse-client

# Or run a single query
docker exec -it clickhouse clickhouse-client --query "SELECT count() FROM blockchain_data.bitcoin_blocks"
```

---

## Troubleshooting

### Docker Desktop Won't Start

**Symptom:** Docker Desktop hangs on "Starting..." or shows error

**Solutions:**

1. **Restart Docker Desktop:**
   - Right-click the Docker icon in the system tray
   - Click "Restart"

2. **Check WSL2:**
   ```powershell
   wsl --status
   ```
   If there's an issue, update WSL:
   ```powershell
   wsl --update
   ```

3. **Check virtualization is enabled** (see Prerequisites)

4. **Restart Windows**

5. **Reset Docker Desktop:**
   - Open Docker Desktop settings
   - Go to "Troubleshoot"
   - Click "Reset to factory defaults"

### "docker: command not found"

**Symptom:** Command Prompt doesn't recognize `docker`

**Solutions:**

1. Ensure Docker Desktop is running
2. Restart your terminal after installing Docker
3. Check PATH environment variable:
   ```cmd
   echo %PATH%
   ```
   Should include `C:\Program Files\Docker\Docker\resources\bin`

4. Reinstall Docker Desktop

### Port Already in Use

**Symptom:** Error about port 3001, 8000, or 8123 being in use

**Solution:**

1. Find the process using the port:
   ```cmd
   netstat -ano | findstr :3001
   ```

2. Note the PID (last column)

3. Kill the process:
   ```cmd
   taskkill /PID <PID> /F
   ```

4. Or stop all Docker containers:
   ```cmd
   docker stop $(docker ps -q)
   ```

### Containers Keep Restarting

**Symptom:** Services don't stay running, logs show crashes

**Solution:**

1. Check Docker resource allocation:
   - Open Docker Desktop Settings
   - Go to Resources
   - Ensure at least 4GB RAM allocated

2. Check logs for specific errors:
   ```cmd
   docker compose logs clickhouse
   docker compose logs collector
   docker compose logs dashboard
   ```

3. Rebuild containers:
   ```cmd
   docker compose down
   docker compose up --build -d
   ```

### Slow Performance

**Symptom:** Dashboard loads slowly, data collection is slow

**Solutions:**

1. **Increase Docker resources:**
   - Docker Desktop > Settings > Resources
   - Increase Memory to 8GB if available
   - Increase CPUs to at least 4

2. **Use WSL2 file system:**
   - Store project files in WSL2 filesystem for better I/O:
   ```powershell
   wsl
   cd ~
   git clone https://github.com/your-repo/big_data_architecture.git
   ```

3. **Disable Windows Defender real-time scanning for project folder:**
   - Windows Security > Virus & threat protection
   - Manage settings > Exclusions > Add exclusion

### Permission Denied Errors

**Symptom:** Scripts fail with "Access Denied" or permission errors

**Solutions:**

1. **Run as Administrator:**
   - Right-click Command Prompt or PowerShell
   - Select "Run as administrator"

2. **PowerShell execution policy:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **File ownership:**
   - Right-click the project folder
   - Properties > Security > Edit
   - Give your user full control

### Network Issues

**Symptom:** Containers can't communicate, API errors

**Solutions:**

1. **Reset Docker networks:**
   ```cmd
   docker network prune -f
   docker compose down
   docker compose up -d
   ```

2. **Check Windows Firewall:**
   - Windows Security > Firewall & network protection
   - Ensure Docker is allowed through firewall

3. **Restart Docker Desktop networking:**
   - Docker Desktop > Settings > Resources > Network
   - Click "Reset"

### WSL2 Memory Issues

**Symptom:** WSL2 or Docker using too much memory

**Solution:**

Create a `.wslconfig` file in your user folder:

1. Open Notepad
2. Add:
   ```ini
   [wsl2]
   memory=4GB
   processors=4
   swap=2GB
   ```
3. Save as `C:\Users\YourUsername\.wslconfig`
4. Restart WSL:
   ```powershell
   wsl --shutdown
   ```

---

## FAQ

### Q: Can I use Windows without WSL2?

**A:** Yes, but not recommended. Docker Desktop can use Hyper-V backend, but WSL2 provides better performance. During Docker Desktop installation, ensure "Use WSL 2 instead of Hyper-V" is selected.

### Q: Do I need to install Linux in WSL?

**A:** No, Docker Desktop handles this automatically. It installs a minimal WSL2 distribution for Docker's backend.

### Q: Can I access files from both Windows and WSL?

**A:** Yes!
- Windows files from WSL: `/mnt/c/Users/YourName/...`
- WSL files from Windows: `\\wsl$\Ubuntu\home\...` (in File Explorer)

### Q: How do I update Docker Desktop?

**A:** Docker Desktop updates automatically, or:
1. Click the Docker icon in system tray
2. Select "Check for Updates"
3. Install any available updates

### Q: Why is the dashboard at port 3001 instead of 3000?

**A:** Port 3001 is used to avoid conflicts with other applications that commonly use port 3000 (like other Node.js projects).

### Q: Can I run this alongside other Docker projects?

**A:** Yes! Each project uses its own Docker network. Just ensure port 3001, 8000, and 8123 aren't used by other projects. Modify `.env` if needed.

### Q: How do I completely uninstall everything?

**A:**
1. Run `cleanup.bat` or `cleanup.ps1`
2. Delete the project folder
3. (Optional) Uninstall Docker Desktop from Windows Settings > Apps

---

## Additional Resources

- [Docker Desktop Documentation](https://docs.docker.com/desktop/windows/)
- [WSL2 Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
- [Project README](../README.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Architecture Overview](ARCHITECTURE.md)

---

## Getting Help

If you encounter issues not covered here:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review Docker Desktop troubleshooting
3. Search existing issues in the project repository
4. Ask your instructor for help
