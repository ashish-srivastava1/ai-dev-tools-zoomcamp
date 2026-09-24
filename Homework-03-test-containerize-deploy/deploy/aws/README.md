# Deploying TableTurn to AWS (CloudFormation)

Provisions **one EC2 instance** that runs **Caddy + the app + Postgres** via
docker compose, all described as infrastructure-as-code in
[`tableturn-stack.yaml`](tableturn-stack.yaml). The instance clones this public
repo on boot, builds the app image (the same multi-stage
[`Dockerfile`](../../Dockerfile)), and starts the production stack
([`compose.prod.yml`](compose.prod.yml)) behind Caddy
([`Caddyfile`](Caddyfile)).

```
Internet ──▶ Caddy :80/:443 ──▶ app :8000 ──▶ Postgres :5432
                (HTTPS optional)   (API + built SPA)   (pgdata volume)
        one EC2 instance, one Elastic IP, its own VPC/subnet/security group
```

## What the template creates

A self-contained VPC + public subnet + internet gateway + route table, a
security group (80/443 open; 22 only if you pass an SSH key), an IAM role for
**SSM Session Manager** (shell access with no SSH key/port), the EC2 instance
(Amazon Linux 2023, 20 GiB gp3), and an **Elastic IP** so the address is stable.

## Prerequisites

- An AWS account and the **AWS CLI** installed and configured
  (`aws configure` — access key, secret, default region).
- Permissions to create VPC/EC2/IAM/EIP resources.
- (Optional) the **Session Manager plugin** for `aws ssm start-session`.
- (Optional) a **domain** you can point at the Elastic IP, for HTTPS.

## Deploy

From this directory:

```bash
POSTGRES_PASSWORD='choose-a-strong-one' ./deploy.sh up
```

That runs `aws cloudformation deploy` and prints the stack outputs (the URL,
the Elastic IP, and an SSM connect command). First boot takes a few minutes
while the instance installs Docker and builds the image — watch progress over
SSM:

```bash
aws ssm start-session --target <instance-id>
sudo tail -f /var/log/tableturn-bootstrap.log
```

When it finishes, open the **URL** output (e.g. `http://<elastic-ip>`).

### Options (env vars for `deploy.sh up`)

| Variable            | Default          | Purpose                                                        |
| ------------------- | ---------------- | -------------------------------------------------------------- |
| `POSTGRES_PASSWORD` | *(required)*     | Password for the Postgres `tableturn` user (≥8 chars).         |
| `DOMAIN_NAME`       | *(empty → HTTP)* | Domain pointed at the Elastic IP; enables Caddy HTTPS.         |
| `KEY_NAME`          | *(empty)*        | EC2 key pair for SSH; omit to use SSM only.                    |
| `GIT_REF`           | `main`           | Branch/tag to deploy (must contain the app **and** `deploy/`). |
| `INSTANCE_TYPE`     | `t3.small`       | Bump to `t3.medium` if the on-instance build is slow.          |
| `STACK_NAME`        | `tableturn`      | CloudFormation stack name.                                     |
| `AWS_REGION`        | `us-east-1`      | Region to deploy into.                                         |

### HTTPS with a domain

1. Deploy once (HTTP) to get the Elastic IP from the outputs.
2. Add a DNS **A record** for your domain pointing at that IP.
3. Redeploy with the domain — Caddy fetches a Let's Encrypt cert automatically:
   ```bash
   POSTGRES_PASSWORD='...' DOMAIN_NAME='tableturn.example.com' ./deploy.sh up
   ```

> **Note on GIT_REF:** the instance clones the repo at `GIT_REF`, so the
> `deploy/aws/` files must exist on that ref. Until this work is merged to
> `main`, deploy with `GIT_REF=hw3-aws-deploy` (the branch these files live on).

## Updating a running deployment

Re-running `./deploy.sh up` updates the CloudFormation stack, but application
code changes require the instance to re-pull and rebuild. The simplest path is
to connect over SSM and:

```bash
cd /opt/app && sudo git pull
cd Homework-03-test-containerize-deploy/deploy/aws
sudo docker compose -f compose.prod.yml up -d --build
```

(A proper CD pipeline — the next homework item — automates this.)

## Tear down (stop paying)

```bash
./deploy.sh down
```

Deletes the stack and **all** its resources (instance, Elastic IP, VPC, IAM
role) and waits for completion. The Postgres data lives on the instance's
volume, so teardown removes it — export anything you want to keep first.

## Cost

A `t3.small` + 20 GiB gp3 + Elastic IP runs on the order of a few US dollars a
week if left on. Tear the stack down when you're done. (New accounts may have
free-tier credit, but `t3.small` is not always free-tier eligible.)

## Troubleshooting

- **App not up after a few minutes** — connect over SSM and check
  `/var/log/tableturn-bootstrap.log`, then `sudo docker compose -f
  /opt/app/Homework-03-test-containerize-deploy/deploy/aws/compose.prod.yml ps`.
- **HTTPS not issued** — confirm the domain's A record resolves to the Elastic
  IP and that port 443 is reachable; check `sudo docker compose ... logs caddy`.
- **Stack fails to create** — read the CloudFormation events:
  `aws cloudformation describe-stack-events --stack-name tableturn`.
