# AWS Deployment Runbook

Deploy the Employee Management API to AWS so it has a **real, shareable public URL** (no more `127.0.0.1`). Follow the steps in order; every command is copy-paste ready. Commands are labelled **PowerShell** (run on your Windows laptop) or **EC2 (Ubuntu)** (run after you SSH into the server).

## What you'll build

```
Client ──HTTP:80──> EC2 (nginx → Gunicorn/Uvicorn → FastAPI)
                      ├──:5432──> RDS PostgreSQL  (private)
                      └──PutObject/presign──> S3  (employee exports)
                    IAM role gives EC2 its S3 permissions (no keys in code)
                    CloudWatch collects metrics/logs
```

See `docs/architecture-aws.png` for the full diagram.

| AWS service | Role in this project | Rough cost if left on 24/7 (ap-south-1) |
|---|---|---|
| EC2 `t3.micro` | Hosts the API (nginx + Gunicorn) | ~$7.50/month |
| RDS PostgreSQL `db.t3.micro` (Single-AZ) | Managed database | ~$13–15/month + storage |
| Public IPv4 (1, on the instance) | Makes the API reachable | ~$3.65/month |
| S3 | Stores CSV exports | a few cents |
| IAM | Role granting EC2 → S3 access | free |
| CloudWatch | Monitoring + 1 alarm | a few cents |

**Total: roughly $25/month if everything runs around the clock.**

> ⚠️ **Read this before you spend anything — the free tier changed.**
>
> AWS replaced the old free tier on **July 15, 2025**. Because you're creating a **new** account, you are **not** on the "750 free hours of EC2/RDS" model that older tutorials describe. New accounts get a **credit-based plan**: **$100 in credits at sign-up**, up to **$100 more** for completing onboarding tasks. Every service draws down that balance.
>
> The good news: the table above totals ~$25/month, which stays **well under a $100 credit** — there's no realistic way it exhausts it. And if you pick the **Free Plan** at sign-up, AWS **closes the account instead of charging you** when credits run out or 6 months pass. That makes accidental billing essentially impossible. (Just don't treat the running demo as permanent.)
>
> **The charges that actually surprise people — avoid all four:**
> 1. **NAT Gateway** — ~$32/month. This runbook never creates one. If a tutorial tells you to, don't.
> 2. **Idle Elastic IP** — an *unattached* Elastic IP bills ~$3.65/month with **no free allowance**, forever, even after you delete everything else. **This runbook does not use an Elastic IP** (see Step 5) precisely to avoid this trap.
> 3. **RDS Multi-AZ** — doubles the database cost. The Free-tier template keeps you Single-AZ; don't switch it on.
> 4. **Leaving it all running after the demo** — see [Cost control & teardown](#cost-control--teardown). Stop/terminate once you're done.
>
> **Do Step 1's budget alarm first**, and watch your **credit balance** in the *Cost and Usage* widget on the console home page.

---

## Prerequisites

- A credit/debit card (AWS requires one even for Free Tier).
- Your repo pushed to GitHub: `https://github.com/Maaadhavq/employee-management-api`
- The deployment code merged to your main branch — see the main README's deployment section.
- About 2–3 focused hours for the first run.

---

## Step 1 — Create your AWS account + a budget alarm

1. Sign up at <https://aws.amazon.com/> → **Create an AWS Account**.
2. **At sign-up you'll be asked to choose a Free Plan or a Paid Plan. Choose the Free Plan.** On the Free Plan, AWS shuts the account down rather than billing you if you ever run past your credits — it's the strongest possible guard against accidental charges, and this usage won't come close to the limit. (Already signed up? Check which plan you're on via the **Cost and Usage** widget on the console home page, or **Billing and Cost Management → Account**.)
3. Once in the console, set the region (top-right) to **Asia Pacific (Mumbai) ap-south-1** — closest to Chennai, lowest latency.
4. Create a budget so you're warned early:
   - Search **Billing and Cost Management** → **Budgets** → **Create budget**.
   - Template: **Zero spend budget** (or a $1 monthly cost budget).
   - Enter your email for alerts → **Create budget**.
   - Bonus: creating a budget is one of the onboarding tasks that earns you **+$20 in credits**. Launching EC2 (Step 5) and configuring RDS (Step 6) are two more — so this week's work itself tops up your balance.
5. Keep an eye on the **Cost and Usage** widget on the console home — it shows your remaining credit balance and how many days are left on the plan.

---

## Step 2 — Create an IAM admin user (stop using root)

Using the root account for daily work is unsafe. Create an admin user for yourself.

1. Console → **IAM** → **Users** → **Create user**.
2. Name: `madhav-admin`. Tick **Provide user access to the AWS Management Console**.
3. Permissions → **Attach policies directly** → tick **AdministratorAccess**.
4. Create the user, **save the sign-in URL and password**, then sign out of root and sign back in as `madhav-admin`.

---

## Step 3 — Create the S3 bucket (employee exports)

1. Console → **S3** → **Create bucket**.
2. **Bucket name**: must be globally unique, e.g. `madhav-employee-exports-2026` (lowercase, no spaces). **Write this name down** — you'll reuse it.
3. **Region**: Asia Pacific (Mumbai) ap-south-1.
4. **Block Public Access**: leave **ON** (all blocked). We never make objects public; downloads use time-limited presigned URLs.
5. Leave the rest as defaults → **Create bucket**.

---

## Step 4 — Create the IAM role for EC2 → S3

This lets the EC2 instance write/read S3 **without any access keys in your code**.

### 4a. Create the policy

1. Console → **IAM** → **Policies** → **Create policy** → **JSON** tab.
2. Paste the contents of `deploy/iam-s3-policy.json` and **replace `REPLACE-WITH-YOUR-BUCKET-NAME`** with your real bucket name:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "EmployeeExportObjectAccess",
         "Effect": "Allow",
         "Action": ["s3:PutObject", "s3:GetObject"],
         "Resource": "arn:aws:s3:::madhav-employee-exports-2026/exports/*"
       }
     ]
   }
   ```
3. Next → name it `employee-api-s3-policy` → **Create policy**.

### 4b. Create the role

1. **IAM** → **Roles** → **Create role**.
2. **Trusted entity type**: AWS service. **Use case**: **EC2** → Next.
3. Search and attach **`employee-api-s3-policy`** → Next.
4. Role name: `employee-api-ec2-role` → **Create role**.

---

## Step 5 — Launch the EC2 instance

1. Console → **EC2** → **Launch instance**.
2. **Name**: `employee-api-server`.
3. **AMI**: **Ubuntu Server 24.04 LTS** (Free Tier eligible).
4. **Instance type**: **t3.micro** (or t2.micro) — Free Tier eligible.
5. **Key pair** → **Create new key pair**:
   - Name: `ema-key`, type **RSA**, format **.pem** → **Create**. The `ema-key.pem` file downloads. **Keep it safe — you can't re-download it.**
6. **Network settings** → **Edit** → create a security group named `employee-api-ec2-sg` with these inbound rules:
   - **SSH** · TCP 22 · Source **My IP**
   - **HTTP** · TCP 80 · Source **Anywhere (0.0.0.0/0)**
7. **Advanced details** → **IAM instance profile** → select **`employee-api-ec2-role`**.
8. **Launch instance**. Open the instance and note its **Public IPv4 address** (e.g. `13.234.x.x`).

> 💡 **Skip the Elastic IP.** The instance already has an auto-assigned public IPv4 — use that. Allocating an Elastic IP adds another billable IP, and if you forget to **release** it at teardown it keeps charging ~$3.65/month forever (idle Elastic IPs have no free allowance — this is the single most common surprise bill). The only downside of skipping it: if you **stop and start** the instance the public IP changes, so just grab the new IP from the console and re-share the URL. For a short-lived demo you likely won't restart it anyway.

---

## Step 6 — Create the RDS PostgreSQL database

1. Console → **RDS** → on the dashboard, find the two creation tiles. Under **"Create with full configuration"**, click **Create**. ⚠️ **Do not** use **"Create with express configuration"** — that spins up an **Aurora Serverless** database, which is a different, pricier engine that isn't Free-tier eligible. You want the full-configuration path.
2. If prompted, choose **Standard create**. Engine: **PostgreSQL** — the standalone option, **not** "Aurora (PostgreSQL Compatible)." Picking plain PostgreSQL is what unlocks the Free tier template. (Latest non-beta 16.x or newer is fine.)
3. **Templates**: **Free tier**. (This forces Single-AZ and the free-eligible instance — exactly what you want.)
4. **DB instance identifier**: `employee-db`.
5. **Master username**: `empadmin`. **Master password**: set a strong one and **write it down**.
6. **Instance configuration**: `db.t3.micro` (Free Tier default).
7. **Storage**: 20 GB gp3 (Free Tier). Turn **off** storage autoscaling to avoid surprise growth.
8. **Connectivity**:
   - **Don't connect to an EC2 compute resource** (we'll wire the security group manually).
   - **Public access**: **No** (EC2 reaches it privately inside the VPC).
   - **VPC security group**: **Create new** → name `employee-api-rds-sg`.
9. **Additional configuration** → **Initial database name**: `employee_db`. ← important; the app expects this DB to exist.
10. **Create database**. Wait ~5–10 min until status is **Available**, then copy the **Endpoint** (e.g. `employee-db.xxxx.ap-south-1.rds.amazonaws.com`).

> 💡 Creating this database is one of the AWS onboarding tasks, so it earns you **+$20 in credits** automatically — no need to click "Start tutorial," just creating the DB counts. While it provisions (5–10 min), jump ahead to **Step 7** so you're not waiting idle.

### 6a. Allow EC2 → RDS on port 5432

1. EC2 console → **Security Groups** → open **`employee-api-rds-sg`** → **Inbound rules** → **Edit**.
2. **Add rule**: **PostgreSQL** · TCP 5432 · Source → start typing and select the **`employee-api-ec2-sg`** security group (not an IP). → **Save**.

This means only your API server can reach the database.

---

## Step 7 — Connect to EC2 over SSH (from PowerShell)

Your `.pem` likely downloaded into a OneDrive-redirected `Downloads`. Move it somewhere stable and lock its permissions (OpenSSH refuses keys that are too open).

**PowerShell:**
```powershell
# Create an .ssh folder and move the key there (adjust the source path if needed)
New-Item -ItemType Directory -Force -Path "$HOME\.ssh"
Move-Item -Path "$HOME\Downloads\ema-key.pem" -Destination "$HOME\.ssh\ema-key.pem" -Force

# Lock down the key so only you can read it
icacls "$HOME\.ssh\ema-key.pem" /inheritance:r
icacls "$HOME\.ssh\ema-key.pem" /grant:r "$($env:USERNAME):(R)"
```

> If OneDrive moved your Downloads, `$HOME\Downloads` may not resolve. Find the file with
> `Get-ChildItem -Path $HOME -Recurse -Filter ema-key.pem -ErrorAction SilentlyContinue | Select FullName`
> and use that path in the `Move-Item` above.

**Connect** (replace with your instance's public IP):
```powershell
ssh -i "$HOME\.ssh\ema-key.pem" ubuntu@13.234.0.0
```
Type `yes` at the fingerprint prompt. You're now on the server — the prompt becomes `ubuntu@ip-...`.

---

## Step 8 — Deploy the application

All commands here run **on the EC2 box**.

```bash
# 1. Clone your repo
git clone https://github.com/Maaadhavq/employee-management-api.git
cd employee-management-api

# 2. If you haven't merged the deployment branch into main yet, deploy from it:
git checkout feature/aws-deployment    # skip this line once it's merged to main

# 3. Run the bootstrap: installs python venv + nginx, builds the venv,
#    installs requirements, registers the systemd service, configures nginx
bash deploy/bootstrap.sh
```

Now create the production environment file. Use `deploy/.env.production.example` as your template:

```bash
sudo nano /etc/employee-api.env
```

Paste this and fill in your **RDS endpoint**, **RDS password**, and **bucket name**:

```ini
DATABASE_URL=postgresql://empadmin:YOUR_RDS_PASSWORD@employee-db.xxxx.ap-south-1.rds.amazonaws.com:5432/employee_db
SQL_ECHO=False
ENVIRONMENT=production
AWS_REGION=ap-south-1
S3_BUCKET_NAME=madhav-employee-exports-2026
S3_PRESIGNED_URL_TTL=3600
```

Save (`Ctrl+O`, `Enter`) and exit (`Ctrl+X`). Then start everything:

```bash
sudo systemctl start employee-api
sudo systemctl restart nginx

# Confirm the API service is running
sudo systemctl status employee-api --no-pager
```

On startup the app connects to RDS and **automatically creates the `employees` and `departments` tables and seeds the six departments** — no manual SQL needed.

Watch logs live if anything looks off:
```bash
journalctl -u employee-api -f      # Ctrl+C to stop following
```

---

## Step 9 — Verify the deployment

**On EC2:**
```bash
curl http://localhost/health
# -> {"status":"ok"}
```

**From your laptop browser**, open the interactive docs (use your instance's public IP):
```
http://13.234.0.0/docs
```

End-to-end test, including S3:
1. In Swagger, **POST `/employees`** a couple of times to create employees.
2. **GET `/employees`** — confirm they're returned from RDS.
3. **GET `/employees/export`** — you should get back JSON with a `download_url`.
4. Open that `download_url` in a new tab → the CSV downloads **straight from S3** via the presigned URL.
5. In the S3 console, open your bucket → `exports/` → confirm the `.csv` object is there.

If all five work, your EC2 + RDS + S3 + IAM chain is correct. 🎉

---

## Step 10 — CloudWatch monitoring

1. EC2 → select your instance → **Monitoring** tab. You'll see CPU, network, and disk metrics flowing in automatically.
2. Create a simple alarm: **CloudWatch** → **Alarms** → **Create alarm** → **Select metric** → **EC2 → Per-Instance Metrics → CPUUtilization** for `employee-api-server`.
   - Condition: **Greater than 80** for **5 minutes**.
   - (Optional) Create an SNS topic with your email to get notified → **Create alarm**.

> Optional/advanced: to ship the API's application logs to CloudWatch Logs, install the CloudWatch agent and point it at the journald unit. Not required here — the metrics + alarm above cover the basics.

---

## Step 11 — What you end up with

You end up with:
- **Public API URL**: `http://<your-ip>/docs` (the Swagger UI). Test it in an incognito window to confirm it's reachable from outside.
- **Architecture diagram**: `docs/architecture-aws.png` (already in the repo).
- **Screenshots** (nice to include): EC2 instance running, RDS available, the S3 `exports/` object, the CloudWatch alarm, and the Swagger UI loaded from the public IP.

---

## Cost control & teardown

**While demoing:** keep the EC2 instance and RDS database **running** so others can hit the URL. (Since you skipped the Elastic IP, a stop/start would change the public IP — so just leave it up during the demo window rather than stopping it.)

On the **Free Plan**, none of this *bills* you — it draws from your credits, and the account closes rather than charging if you somehow hit zero. But tearing down still conserves credits and is good habit, so once you're done:

**Teardown checklist (do all of these):**
- **Terminate** the EC2 instance: EC2 → Instance state → **Terminate**. This also deletes its root EBS volume (delete-on-termination is on by default) and releases its public IPv4 — so compute, storage, and IP charges all stop.
- **Delete** the RDS database: RDS → select `employee-db` → **Actions → Delete**. Untick "create final snapshot" for a throwaway project (snapshots cost storage). This stops the database and its 20 GB.
- **Empty, then delete** the S3 bucket if you no longer need the exports (S3 → bucket → Empty → Delete).
- **Check for stray Elastic IPs**: EC2 → **Elastic IPs**. If anything is listed, **Release** it — an unattached Elastic IP is the one thing that keeps billing after everything else is gone. (You shouldn't have one if you followed Step 5, but verify.)
- **Keep your budget alarm on** regardless — it costs nothing and is your safety net.

> Just pausing, not finished? **Stop** (not terminate) the instance: EC2 → Instance state → **Stop**. A stopped instance isn't billed for compute and drops its public IP, but its EBS root volume still incurs a small storage charge. To halt charges completely, terminate.

---

## Troubleshooting

| Symptom | Likely cause & fix |
|---|---|
| `ssh` times out | EC2 SG inbound SSH source isn't **My IP** (your IP changed), or you're using the wrong public IP. Update the SG rule. |
| `Permissions ... are too open` on the key | Re-run the `icacls` commands in Step 7. |
| Browser shows the **nginx default page** | The default site wasn't removed. Run `sudo rm -f /etc/nginx/sites-enabled/default && sudo systemctl restart nginx`. |
| **502 Bad Gateway** from nginx | The app isn't running. `sudo systemctl status employee-api` and `journalctl -u employee-api -n 50`. Usually a bad `DATABASE_URL`. |
| App won't start, DB connection refused/timeout | RDS SG missing the inbound **5432 from `employee-api-ec2-sg`** (Step 6a), or the endpoint/password in `/etc/employee-api.env` is wrong. EC2 and RDS must be in the **same VPC**. |
| `/employees/export` returns **503** | `S3_BUCKET_NAME` is blank in `/etc/employee-api.env`. Set it and `sudo systemctl restart employee-api`. |
| `/employees/export` returns **502 / AccessDenied** | The IAM role isn't attached to the instance, or the policy's `Resource` ARN doesn't match your bucket/`exports/*` path. Check Step 4 and that the role is on the instance (EC2 → Actions → Security → Modify IAM role). |
| Changed `/etc/employee-api.env` but nothing changed | You must restart: `sudo systemctl restart employee-api`. |

---

## Appendix — optional automated test for the export endpoint

If you want to extend your test suite, this mirrors your existing style and uses `moto` to mock S3 (already in `requirements.txt`). Drop it into your `tests/` folder:

```python
# tests/test_export.py
import os
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-south-1")

import boto3
from moto import mock_aws
from app.services.s3_service import S3Service, S3NotConfiguredError


def test_unconfigured_s3_raises():
    svc = S3Service(bucket_name="", region="ap-south-1")
    assert svc.is_configured is False
    try:
        svc.upload_text(content="x", key="k.csv")
        assert False, "expected S3NotConfiguredError"
    except S3NotConfiguredError:
        pass


@mock_aws
def test_upload_returns_presigned_url():
    client = boto3.client("s3", region_name="ap-south-1")
    client.create_bucket(
        Bucket="test-bucket",
        CreateBucketConfiguration={"LocationConstraint": "ap-south-1"},
    )
    svc = S3Service(bucket_name="test-bucket", region="ap-south-1")
    url = svc.upload_text(content="id,name\n1,Ada\n", key="exports/x.csv",
                          content_type="text/csv")
    assert url.startswith("https://")
    body = client.get_object(Bucket="test-bucket", Key="exports/x.csv")["Body"].read()
    assert b"Ada" in body
```
