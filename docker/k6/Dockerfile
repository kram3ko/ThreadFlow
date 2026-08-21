FROM grafana/k6:2.2.0

WORKDIR /scripts
COPY --chown=k6:k6 load-tests ./

ENTRYPOINT ["k6"]
