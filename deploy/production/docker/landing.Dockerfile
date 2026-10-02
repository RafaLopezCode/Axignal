FROM nginx:1.27-alpine

ARG AXIGNAL_CODE_SHA
LABEL org.opencontainers.image.title="AXIGNAL Landing" \
      org.opencontainers.image.source="https://github.com/RafaLopezCode/Axignal" \
      org.opencontainers.image.revision="$AXIGNAL_CODE_SHA"

COPY deploy/production/docker/landing-nginx.conf /etc/nginx/nginx.conf
COPY apps/web/landing/ /usr/share/nginx/html/
COPY apps/web/knowledge/ /usr/share/nginx/html/knowledge/

USER nginx

ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
