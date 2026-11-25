"""Generates CampusCart_Assignment_Report.pdf (run with a Python that has reportlab)."""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (PageBreak, Paragraph, Preformatted, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "CampusCart_Assignment_Report.pdf")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=10)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13)
C = ParagraphStyle("C", parent=ss["Code"], fontSize=7.4, leading=9.2, backColor=colors.HexColor("#f3f3f3"),
                   borderPadding=3)
story = []


def h1(t): story.append(Paragraph(t, H1))
def h2(t): story.append(Paragraph(t, H2))
def p(t): story.append(Paragraph(t, B)); story.append(Spacer(1, 4))
def bl(items):
    for i in items: story.append(Paragraph("&bull; " + i, B))
    story.append(Spacer(1, 4))
def code(t): story.append(Preformatted(t.strip("\n"), C)); story.append(Spacer(1, 6))
def table(rows, widths):
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                           ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                           ("GRID", (0, 0), (-1, -1), .4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    rows2 = [[Paragraph(str(c), B) if i else Paragraph("<font color='white'>%s</font>" % c, B) for c in r]
             for i, r in enumerate(rows)]
    t = Table(rows2, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
                           ("GRID", (0, 0), (-1, -1), .4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t); story.append(Spacer(1, 6))


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def evidence(name, title):
    path = os.path.join(ROOT, "evidence", name)
    h2(title)
    if os.path.exists(path):
        code(open(path, encoding="utf-8", errors="replace").read()[:3500])
    else:
        p("<i>[Paste screenshot / output here after running the step - file evidence/%s]</i>" % name)


# ---------------- Title ----------------
story.append(Paragraph("Containerizing the CampusCart API", ParagraphStyle("T", parent=ss["Title"])))
p("<b>Cloud Computing Case Study Assignment</b> &mdash; BITS Pilani WILP<br/>"
  "Name: ____________ &nbsp; ID: ____________ &nbsp; Date: ____________")
p("Contents: 1 Problem &amp; assumptions; 2 Architecture; 3 Implementation; 4 Verification plan &amp; evidence; "
  "5 AWS console steps; 6 Demo script; 7 Trade-offs &amp; limitations; 8 Cleanup.")

h1("1. Problem and assumptions")
p("The CampusCart API behaves differently on developer laptops and the test server because runtime versions and "
  "installed packages differ. The team wants reproducible deployment without shipping a full guest OS per API instance. "
  "Containers share the host kernel and package app + exact dependencies in one immutable image.")
table([["Item", "Assumption"],
       ["Workload", "Stateless REST API (/health, /products, /orders). ~50 req/s peak at campus sale; small payloads."],
       ["Users", "Students (web/mobile) through a reverse proxy / load balancer."],
       ["State", "Orders live in a managed relational database (RDS PostgreSQL in cloud; PostgreSQL container as a local stand-in)."],
       ["Secrets", "DB password never in the image, Git or Dockerfile; supplied at deployment (Docker secret / AWS Secrets Manager)."],
       ["Targets", "Build &lt; 3 min; image &lt; 200 MB; zero HIGH/CRITICAL fixable CVEs; failover with no failed request after one instance stops; rollback &lt; 2 min (RTO)."],
       ["Environment", "Prayogshala Virtual Lab VM (Docker preinstalled) and/or AWS Console Lab EC2 t3a.small, ap-south-1."]],
      [3.2 * cm, 13.5 * cm])

h1("2. Architecture and reasoning")
code("""
 Client --> [ nginx proxy :8080 ] --+--> [ api1 container (campuscart-api:1.0.0) ] --+
                                    |                                              |--> [ PostgreSQL / RDS ]
                                    +--> [ api2 container (campuscart-api:1.0.0) ] --+     (data volume / managed)
                                                  ^
                          DB_HOST, DB_USER = env vars ; DB password = /run/secrets/db_password (secret)
""")
table([["Component", "Responsibility", "Security / trade-off"],
       ["API image", "Flask+gunicorn, stateless, /health", "Multistage, pinned python:3.12.5-slim-bookworm, nonroot user, only 8000 exposed, read-only FS"],
       ["nginx", "Round-robin, retries on failed upstream", "Single proxy is a SPOF locally; use ALB in cloud"],
       ["Database", "Persistent orders", "Outside the container so replicas are disposable"],
       ["Secret", "DB password", "Mounted file, not ENV baked into image; .dockerignore excludes secrets/"],
       ["Tags", "1.0.0 good, 1.1.0 deliberately faulty (FAIL_HEALTH)", "Immutable tags make rollback = redeploy old tag"]],
      [3 * cm, 6 * cm, 7.7 * cm])
p("<b>Containers vs VMs:</b> no guest OS per instance &rarr; seconds to start, MBs instead of GBs, but weaker isolation "
  "(shared kernel) &mdash; mitigated by nonroot user, read-only FS and image scanning.")

h1("3. Implementation (files)")
p("Project folder: <b>Desktop\\CC-Assignment</b>")
table([["File", "Purpose"],
       ["app/app.py", "API; config from env vars; secret read from /run/secrets"],
       ["app/requirements.txt", "Exact pinned dependency versions"],
       ["tests/test_api.py", "5 pytest unit tests"],
       ["Dockerfile / .dockerignore", "Multistage, nonroot, HEALTHCHECK, cache-friendly layer order"],
       ["docker-compose.yml, nginx/nginx.conf", "2 replicas + proxy + DB, secret wiring"],
       ["scripts/demo.sh", "One command per demo step; writes evidence/*.txt"],
       ["scripts/ec2-user-data.sh", "Installs Docker on EC2 at launch"]], [6 * cm, 10.7 * cm])
h2("Dockerfile")
code(read("Dockerfile"))
h2("docker-compose.yml")
code(read("docker-compose.yml"))
h2("nginx.conf")
code(read("nginx/nginx.conf"))
h2("Key application code (config & health)")
code("""
def database_url():                      # settings from environment
    host = os.getenv("DB_HOST"); user = os.getenv("DB_USER", "campuscart")
    pwd = read_secret("DB_PASSWORD")     # /run/secrets/db_password, else env at runtime
    ...
@app.get("/health")                      # used by HEALTHCHECK and proxy checks
def health(): 200 {"status":"ok","version":...} | 503 if DB down | 500 if FAIL_HEALTH=1
""")
story.append(PageBreak())

h1("4. Verification plan and evidence")
p("Each step is run with <font face='Courier'>./scripts/demo.sh &lt;step&gt;</font>; output is saved to evidence/ and "
  "reproduced below.")
table([["#", "Step / command", "Expected result"],
       ["1", "demo.sh test", "5 passed"],
       ["2", "demo.sh build", "campuscart-api:1.0.0 and :1.1.0 built"],
       ["3", "demo.sh scan", "0 fixable HIGH/CRITICAL; otherwise bump base image/dependency and rebuild (corrective action)"],
       ["4", "demo.sh secret; up", "api1, api2, proxy, db running; db healthy"],
       ["5", "demo.sh health", "HTTP 200 alternating between 2 hostnames; order stored; user=app"],
       ["6", "demo.sh failover", "api1 stopped; all requests still 200 served by api2"],
       ["7", "demo.sh release-bad", "1.1.0 reports unhealthy (500) &rarr; defect detected"],
       ["8", "demo.sh rollback", "1.0.0 redeployed; /health 200, version 1.0.0"],
       ["9", "demo.sh summary", "image size, user, ports, layer history"]],
      [0.8 * cm, 5 * cm, 10.9 * cm])
evidence("01-unit-tests.txt", "Evidence 1 - Unit tests (executed on author machine)")
evidence("02-build-1.0.0.txt", "Evidence 2 - Build")
evidence("03-scan-1.0.0.txt", "Evidence 3 - Vulnerability scan (Trivy)")
evidence("04-compose-ps.txt", "Evidence 4 - Running containers")
evidence("05-health.txt", "Evidence 5 - Health check / API / nonroot")
evidence("06-failover.txt", "Evidence 6 - Failover (api1 stopped)")
evidence("07-bad-release.txt", "Evidence 7 - Faulty release 1.1.0")
evidence("08-rollback.txt", "Evidence 8 - Rollback to 1.0.0")
evidence("09-image-summary.txt", "Evidence 9 - Image summary")

story.append(PageBreak())
h1("5. AWS Console steps (Prayogshala Console Lab)")
p("<b>Limits:</b> 60-minute session, ~$5 credit, region ap-south-1, only t3a.nano/micro/small/medium allowed. "
  "Student role may block ECR/RDS/Secrets Manager &mdash; fallbacks are given.")
h2("A. Start the lab")
bl(["Open <b>https://prayogshala.bits-pilani.ac.in</b> &rarr; Continue with BITS SSO &rarr; eLearn login.",
    "Open the <b>Console Lab</b> course &rarr; <b>Launch Lab</b> &rarr; <b>Launch AWS Console</b> (first launch takes 5-8 min) &rarr; <b>Open Console</b>.",
    "Confirm region = <b>Asia Pacific (Mumbai) ap-south-1</b> (top-right)."])
h2("B. Launch the Docker host (EC2)")
bl(["EC2 &rarr; Launch instance. Name: <b>campuscart-docker</b>. AMI: <b>Amazon Linux 2023</b>.",
    "Instance type: <b>t3a.small</b> (2 GB RAM; t3a.micro may be too small for Postgres+scan).",
    "Key pair: create new (.pem) or proceed without and use <b>EC2 Instance Connect</b> from the console.",
    "Network: Security group allow <b>SSH 22</b> (My IP) and <b>Custom TCP 8080</b> (My IP) for the demo.",
    "Storage 20 GiB gp3. Advanced details &rarr; <b>User data</b>: paste contents of <i>scripts/ec2-user-data.sh</i>.",
    "Launch; wait for 2/2 checks (~2 min). Select instance &rarr; <b>Connect</b> &rarr; EC2 Instance Connect &rarr; Connect.",
    "Verify: <font face='Courier'>docker --version; docker compose version</font> (wait 1-2 min after boot if missing)."])
h2("C. Get the project onto the instance")
bl(["Easiest: push the folder to your own GitHub repo (no secrets) and on EC2 run <font face='Courier'>git clone &lt;url&gt; && cd CC-Assignment</font>.",
    "Alternative: upload zip to S3 and <font face='Courier'>aws s3 cp</font>, or use Instance Connect paste for individual files."])
h2("D. Run the demo (on the EC2 terminal)")
code("""
chmod +x scripts/demo.sh
./scripts/demo.sh test && ./scripts/demo.sh build && ./scripts/demo.sh scan
./scripts/demo.sh secret && ./scripts/demo.sh up && ./scripts/demo.sh health
./scripts/demo.sh failover && ./scripts/demo.sh recover
./scripts/demo.sh release-bad && ./scripts/demo.sh rollback
./scripts/demo.sh summary
""")
p("Browser check: http://&lt;EC2-public-IP&gt;:8080/health (refresh &mdash; hostname changes between api1/api2).")
h2("E. Optional cloud-native extras (if permitted)")
bl(["<b>ECR:</b> Create private repo <i>campuscart-api</i>; push with <font face='Courier'>aws ecr get-login-password | docker login ...</font>, "
    "then <font face='Courier'>docker tag/push campuscart-api:1.0.0</font>; image tags set to <b>Immutable</b>; enable <b>Scan on push</b>.",
    "<b>Secrets Manager:</b> Store a secret <i>campuscart/db_password</i>; show retrieval with <font face='Courier'>aws secretsmanager get-secret-value</font>. "
    "If AccessDenied, state that the lab role blocks it and keep the Docker secret approach.",
    "<b>RDS:</b> The target design uses RDS PostgreSQL (db.t3.micro) in private subnets; in the time-limited lab the PostgreSQL container substitutes."])
h2("F. Capture screenshots")
bl(["EC2 instance running, security group rules, terminal output of each step, browser /health, ECR repo (if used)."])
h2("G. Alternative: Virtual Lab")
p("Launch <b>Introduction to DevOps (CSIST108)</b> VM in the Virtual Lab (Docker installed). Save the folder under "
  "<b>~/workspace</b> (everything else is lost at terminate), then run the same commands.")

h1("6. Demo script (5-7 minutes)")
bl(["Show Dockerfile: pinned base, deps-first caching, multistage, nonroot, HEALTHCHECK, no secrets.",
    "<b>test</b> &rarr; <b>build</b> &rarr; <b>scan</b>; show image size with <b>summary</b>.",
    "<b>up</b>, then browser/curl <b>/health</b> repeatedly: two instance names appear.",
    "POST an order, show it in GET /orders; mention it is in the DB, not the container.",
    "<b>failover</b>: stop api1; requests continue (200). <b>recover</b>.",
    "<b>release-bad</b>: 1.1.0 is unhealthy &rarr; <b>rollback</b> to 1.0.0; show /health version 1.0.0.",
    "Close with trade-offs and cleanup."])

h1("7. Trade-offs and limitations")
bl(["Containers share the host kernel: lighter than VMs but less isolated; mitigated with nonroot, read-only FS, scanning.",
    "Local nginx is a single point of failure; production would use an ALB across AZs with an orchestrator (ECS/EKS).",
    "Scan results depend on the vulnerability DB date; re-scan regularly. Base image is pinned for reproducibility, so patches require a deliberate bump.",
    "The local DB container is not highly available; RDS Multi-AZ is the production choice.",
    "1.1.0 'bad release' is simulated via a flag. Rollback here is manual; orchestrators automate it on failed health checks."])

h1("8. Cleanup (important)")
bl(["Run <font face='Courier'>./scripts/demo.sh down</font>.",
    "EC2 &rarr; select instance &rarr; Instance state &rarr; <b>Terminate</b> (not just Stop). Delete ECR repo/secret if created.",
    "Back on Prayogshala: <b>List Resources</b> to verify nothing is left, then <b>Stop Session</b>."])
p("<b>Submission checklist:</b> Dockerfile, build/run commands, health check result, image summary, rollback evidence, this report.")

SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                  bottomMargin=1.8 * cm, title="CampusCart Containerization").build(story)
print("wrote", OUT)
