# Desktop labs: Docker Desktop, Podman Desktop, Rancher Desktop

Every FDE repo runs on all three desktops, first as containers, then on local Kubernetes. Here that means three moving parts: **Postgres**, the **report API** and the **ingest job**. Do the lab on the desktop you have; doing it on a second one is the best way to understand what is engine-specific and what is not.

> Run only **one** desktop engine at a time. Two engines fight over port 8000, the Docker socket and kubectl contexts.

## Sizing

| Profile | CPU | RAM | Free disk |
| --- | --- | --- | --- |
| Postgres + API (+ ingest job) | 1–2 vCPU | 1.5 GiB | 6 GiB |
| + Prometheus + Grafana | 2 vCPU | 2.5 GiB | 9 GiB |
| Desktop engine VM (Windows/macOS) | 2-4 CPUs | 4 GiB minimum, 6-8 GiB comfortable | 20 GiB |
| Local Kubernetes on top | +1 CPU | +2 GiB | +5 GiB |

These are starting estimates (not measured). A full-history CSV backfill needs several GB of free disk for the download and the database volume.

## 0. Prepare (all desktops)

```bash
git clone https://github.com/<you>/<repo>.git && cd <repo>
python3.12 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
make install && make test && make e2e                       # proves the code before containers
cp .env.example .env                                        # optional: change POSTGRES_PASSWORD
```

Windows users: run the labs from WSL2 (Ubuntu) for `make` and the shell syntax used here.

## 1A. Docker Desktop

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), start it, and in **Settings → Resources** give it at least 2 CPUs, 4 GiB RAM and 20 GiB disk.
2. Containers:

   ```bash
   make up-docker            # Postgres + API with Compose, then the smoke test
   make ingest-docker ARGS="ingest-synthetic --count 5000"     # offline data
   make ingest-docker ARGS="ingest-api --days 7"               # real CFPB data
   mkdir -p data && cp tests/fixtures/cfpb_sample.csv data/   # or a CSV of your own
   make ingest-docker ARGS="ingest-csv /data/cfpb_sample.csv"
   curl -s http://127.0.0.1:8000/api/v1/runs | python -m json.tool
   docker compose -f deploy/compose/compose.yaml ps
   docker compose -f deploy/compose/compose.yaml logs --tail=50 api
   make down-docker          # -v also removes the database volume
   ```

3. Kubernetes: **Settings → Kubernetes → Enable Kubernetes**, wait for the green light, then:

   ```bash
   make k8s-docker           # builds, applies the overlay (API, Postgres StatefulSet, CronJob), smoke test
   kubectl --context docker-desktop -n fde get pods,svc,pvc,cronjob,hpa,pdb
   make k8s-ingest           # runs the (suspended) CronJob once
   kubectl --context docker-desktop -n fde get jobs && kubectl -n fde logs job/<name>
   make k8s-delete
   ```

## 1B. Podman Desktop

1. Install [Podman Desktop](https://podman-desktop.io/). On Windows and macOS, create and start a Podman machine (2+ CPUs, 4+ GiB):

   ```bash
   podman machine init --cpus 2 --memory 4096 --disk-size 30
   podman machine start
   podman info | head
   ```

2. Pod (the Kubernetes-style path):

   ```bash
   make up-podman            # podman build + podman kube play (Postgres + API in one pod) + smoke test
   make ingest-podman ARGS="ingest-api --days 7"    # runs the CLI inside the api container
   podman pod ps && podman logs fde-00-programming-api
   make down-podman          # the named volume fde-00-programming-pgdata survives; podman volume rm to reset
   ```

   The first start can fail readiness once while Postgres initialises; the smoke test waits for `/health/ready`.

3. Compose alternative: `make up-podman-compose` (needs `podman compose`, which uses docker-compose or podman-compose).
4. Kubernetes with kind: install [kind](https://kind.sigs.k8s.io/), or install it through Podman Desktop's Kind integration, then:

   ```bash
   export KIND_EXPERIMENTAL_PROVIDER=podman
   make k8s-kind             # creates cluster 'fde', loads the image, applies the kind overlay, smoke test
   kind delete cluster --name fde
   ```

Notes: Podman is rootless by default, which matches the non-root image. On SELinux hosts (Fedora, RHEL) add `:Z` to bind mounts you create yourself.

## 1C. Rancher Desktop

1. Install [Rancher Desktop](https://rancherdesktop.io/). In **Preferences → Container Engine** choose **dockerd (moby)**; in **Preferences → Kubernetes** enable Kubernetes. Give the VM 2+ CPUs and 4+ GiB.
2. Rancher Desktop sets a `rancher-desktop` Docker context. Containers:

   ```bash
   docker context ls
   make up-rancher           # docker --context rancher-desktop compose up, then the smoke test
   make ingest-rancher ARGS="ingest-api --days 7"
   make down-rancher
   ```

3. Kubernetes (k3s). With the moby engine, k3s sees images you build, so no registry is needed:

   ```bash
   make k8s-rancher          # build, apply the rancher-desktop overlay, port-forward, smoke test
   kubectl --context rancher-desktop -n fde get pods,pvc
   make k8s-ingest
   make k8s-delete
   ```

   Using the **containerd** engine instead? Build with `nerdctl --namespace k8s.io build -t fde-00-programming:local .` and run `make k8s-rancher RANCHER="nerdctl --namespace k8s.io"`.

## 2. Observability (any desktop)

```bash
docker compose -f deploy/compose/compose.yaml --profile observability up -d --build
# Prometheus http://127.0.0.1:9090 · Grafana http://127.0.0.1:3000 → "FDE service overview"
# Panels include complaints stored and hours since the last ingest; alerts.yml has IngestStale.
```

## 3. Evidence for your portfolio

Capture: the smoke-test output, the ingest run log (`/api/v1/runs`) after a real CFPB pull, `kubectl get pods` showing Ready, a Grafana screenshot, and the commit SHA. Note which desktop and versions you used.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `port is already allocated` | Another engine or old stack on 8000 | Stop the other desktop; `make down-*`; or `HOST_PORT=8080 make up-docker` |
| Pod `ImagePullBackOff` on desktop Kubernetes | Cluster cannot see the local image | Docker/Rancher: build with the same engine as the cluster. kind: re-run `make k8s-kind` (it loads the image) |
| `CreateContainerConfigError` | Secret `fde-00-programming-db` missing | Desktop overlays create it; on cloud/OpenShift create it yourself (see `docs/DEPLOYMENT.md`) |
| API readiness 503 `database unavailable` | Postgres still starting or wrong `DATABASE_URL` | Wait for `pg_isready`; `docker compose logs db`; `kubectl -n fde get pods` |
| Postgres pod pending | PVC not bound (no default StorageClass) | `kubectl get sc`; kind, Docker and Rancher Desktop ship one by default |
| `ingest-api` fails with a connect error | No internet from the container, or CFPB down | Try `ingest-synthetic`; check proxy settings of the desktop VM |
| Podman `kube play` port not reachable | Podman machine not running | `podman machine start` |
| Rancher `docker: context not found` | Engine set to containerd | Switch to dockerd (moby) or use `nerdctl` as above |
| Smoke test times out | Container crashed on start | `docker compose ... logs api`, `podman logs`, or `kubectl logs` |
