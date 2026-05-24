Demo folder: CI (build) and CD (manifest update) examples

Overview
- `Jenkinsfile` — CI pipeline: build, test, JaCoCo, dependency-check, SonarQube, quality gate, Docker build/push, Trivy scan, smoke-test, trigger CD job.
- `Jenkinsfile-cicd` — CD pipeline: updates `kubernetes/deployment.yaml` image tag and pushes to manifest repo; Argo CD/Flux should apply it.
- `Dockerfile` — simple Spring Boot image (expects `target/*.jar`).
- `smoke-test.sh` — quick runtime test that checks `/actuator/health` on port 8080.
- `trivy-scan.sh` — runs `trivy image` and fails on HIGH/CRITICAL if `jq` present.
- `kubernetes/` — `deployment.yaml` and `service.yaml` (NodePort demo).

Quick local steps (manual)

1. Build the app with Maven:

```bash
mvn -B -DskipTests=false clean package
```

2. Build the Docker image and tag with a demo tag:

```bash
docker build -t docker.io/your-username/demo-app:local-test -f demo/Dockerfile .
```

3. Run Trivy (install Trivy first):

```bash
./demo/trivy-scan.sh docker.io/your-username/demo-app:local-test
```

4. Smoke test locally (requires Docker):

```bash
./demo/smoke-test.sh docker.io/your-username/demo-app:local-test
```

Jenkins notes
- Replace credential IDs in `Jenkinsfile` with your Jenkins credential names.
- Configure a SonarQube server in Jenkins global config and set `SONAR_SERVER` accordingly.
- The CD job requires push access to the manifest repo; set `REPO_URL` and a Jenkins Git credential.

Argo CD (GitOps)
- Point Argo CD to the manifest repository and the `kubernetes/` folder.
- Use manual sync for production and automatic sync for test environments if desired.

License
- Demo files are sample configuration for learning. Adjust to your environment before use.
