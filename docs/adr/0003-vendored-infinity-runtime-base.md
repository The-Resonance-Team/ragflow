# Vendored Infinity runtime base: ubuntu:24.04 with the v0.7.3 release artifacts

The `infiniflow/infinity:v0.7.3-arm64` image bases its runtime on `ubuntu:22.04` (glibc 2.35), but the release binary requires `GLIBC_2.36`/`GLIBC_2.38`, so the container dies in the loader before the server starts. Upstream `scripts/Dockerfile_infinity` still pins `ubuntu:22.04` on `main`, and the broken tag has not been rebuilt. RAGFlow pinned the x64-only image (`infiniflow/infinity:v0.7.3-x64-v3`), so ARM64 hosts had no usable Infinity image at all. We build a local runtime image instead: `docker/Dockerfile_infinity` copies the arch-matched v0.7.3 binary and `/usr/share/infinity` from the official image into `ubuntu:24.04`, and `docker-compose-base.yml` builds it as `ragflow-infinity:v0.7.3` for each host architecture.

## Considered Options

- Bump `FROM ubuntu:22.04` to `ubuntu:24.04` in the infinity repo and wait for a republished tag — rejected: outside this repository, no rebuild or re-push path here, and ARM64 deployments stay broken meanwhile.
- Keep the registry pull for x64 and ship an ARM-only compose override — rejected: two deployment paths for one service; the vendored base works for every architecture from the same source artifacts.
- Copy the binary from a GitHub release tarball — rejected: the published image is the release vehicle; no verified standalone tarball exists for `v0.7.3`.
- Use the multi-arch `v0.7.0`/`nightly` images as the copy source — rejected: version drift from the pinned `v0.7.3` release.
- Pin the source images by digest — rejected: this repo pins Infinity by tag today; revisit if upstream republishes a fixed image.

## Consequences

- Compose builds the Infinity image locally on first `up` (one apt layer plus two COPYs after BuildKit pulls the arch-matched official image as a source stage); the final image keeps the `-f /infinity_conf.toml` command and healthcheck from `docker-compose-base.yml`.
- The x64 path no longer pulls the registry image directly; `docker compose pull` cannot refresh Infinity, `docker compose build infinity` does.
- `TARGETARCH` selects the source tag (`v0.7.3-x64-v3` / `v0.7.3-arm64`) and requires BuildKit, which Compose v2 uses by default.
- Helm still references the registry tag; ARM clusters must push the locally built image and override `infinity.image.repository`/`tag`.
- Verification: x64 image builds and answers `GET /admin/node/current` with `"status":"started"`; ARM64 acceptance (periodic checkpoints on an existing `/var/infinity` index) runs on the ARM host.
