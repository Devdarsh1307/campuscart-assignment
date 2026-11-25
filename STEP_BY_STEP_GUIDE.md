# CampusCart – Detailed Step-by-Step Guide (AWS Console Lab, from zero to rollback)

Everything below is done **on an EC2 Linux instance** launched from the Prayogshala AWS Console Lab. Estimated time: 35–45 min (session limit 60 min — prepare first, launch later).

---
## PART 0 – Prepare on your laptop BEFORE starting the lab clock
1. Put the `CC-Assignment` folder in a **private GitHub repo** (secrets/ and .env are already git-ignored):
   ```
   cd %USERPROFILE%\Desktop\CC-Assignment
   git init && git add . && git commit -m "CampusCart"
   gh repo create campuscart-assignment --private --source . --push
   ```
   (No GitHub? Zip the folder; you will paste files via Instance Connect or use S3 – see Part 3 alt.)
2. Open `scripts\ec2-user-data.sh` and keep it ready to copy.
3. Create a Word/Docs file to paste **screenshots** in as you go (name each "Evidence N").

## PART 1 – Start the lab
1. Browser → https://prayogshala.bits-pilani.ac.in → **Continue with BITS SSO** → log in with eLearn credentials.
2. Open the **Console Lab** course → **Launch Lab** → **Launch AWS Console** (first launch takes 5–8 minutes; wait).
3. Click **Open Console**. Top-right region must read **Asia Pacific (Mumbai) ap-south-1**. Change it if not.
4. Session timer starts (60 min). Do not close the Prayogshala tab.

## PART 2 – Launch the Docker host (EC2)
1. Search bar → **EC2** → **Launch instance**.
2. Name: `campuscart-docker`.
3. AMI: **Amazon Linux 2023** (Free-tier eligible, 64-bit x86).
4. Instance type: **t3a.small** (only t3a.nano/micro/small/medium are allowed).
5. Key pair: **Proceed without a key pair** (we will use browser-based EC2 Instance Connect). If Instance Connect is blocked, create a key pair `cc-key` (.pem) and use SSH.
6. Network settings → **Edit**:
   - Auto-assign public IP: **Enable**
   - Security group: create new `campuscart-sg`
   - Rule 1: SSH, TCP 22, Source **My IP**
   - Rule 2: Custom TCP **8080**, Source **My IP**
7. Storage: **20 GiB gp3**.
8. Expand **Advanced details** → scroll to **User data** → paste the entire content of `scripts\ec2-user-data.sh`.
9. Click **Launch instance** → **View all instances**.
10. Wait for Instance state **Running** and Status check **2/2 passed** (~2 min). 📸 *Evidence A: instance running + security group inbound rules.*
11. Select the instance → **Connect** → tab **EC2 Instance Connect** → **Connect**. A browser terminal opens.
12. Verify Docker (wait 1–2 more min if "command not found" – user-data is still running):
    ```
    docker --version
    docker compose version
    ```
    If `permission denied`: run `newgrp docker` (or prefix commands with `sudo`).
    📸 *Evidence B.*

## PART 3 – Get the project on the instance
```
git clone https://github.com/<your-user>/campuscart-assignment.git
cd campuscart-assignment
ls
chmod +x scripts/demo.sh
```
(Private repo: use a Personal Access Token as password, or make the repo public temporarily – never put secrets in it.)

Alt (no GitHub): `mkdir -p CC && cd CC`, then for each file `nano <path>` and paste (create folders `app tests nginx scripts evidence secrets` first). Needed: Dockerfile, .dockerignore, docker-compose.yml, app/app.py, app/requirements.txt, tests/test_api.py, nginx/nginx.conf, scripts/demo.sh.

## PART 4 – Run each step (one command each; screenshot every output)
| # | Command | What it does | Success looks like |
|---|---------|--------------|--------------------|
| 1 | `./scripts/demo.sh test` | Runs pytest in a throwaway container | `5 passed` |
| 2 | `./scripts/demo.sh build` | Builds `campuscart-api:1.0.0` (good) and `:1.1.0` (faulty on purpose) | "Successfully built/naming to ...:1.0.0" |
| 3 | `./scripts/demo.sh scan` | Trivy scan, fails on fixable HIGH/CRITICAL | `Total: 0` (or see fix below) |
| 4 | `./scripts/demo.sh secret` | Generates random DB password into `secrets/db_password.txt` (outside the image) | "secret file ready" |
| 5 | `./scripts/demo.sh up` | Starts db, api1, api2, nginx | 4 containers `Up`, db `healthy` |
| 6 | `./scripts/demo.sh health` | 6x /health via proxy, creates + lists an order, shows non-root user, checks no password in image history | Two different `instance` hostnames; `uid=...(app)`; final number `0` |
| 7 | `./scripts/demo.sh failover` | Stops api1 | All codes `200`, hostname always api2 |
| 8 | `./scripts/demo.sh recover` | Starts api1 again | – |
| 9 | `./scripts/demo.sh release-bad` | Deploys 1.1.0 | containers `(unhealthy)`, HTTP `500` |
| 10 | `./scripts/demo.sh rollback` | Redeploys 1.0.0 | `(healthy)`, `"version":"1.0.0"` |
| 11 | `./scripts/demo.sh summary` | Image size, user, port, layers | Size ≈ 150–200 MB, User=app, 8000/tcp |

Each step saves its output into `evidence/`. Also open **http://\<EC2 public IPv4\>:8080/health** in your browser after step 5 and refresh several times: the `instance` value alternates. 📸

### If something fails
- **Scan finds HIGH/CRITICAL**: this *is* the corrective-action evidence. Edit `Dockerfile` base to the latest patch (e.g. `python:3.12.x-slim-bookworm`), bump the vulnerable package in `requirements.txt`, rebuild (`./scripts/demo.sh build`), re-scan; screenshot **before and after**.
- **Trivy image pull is slow / blocked**: say so in limitations; alternatively `docker scout quickview campuscart-api:1.0.0` or `docker run --rm aquasec/trivy image --severity HIGH,CRITICAL campuscart-api:1.0.0` once.
- **api containers restarting**: `docker compose logs api1` (usually secret file missing → run step 4).
- **Port 8080 not reachable in browser**: re-check the security group rule and your public IP (it changes); use `curl localhost:8080/health` on the instance instead.
- **Out of memory**: use t3a.medium.

## PART 5 – (Optional) AWS-native extras, only if permitted (screenshot the AccessDenied if blocked and state it)
**ECR**: ECR → Create repository → Private, name `campuscart-api`, **Tag immutability: Enabled**, **Scan on push: Enabled**. In **View push commands** copy the 4 commands; run them on the instance (the instance needs an IAM role/credentials; if not available, skip). Push `1.0.0` and `1.1.0`.
**Secrets Manager**: Store a new secret → Other type → key `password` → name `campuscart/db_password`. Show it exists (do not screenshot the value).
**RDS**: Describe only (design: PostgreSQL db.t3.micro, private subnets, SG allowing 5432 from API SG only). Do not create in a 60-min lab.

## PART 6 – Collect deliverables
Copy files off the instance for your report (Instance Connect terminal): `cat evidence/*.txt` and paste into your document, or `git add evidence && git commit && git push` from the instance. Required submission items:
- Dockerfile ✔ (project root)
- Build and run commands ✔ (Part 4 steps 2, 5)
- Health check result ✔ (`evidence/05-health.txt`)
- Image summary ✔ (`evidence/09-image-summary.txt`)
- Rollback evidence ✔ (`evidence/07` + `evidence/08`)
Then copy `evidence/` back to your laptop folder and run `python make_report.py` (needs `pip install reportlab`) to regenerate the PDF with real outputs embedded.

## PART 7 – Clean up (do not skip; protects your credit)
1. On the instance: `./scripts/demo.sh down`
2. EC2 console → Instances → select → **Instance state → Terminate instance** (Stop is not enough). Confirm state **Terminated**.
3. Delete ECR repo / secret if you created them.
4. Back on Prayogshala: **List Resources** (verify empty) → **Stop Session**.

## PART 8 – 5-minute viva/demo talk track
1. Problem: "works on my laptop" → drift in runtime/package versions; containers fix this without a guest OS per instance.
2. Show Dockerfile: pinned base, `requirements.txt` copied first (layer cache), multistage, non-root, HEALTHCHECK, only 8000 exposed.
3. Secrets and state: password only in `secrets/` (ignored by Git and Docker), orders in Postgres (RDS in cloud).
4. Run test → build → scan → up → `/health` alternating instances.
5. Stop api1 → still 200. Release 1.1.0 → unhealthy → rollback to 1.0.0 by redeploying the old immutable tag.
6. Trade-offs: shared kernel, single nginx, DB not HA; production = ECS/EKS + ALB + RDS Multi-AZ + ECR scanning.

## Alternative: Virtual Lab (no AWS)
Launch **Introduction to DevOps (CSIST108)** VM (Docker preinstalled). Clone/copy the project into `~/workspace` (the only persistent place), then do Parts 3–4 and 6. Terminate the VM when done.
