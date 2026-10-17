# Week 00: Set up your toolchain and run the service

**Goal:** run the ingestion service end to end on your machine and on one desktop engine, before you change any code.

## Brief

You join the Northfield Bank engagement (fictional) on Monday. Before you write anything for the customer, prove that your toolchain works: Python, tests, a container engine, and a smoke test against the running service.

## Steps

1. Install Python 3.12, Git, `make`, and one desktop engine (Docker Desktop, Podman Desktop or Rancher Desktop). Windows: use WSL2 (Ubuntu).
2. Create your copy of `fde-00-programming-starter` ("Use this template" on GitHub) and clone it.
3. Follow step 0 in [desktop labs](../../docs/learning/DESKTOP-LABS.md):

   ```bash
   python3.12 -m venv .venv && source .venv/bin/activate
   make install
   make test          # green: exercise tests are skipped in the starter
   make exercises     # red: this is your to-do list for weeks 1-4
   make e2e           # the API starts on an empty database and passes its smoke checks
   ```

4. Start the containers on your desktop: `make up-docker`, `make up-podman` or `make up-rancher`. Open http://127.0.0.1:8000/docs and call `/health/ready`.
5. Read `src/complaints_ingest/` top to bottom: `schema.py` → `clean.py` → `cfpb.py` → `store.py` → `pipeline.py` → `cli.py`. Write down, in two sentences each, what every module does.

## Check

```bash
make test && make e2e
```

## Evidence

Smoke-test output from your desktop run, plus the desktop name and version, and `make exercises` output showing the failing exercises.

## Stretch

Run the same stack on a second desktop engine, then on local Kubernetes (`make k8s-*`). Note one thing that differed.
