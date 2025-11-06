FROM nginx:1.27-alpine

# Remove default site so only our virtual hosts are active
RUN rm -f /etc/nginx/conf.d/default.conf

# Ship the curated Nginx configuration with the image
COPY conf.d/ /etc/nginx/conf.d/

# Provide a writable webroot for ACME HTTP challenges
RUN mkdir -p /var/www/html && chown -R nginx:nginx /var/www/html
