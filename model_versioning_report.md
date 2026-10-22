# Model Versioning and Rollback Strategy

## Verified deployment baseline

On October 22, 2026, the [Docker Hub tag listing](https://hub.docker.com/v2/repositories/olueniola1/sentiment-api/tags?page_size=100) returned only `latest` (last pushed October 11, 2026). Neither `v1.0` nor `v1.0.0` was listed; these were documentation examples, not verified releases.

The deployment now pins the published image index by digest:

```text
olueniola1/sentiment-api@sha256:a64ec8ed3b92d5f154d9c870ffe200aea5779486ad23a7246009c3bc01c8f789
```

This digest was fetched from the Docker Registry manifest endpoint and its SHA-256 verified against the response bytes. The index contains a Linux/amd64 image plus an attestation manifest; it does not advertise an ARM64 runtime image. Confirm target nodes support Linux/amd64 before deployment.

The digest identifies the existing published artifact, not a newly built release. Its source commit and runtime health have not been established by this check. Validate it in staging before treating it as a known-good rollback target. Retain this artifact in the registry: a digest prevents content changes but cannot prevent deletion.

## Release and versioning policy

Docker tags, including semantic version and commit-based tags, can be overwritten unless registry policy prevents it. Use unique release tags for discovery and record the resolved digest in `k8s-deployment.yaml` for deployment identity. Never use a floating tag alone for deployment or recovery.

For each future release:

1. Build and test the API with the intended model files. Record the source commit and model version/checksum. The Dockerfile uses a floating Python base tag and installs dependencies at build time, so rebuilding the same source is not proof of identical image content.
2. Publish under a new release or full-commit tag; do not reuse it. Publishing is currently a separate operator step: `.github/workflows/ci.yml` only installs dependencies and runs `pytest test_app.py` on pushes to main.
3. Verify the published tag and digest with `docker buildx imagetools inspect olueniola1/sentiment-api:TAG`, replacing TAG with the actual published tag. Check platform compatibility and pull/test the digest in staging.
4. Record the tag, digest, source commit, model identity, and staging result in the release record. Update the manifest to the verified `olueniola1/sentiment-api@sha256:...` reference in a reviewed commit. Keep earlier known-good images available.

## Deployment validation

With the intended Kubernetes context and namespace selected:

```sh
kubectl apply --dry-run=server -f k8s-deployment.yaml
kubectl diff -f k8s-deployment.yaml
kubectl apply -f k8s-deployment.yaml
kubectl rollout status deployment/sentiment-api-deployment --timeout=300s
kubectl get pods -l app=sentiment-api
```

Smoke-test POST `/predict` through the service with a JSON body such as `{"tweet":"I absolutely love this!"}`; expect HTTP 200 and the `sentiment` and `tweet` fields. Inspect pod image IDs and application logs. Rollout completion alone does not prove model correctness.

The successful October 11 Actions run tested the API endpoint, not image publication, Kubernetes deployment, or rollback. Registry verification and static manifest checks likewise do not establish runtime reliability. This manifest has no application readiness probe; zero-downtime recovery is not guaranteed.

## Rollback procedure

Prefer restoring the manifest's image reference to a previously recorded, staging-validated digest, committing that change, and applying it. This keeps Git and the cluster aligned. Do not substitute an unverified example tag.

For urgent recovery to a known-good digest:

```sh
# Set this to the exact previously validated image reference from the release record.
: "${ROLLBACK_IMAGE:?Set ROLLBACK_IMAGE to a known-good olueniola1/sentiment-api@sha256 digest}"
case "$ROLLBACK_IMAGE" in
  olueniola1/sentiment-api@sha256:*) ;;
  *) echo "Rollback requires a recorded digest reference" >&2; exit 1 ;;
esac
kubectl set image deployment/sentiment-api-deployment sentiment-api="$ROLLBACK_IMAGE"
kubectl rollout status deployment/sentiment-api-deployment --timeout=300s
```

Repeat the service smoke test and inspect logs and image IDs. Immediately update `k8s-deployment.yaml` to the same digest in Git so a later apply does not restore the faulty version.

Alternatively, inspect retained revisions with `kubectl rollout history deployment/sentiment-api-deployment` and `kubectl rollout history deployment/sentiment-api-deployment --revision=REVISION`. Only after confirming the chosen revision contains a known-good digest, run `kubectl rollout undo deployment/sentiment-api-deployment --to-revision=REVISION`, replacing REVISION with the inspected number. Then check rollout status, smoke-test, and reconcile Git. Old revisions using `:latest` do not identify the old image bytes and are not reproducible rollback targets. Undo also depends on retained revision history.

No prior known-good digest was verified during this change. Establish one through staging validation and rehearse rollback before relying on this procedure in production.
