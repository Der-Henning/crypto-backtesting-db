FROM rust:1-bookworm AS builder

WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release --locked

FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --gid 1001 --system crypto && \
    useradd --uid 1001 --gid crypto --system --no-create-home --shell /usr/sbin/nologin crypto

COPY --from=builder /app/target/release/crypto-db /usr/local/bin/crypto-db

USER crypto

ENTRYPOINT ["/usr/local/bin/crypto-db"]
