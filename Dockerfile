FROM nginx:stable-alpine

# Copy your static frontend files
COPY dist/ /usr/share/nginx/html/

# Copy your custom nginx.conf
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Make /tmp/nginx writable for non-root Nginx
RUN mkdir -p /tmp/nginx && chmod -R 0777 /tmp/nginx

# Expose port (matches your server block)
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]