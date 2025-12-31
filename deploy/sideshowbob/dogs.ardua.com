# dogs.ardua.com - Nginx configuration for sideshowbob
# Copy to /etc/nginx/sites-available/dogs.ardua.com
# Then: ln -s /etc/nginx/sites-available/dogs.ardua.com /etc/nginx/sites-enabled/
# Then: sudo nginx -t && sudo systemctl reload nginx
# Then: sudo certbot --nginx -d dogs.ardua.com

server {
    listen 80;
    server_name dogs.ardua.com;

    # Redirect HTTP to HTTPS (certbot will add this)
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name dogs.ardua.com;

    # SSL certificates (certbot will configure these)
    # ssl_certificate /etc/letsencrypt/live/dogs.ardua.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/dogs.ardua.com/privkey.pem;

    # Proxy settings
    location / {
        proxy_pass http://frink.ardua.lan:8001;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # File upload size limit (matches Flask config)
    client_max_body_size 100M;
}
