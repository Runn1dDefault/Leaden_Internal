FROM nginx:1.19.0-alpine

COPY /nginx/dev/nginx.dev.conf /etc/nginx/conf.d/default.conf