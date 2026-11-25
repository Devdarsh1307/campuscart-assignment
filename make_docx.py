"""Builds Panth_Devdarsh_Assignment.docx from the lab-report template (same styles/layout)."""
import copy
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.environ["REPORT_TEMPLATE"]
OUT = os.path.join(ROOT, "Panth_Devdarsh_Assignment.docx")
IMG = os.path.join(ROOT, "diagrams")
CODE_IMG = os.path.join(ROOT, "diagrams", "code")
CUR, LAST_H3 = 0, "Code listing"
import itertools
CODE_N = itertools.count(1)
os.makedirs(IMG, exist_ok=True)


def rd(rel, limit=None):
    t = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
    t = "\n".join(ln.split("\r")[-1] for ln in t.split("\n"))
    t = "".join(ch for ch in t if ch in "\n\t" or ord(ch) >= 32)
    return t if limit is None else t[:limit]


# ---------------- diagrams ----------------
def box(ax, x, y, w, h, text, color="#dce6f1", fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=color, ec="#1f4e79", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color="#444"))


def diagram_local():
    f, ax = plt.subplots(figsize=(8, 3.6)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 5)
    box(ax, 0.1, 2, 1.4, 1, "Client\n(browser/curl)", "#ffffff")
    box(ax, 2.2, 2, 1.8, 1, "nginx proxy\n:8080", "#fff2cc")
    box(ax, 5, 3.3, 2.4, 1, "api1\ncampuscart-api:1.0.0")
    box(ax, 5, 0.7, 2.4, 1, "api2\ncampuscart-api:1.0.0")
    box(ax, 8.2, 2, 1.6, 1, "PostgreSQL\n(RDS in cloud)", "#d9ead3")
    for a in [(1.5, 2.5, 2.2, 2.5), (4, 2.8, 5, 3.7), (4, 2.2, 5, 1.2), (7.4, 3.7, 8.2, 2.8), (7.4, 1.2, 8.2, 2.2)]:
        arrow(ax, *a)
    ax.text(6.2, 0.15, "DB_HOST, DB_USER = env vars   |   DB password = /run/secrets/db_password", ha="center", fontsize=7.5, style="italic")
    f.savefig(os.path.join(IMG, "arch_local.png"), dpi=170, bbox_inches="tight"); plt.close(f)


def diagram_cloud():
    f, ax = plt.subplots(figsize=(8, 4.2)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 6)
    box(ax, 0.1, 2.5, 1.3, 1, "Users", "#ffffff")
    box(ax, 1.9, 2.5, 1.9, 1, "Application Load\nBalancer :80\nhealth: /health", "#fff2cc")
    ax.add_patch(FancyBboxPatch((4.3, 0.8), 3.4, 4.4, boxstyle="round,pad=0.02", fc="#f4f9ff", ec="#1f4e79", ls="--"))
    ax.text(6, 5.0, "Auto Scaling Group (min 1, desired 2, max 3)", ha="center", fontsize=8)
    box(ax, 4.6, 3.3, 2.8, 1.1, "EC2 (AZ-a)\nDocker: campuscart-api:1.0.0")
    box(ax, 4.6, 1.2, 2.8, 1.1, "EC2 (AZ-b)\nDocker: campuscart-api:1.0.0")
    box(ax, 8.2, 3.6, 1.7, 0.9, "ECR\nimmutable tags\nscan on push", "#e6d9f2", 7.5)
    box(ax, 8.2, 2.0, 1.7, 0.9, "Secrets Manager\nDB password", "#f8cbad", 7.5)
    box(ax, 8.2, 0.4, 1.7, 0.9, "RDS PostgreSQL\n(managed DB)", "#d9ead3", 7.5)
    for a in [(1.4, 3, 1.9, 3), (3.8, 3.2, 4.6, 3.8), (3.8, 2.8, 4.6, 1.8), (7.4, 3.8, 8.2, 4.0), (7.4, 1.8, 8.2, 1.0), (7.4, 3.5, 8.2, 2.5)]:
        arrow(ax, *a)
    ax.text(5, 0.1, "CloudWatch CPU 50% target-tracking policy drives scale-out / scale-in", ha="center", fontsize=7.5, style="italic")
    f.savefig(os.path.join(IMG, "arch_cloud.png"), dpi=170, bbox_inches="tight"); plt.close(f)


diagram_local(); diagram_cloud()

# ---------------- document ----------------
d = docx.Document(TEMPLATE)
body = d.element.body
sect = body.find(qn("w:sectPr"))
for el in list(body):
    if el is not sect:
        body.remove(el)

fig_no = {}


def para(text="", style="Normal", align=None, bold=None, size=None, italic=None):
    p = d.add_paragraph(style=style)
    if text:
        r = p.add_run(text)
        r.bold = bold; r.italic = italic
        if size: r.font.size = Pt(size)
    if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def pagebreak():
    d.add_paragraph().add_run().add_break(docx.enum.text.WD_BREAK.PAGE)


def h1(t):
    global CUR
    head = t.split(".")[0]
    CUR = int(head) if head.isdigit() else CUR; pagebreak(); d.add_paragraph(t, style="Heading 1")
def h2(t): d.add_paragraph(t, style="Heading 2")
def h3(t):
    global LAST_H3
    LAST_H3 = t.split(": ", 1)[-1]; d.add_paragraph(t, style="Heading 3")
def bullets(items):
    for i in items: d.add_paragraph(i, style="List Bullet")


def shade(p, fill="F2F2F2"):
    pPr = p._p.get_or_add_pPr()
    s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:fill"), fill); pPr.append(s)


def code(text, size=None, cap=None, chunk=55, wrap=105):
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 17)
    lines = []
    for ln in text.rstrip("\n").replace("\t", "    ").split("\n"):
        while len(ln) > wrap:
            lines.append(ln[:wrap]); ln = "    " + ln[wrap:]
        lines.append(ln)
    cap = cap or LAST_H3
    parts = [lines[i:i + chunk] for i in range(0, len(lines), chunk)]
    for n, part in enumerate(parts, 1):
        cw, lh, pad = 10, 24, 14
        w = max(380, cw * max(len(x) for x in part) + 2 * pad)
        im = Image.new("RGB", (w, lh * len(part) + 2 * pad), "#1e1e1e")
        dr = ImageDraw.Draw(im)
        for i, ln in enumerate(part):
            dr.text((pad, pad + i * lh), ln, font=font, fill="#d4d4d4")
        os.makedirs(CODE_IMG, exist_ok=True)
        path = os.path.join(CODE_IMG, "code_%03d.png" % next(CODE_N))
        im.save(path)
        label = cap + (" (part %d of %d)" % (n, len(parts)) if len(parts) > 1 else "")
        image(path, CUR, label, min(15.5, 15.5 * w / 1100))


def caption(chapter, text):
    fig_no[chapter] = fig_no.get(chapter, 0) + 1
    para("Figure %d.%d: %s" % (chapter, fig_no[chapter], text), align="c", size=9)


def image(path, chapter, cap, width=15.5):
    p = para(align="c"); p.add_run().add_picture(path, width=Cm(width)); caption(chapter, cap)


def shot(name, chapter, cap, width=15.5):
    image(os.path.join(ROOT, "screenshots", name + ".png"), chapter, cap, width)


def placeholder(chapter, cap, what):
    t = d.add_table(rows=1, cols=1); t.style = "Table Grid"
    c = t.rows[0].cells[0]; c.text = ""
    pp = c.paragraphs[0]; pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = pp.add_run("\n[ INSERT SCREENSHOT ]\n%s\n" % what); r.italic = True; r.font.size = Pt(9)
    r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    caption(chapter, cap)


def table(rows, widths=None, header=True):
    t = d.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.rows[i].cells[j]; c.text = ""
            r = c.paragraphs[0].add_run(str(v)); r.font.size = Pt(9)
            if header and i == 0: r.bold = True
            if widths: c.width = Cm(widths[j])
    para()


# Title page
para("BITS Pilani, Work Integrated Learning Programmes", align="c", bold=True, size=14)
para("Cloud Computing", align="c", bold=True, size=26)
para("Case Study Assignment Report", align="c", bold=True, size=20)
para("Containerizing the CampusCart API: Build, Test, Scan, Run and Rollback", align="c", size=12)
para()
table([["Name", "Devdarsh V Panth"], ["BITS ID", "2026SI96022"], ["Course", "Cloud Computing"],
       ["Platform", "BITS Prayogshala Console Lab (AWS, ap-south-1 Mumbai) / Docker"],
       ["Date", "25/11/2026"]], [4, 12], header=False)

d.add_paragraph("Table of Contents", style="Heading 1")
bullets(["1. Problem and Assumptions", "2. Architecture and Design Reasoning",
         "3. Concepts Used and How They Were Applied",
         "4. Implementation (Dockerfile, Application, Compose, Proxy, Scripts)",
         "5. Execution (Docker Desktop and AWS Console Lab) - Build, Scan, Run, Failover, Rollback",
         "6. Cloud-Native Extension: ECR, Load Balancer, Auto Scaling, Cloud Scanning",
         "7. Verification and Evidence", "8. Trade-offs and Limitations", "Conclusion",
         "Appendix A: Project Files", "Appendix B: Demo Instructions and Cleanup"])

# 1
h1("1. Problem and Assumptions")
h2("Objective")
para("The CampusCart API behaves differently on developer laptops and the test server because runtime versions and "
     "installed packages differ. The goal is a reproducible deployment without packaging a full guest operating system "
     "for each API instance: containerize the stateless API, keep secrets and persistent data out of the image, and "
     "demonstrate build, test, scan, run and rollback of an image version.")
h2("Assumptions")
table([["Item", "Assumption"],
       ["Workload", "Stateless REST API (/health, /products, /orders); about 50 requests/s at a campus sale peak; small JSON payloads."],
       ["Users", "Students on web/mobile reaching the API through a reverse proxy or load balancer."],
       ["State", "Orders live in a managed relational database (RDS PostgreSQL in the cloud design; a PostgreSQL container is the local stand-in)."],
       ["Secrets", "The DB password is never in the image, Git or Dockerfile; it is supplied at deployment time (Docker secret / AWS Secrets Manager)."],
       ["Targets", "Build under 3 minutes; image under 200 MB; zero fixable HIGH/CRITICAL CVEs at release; no failed request after one instance stops; rollback under 2 minutes."],
       ["Constraints", "Lab session of 60 minutes, about $5 credit, instance types limited to t3a.nano/micro/small/medium, student-level IAM permissions."]],
      [3.2, 13])

# 2
h1("2. Architecture and Design Reasoning")
h2("Local / test-server architecture")
image(os.path.join(IMG, "arch_local.png"), 1, "Two stateless API containers behind an nginx proxy with an external database")
para("Responsibilities: nginx distributes requests round-robin and retries on a failed upstream; each API container is "
     "disposable and holds no data; PostgreSQL stores orders in a named volume, outside the container filesystem.")
h2("Cloud target architecture")
image(os.path.join(IMG, "arch_cloud.png"), 1, "Cloud design: ALB, Auto Scaling Group of Docker hosts, ECR, Secrets Manager, RDS")
table([["Component", "Responsibility", "Security / trade-off"],
       ["API image", "Flask + gunicorn, stateless, /health", "Multistage build, pinned base, non-root user, only port 8000 exposed, read-only filesystem"],
       ["Proxy / ALB", "Load balancing and health-based routing", "Local nginx is a single point of failure; the ALB spans Availability Zones"],
       ["Database", "Persistent orders", "Outside the container so replicas stay disposable; RDS Multi-AZ in production"],
       ["Secrets", "DB password", "Mounted file at /run/secrets, never an image layer; .dockerignore excludes secrets/"],
       ["Image tags", "1.0.0 known-good, 1.1.0 deliberately faulty", "Immutable tags make rollback a redeploy of the previous tag"]],
      [3, 6, 7.2])
para("Containers vs virtual machines: containers share the host kernel, so they start in seconds and are tens of MB "
     "instead of GB per instance, at the cost of weaker isolation. This is mitigated with a non-root user, a read-only "
     "filesystem and image scanning.")

# 3
h1("3. Concepts Used and How They Were Applied")
table([["Concept", "Explanation", "How it is used in this project"],
       ["Dockerfile", "Text recipe that builds an image layer by layer.",
        "Pinned python:3.12.5-slim-bookworm; requirements.txt copied first for layer caching; multistage build keeps build tooling out of the final image; non-root user; EXPOSE 8000; HEALTHCHECK."],
       ["Image", "Immutable package of the app plus exact dependencies; containers are running instances of it.",
        "campuscart-api image built once and run identically on laptop, test server and EC2, removing runtime drift."],
       ["Image tagging", "Human-readable, versioned label for an image.",
        "campuscart-api:1.0.0 (good) and :1.1.0 (faulty). Tags are never overwritten; ECR tag immutability enforces this in the cloud."],
       ["Health check endpoint", "HTTP endpoint reporting whether the service can serve traffic.",
        "GET /health returns 200 (ok), 503 (database down) or 500 (faulty release). Used by the Docker HEALTHCHECK, nginx retries and the ALB target group."],
       ["Load balancing", "Spreading requests across healthy instances.",
        "nginx round-robin across api1 and api2 with proxy_next_upstream; in the cloud an Application Load Balancer."],
       ["Auto Scaling Group", "Keeps a desired number of identical instances, replaces unhealthy ones, scales by metric.",
        "Cloud design: launch template pulls the image from ECR; ASG min 1 / desired 2 / max 3 with CPU 50% target tracking and ALB health checks."],
       ["Vulnerability scanning", "Checking image packages against known CVE databases.",
        "Trivy locally (fail on fixable HIGH/CRITICAL); Amazon ECR scan-on-push in the cloud. Findings are fixed by bumping the base image or package and re-scanning."],
       ["Rollback", "Returning to the previous known-good version.",
        "Release 1.1.0 is detected unhealthy, then 1.0.0 is redeployed with TAG=1.0.0; in the ASG, by pointing the launch template back to the old version."]],
      [3, 5, 8.2])

# 4
h1("4. Implementation")
h2("Procedure")
h3("Step 1: Create the project structure")
para("Created the folder CC-Assignment with app/, tests/, nginx/, scripts/, evidence/ and secrets/ (git- and docker-ignored).")
h3("Step 2: Write the stateless API")
para("The API reads the database address and user from environment variables and the password from /run/secrets/db_password (falling back to an environment variable at runtime). Orders are stored in the database only.")
code(rd("app/app.py"))
h3("Step 3: Pin dependencies")
code(rd("app/requirements.txt"))
h3("Step 4: Write the Dockerfile")
para("Dependency manifest is copied first so the dependency layer is cached; the final stage has no build tools and runs as user app.")
code(rd("Dockerfile"))
h3("Step 5: Add .dockerignore")
code(rd(".dockerignore"))
h3("Step 6: Define the runtime stack (two replicas + proxy + database)")
code(rd("docker-compose.yml"), cap="docker-compose.yml")
code(rd("nginx/nginx.conf"), cap="nginx/nginx.conf")
h3("Step 7: Unit tests")
code(rd("tests/test_api.py"))
h3("Step 8: Demo automation script")
para("One command per step; each writes its output to evidence/.")
code(rd("scripts/demo.sh"), 7)
h3("Step 9: EC2 bootstrap (user data)")
code(rd("scripts/ec2-user-data.sh"))

# 5
h1("5. Execution (Docker Desktop and AWS Console Lab)")
h2("Objective")
para("Run the full build, test, scan, run, failover and rollback workflow on an EC2 Docker host launched from the Prayogshala AWS Console Lab.")
h2("Procedure")
h3("Step 1: Open the AWS console via Prayogshala")
para("Prayogshala portal > Continue with BITS SSO > Console Lab > Launch Lab > Launch AWS Console > Open Console. Confirmed region ap-south-1 (Mumbai).")
placeholder(5, "AWS console home page in ap-south-1", "AWS Console home with region ap-south-1")
h3("Step 2: Launch the Docker host")
para("EC2 > Launch instance: name campuscart-docker, Amazon Linux 2023, t3a.small, 20 GiB gp3, security group allowing SSH 22 and TCP 8080 from My IP, and scripts/ec2-user-data.sh as user data.")
placeholder(5, "Instance running with status checks passed", "EC2 instance list: Running, 2/2 checks passed")
placeholder(5, "Security group inbound rules (22 and 8080)", "Security group inbound rules")
h3("Step 3: Connect and verify Docker")
para("Connected with EC2 Instance Connect and ran docker --version and docker compose version.")
placeholder(5, "Docker and Compose versions on the instance", "Terminal: docker --version / docker compose version")
h3("Step 4: Fetch the project")
code("git clone https://github.com/<user>/campuscart-assignment.git\ncd campuscart-assignment\nchmod +x scripts/demo.sh")
h3("Step 5: Test, build and scan")
code("./scripts/demo.sh test\n./scripts/demo.sh build\n./scripts/demo.sh scan")
para("Screenshots from Step 5 onward were captured on Docker Desktop (Git Bash) with the same scripts that run on the EC2 host.")
shot("test", 5, "Unit tests passing in a container (5 passed)", 12)
shot("build", 5, "Image build for 1.0.0 and 1.1.0 (multistage, pinned base image)", 11)
shot("scan-run", 5, "Trivy scan start: vulnerability database download and scanners enabled")
shot("scan-summary", 5, "Trivy scan result for campuscart-api:1.0.0: 0 vulnerabilities")
h3("Step 6: Create the secret and run two instances behind the proxy")
code("./scripts/demo.sh secret\n./scripts/demo.sh up\n./scripts/demo.sh health")
shot("containers", 5, "Docker Desktop: api1, api2, proxy and db running (proxy on 8080)")
shot("health", 5, "Health check through the proxy alternating between instances; order created; non-root user; no secret in image", 11)
shot("browser1-crop", 5, "Browser /health served by instance 444760aa8076", 12)
shot("browser2-crop", 5, "Browser /health after refresh served by instance 87dd6465b845", 12)
h3("Step 7: Failover test")
code("./scripts/demo.sh failover\n./scripts/demo.sh recover")
shot("failover", 5, "api1 stopped, six requests still served with HTTP 200, then recovered", 12)
h3("Step 8: Faulty release and rollback")
code("./scripts/demo.sh release-bad   # deploys campuscart-api:1.1.0 - unhealthy\n./scripts/demo.sh rollback      # redeploys campuscart-api:1.0.0")
shot("release-bad", 5, "Release 1.1.0 unhealthy; proxy returns 500 502 502", 12)
shot("rollback", 5, "Rollback to 1.0.0: containers healthy, /health reports version 1.0.0", 13)
h3("Step 9: Image summary")
code("./scripts/demo.sh summary")
shot("summary", 5, "Image size, tags, non-root user, exposed port and layer history", 15)
h3("Step 10: Clean up")
para("Ran ./scripts/demo.sh down, terminated the EC2 instance (not just stopped), used List Resources to confirm nothing remained, then Stop Session.")
placeholder(5, "Instance in Terminated state", "EC2 instance state Terminated")

# 6
h1("6. Cloud-Native Extension")
para("These steps map the local proof to AWS services. Where the student lab role denies an action, the AccessDenied message is captured and the configuration screen is shown instead.")
h3("Step 1: Amazon ECR with immutable tags and scan on push")
para("ECR > Create repository (private) campuscart-api, Tag immutability: Enabled, Scan on push: Enabled. Use View push commands to log in, tag and push 1.0.0 and 1.1.0. The scan findings tab is the cloud vulnerability-scanning evidence.")
placeholder(6, "ECR repository with immutable tags", "ECR repository settings / images list")
placeholder(6, "ECR scan findings", "ECR image scan results")
h3("Step 2: AWS Secrets Manager")
para("Store a secret campuscart/db_password (value hidden). The application reads it at deployment instead of baking it into the image.")
h3("Step 3: Launch template")
para("EC2 > Launch templates: Amazon Linux 2023, t3a.small, user data installs Docker, logs in to ECR and runs docker run -p 80:8000 <ecr-uri>/campuscart-api:1.0.0. Version 1 uses tag 1.0.0.")
h3("Step 4: Application Load Balancer and target group")
para("Target group (HTTP 8000/80) with health check path /health, healthy threshold 2, interval 15 s. Internet-facing ALB listener on port 80 forwarding to the target group.")
placeholder(6, "Target group health check configuration (/health)", "Target group > Health checks")
h3("Step 5: Auto Scaling Group")
para("Create the ASG from the launch template across two AZs, attach the target group, enable ELB health checks, min 1 / desired 2 / max 3, target-tracking policy on average CPU 50%.")
placeholder(6, "Auto Scaling Group configuration", "ASG details: capacity 1/2/3, target group attached")
placeholder(6, "Two healthy targets registered with the ALB", "Target group > Targets: healthy")
h3("Step 6: Failover and rollback in the cloud")
para("Terminate one instance: the ALB stops routing to it and the ASG launches a replacement. For rollback, create launch template version 2 (faulty 1.1.0), observe unhealthy targets, then set the ASG to launch template version 1 (tag 1.0.0) and start an instance refresh.")
placeholder(6, "ASG replacing a terminated instance", "ASG activity history")
placeholder(6, "Instance refresh to previous launch template version", "Instance refresh progress")
para("Note: ECR, ALB and ASG may be restricted for the student role and the 60-minute session is short. Any blocked step is documented as a limitation.", italic=True)

# 7
h1("7. Verification and Evidence")
h2("Verification plan")
table([["#", "Check", "Expected", "Status"],
       ["1", "Unit tests", "5 passed", "Executed - passed"],
       ["2", "Two instances + proxy, stop one", "All requests HTTP 200", "Executed - passed (Docker, nginx, api1 stopped)"],
       ["3", "Docker build 1.0.0 / 1.1.0", "Images created", "Executed - passed (257 MB on disk, 61.7 MB compressed content; disk figure above the 200 MB target)"],
       ["4", "Trivy scan", "0 fixable HIGH/CRITICAL", "Executed - before: 9 CRITICAL + 56 HIGH on python:3.12.5; after bump to 3.12.16: 0"],
       ["5", "Secret not in image", "docker history shows no password", "Executed - passed"],
       ["6", "Container failover", "Requests served by api2", "Executed - passed"],
       ["7", "Bad release 1.1.0 detected", "unhealthy / HTTP 500", "Executed - passed"],
       ["8", "Rollback to 1.0.0", "healthy, version 1.0.0", "Executed - passed"]],
      [0.8, 5.2, 5, 5.2])
h2("Evidence 1: Unit test results (executed)")
shot("test", 7, "Unit tests: 5 passed", 12)
h2("Evidence 2: Vulnerability scan - corrective action")
para("First scan of campuscart-api:1.0.0 built on python:3.12.5-slim-bookworm (Debian 12.7) found 9 CRITICAL and 56 HIGH fixable vulnerabilities, so release was blocked. The base image was moved to python:3.12.16-slim-bookworm (Debian 12.15), the image was rebuilt with the same tag and re-scanned: 0 HIGH/CRITICAL in the OS layer and in all Python packages.")
shot("scan-summary", 7, "Trivy re-scan after the base image bump: 0 vulnerabilities")
h2("Evidence 3: Build 1.0.0 and 1.1.0")
shot("build", 7, "Image build output", 11)
h2("Evidence 4: Running containers")
shot("containers", 7, "api1, api2, proxy and db running")
h2("Evidence 5: Health check via proxy, order persisted, non-root, no secret in image")
shot("health", 7, "Health check alternating between instances", 11)
h2("Evidence 6: Failover - api1 stopped")
shot("failover", 7, "Six requests returned HTTP 200 while api1 was stopped", 12)
h2("Evidence 7: Faulty release 1.1.0 detected")
shot("release-bad", 7, "Release 1.1.0 unhealthy: 500 502 502", 12)
h2("Evidence 8: Rollback to 1.0.0")
shot("rollback", 7, "Rollback to 1.0.0: healthy, version 1.0.0", 13)
h2("Evidence 9: Image summary")
shot("summary", 7, "Image size, tags, non-root user, exposed port and history", 15)
h2("Corrective action")
para("If the scan reports HIGH/CRITICAL findings, the base image tag is moved to the latest patch release or the vulnerable package is bumped in requirements.txt, the image is rebuilt as a new immutable tag and re-scanned before release. A failed release (1.1.0) is corrected by redeploying the previous tested tag 1.0.0.")

# 8
h1("8. Trade-offs and Limitations")
bullets(["Containers share the host kernel: lighter and faster than VMs, but with weaker isolation. Mitigated by non-root user, read-only filesystem and scanning.",
         "The local nginx proxy is a single point of failure; production uses an ALB across Availability Zones with an Auto Scaling Group or orchestrator (ECS/EKS).",
         "The local database container is not highly available; RDS Multi-AZ is the production choice. In the 60-minute lab the container substitutes for RDS.",
         "Scan results depend on the vulnerability database date; images must be re-scanned regularly. Pinning the base image gives reproducibility but requires deliberate patch bumps.",
         "Release 1.1.0 is a simulated faulty release (FAIL_HEALTH flag). Rollback is manual here; an ASG instance refresh or orchestrator can automate it on failed health checks.",
         "Container steps were executed locally on Docker Desktop (Windows, Docker 29.9.3); the same scripts run unchanged on an EC2 Docker host. Image disk size is 257 MB (61.7 MB content), above the 200 MB target; a distroless or alpine base would reduce it.",
         "ECR, Secrets Manager, ALB and ASG may be denied by the student role; any such step is shown as a configuration screen with the AccessDenied message."])

h1("Conclusion")
para("The CampusCart API was containerized as a stateless, non-root, multistage image with pinned dependencies, environment-based configuration, a health endpoint and secrets kept outside the image. The workflow of unit tests, immutable version tags, vulnerability scanning, two replicas behind a proxy, failover and rollback to the previous tag is scripted end to end and mapped to AWS services (ECR, ALB, Auto Scaling, Secrets Manager, RDS). Resources are terminated after the lab to conserve credits.")

h1("Appendix A: Project Files")
table([["File", "Purpose"],
       ["Dockerfile", "Multistage, non-root, pinned base, HEALTHCHECK"],
       [".dockerignore / .gitignore", "Keep secrets, tests and evidence out of the image and Git"],
       ["app/app.py, app/requirements.txt", "Stateless API and exact dependency versions"],
       ["tests/test_api.py", "5 pytest unit tests"],
       ["docker-compose.yml, nginx/nginx.conf", "Two replicas, proxy, database and secret wiring"],
       ["scripts/demo.sh", "build, test, scan, up, health, failover, release-bad, rollback, summary, down"],
       ["scripts/ec2-user-data.sh", "Installs Docker and Compose on EC2"],
       ["scripts/local_simulation.py", "Docker-free failover proof"],
       ["evidence/", "Saved outputs of each step"],
       ["STEP_BY_STEP_GUIDE.md / .pdf", "Detailed instructions"],
       ["Panth_Devdarsh_Assignment.docx", "This report"]], [6, 10.2])

h1("Appendix B: Demo Instructions and Cleanup")
bullets(["Start the Prayogshala Console Lab, launch the EC2 host, clone the project (Section 5).",
         "Run demo.sh in order: test, build, scan, secret, up, health, failover, recover, release-bad, rollback, summary.",
         "Open http://<public-ip>:8080/health in a browser and refresh to show instance alternation.",
         "Clean up: demo.sh down, terminate the EC2 instance, delete ECR repository/secret/ALB/ASG if created, List Resources, Stop Session."])

used = set(d.element.body.xml.split('r:embed="')[i].split('"')[0] for i in range(1, d.element.body.xml.count('r:embed="') + 1))
for rid, rel in list(d.part.rels.items()):
    if rel.reltype.endswith("/image") and rid not in used:
        del d.part.rels[rid]
d.save(OUT)


