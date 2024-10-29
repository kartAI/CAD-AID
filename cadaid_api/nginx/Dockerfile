# Use the official Nginx image as the base image
FROM nginx:latest

# Remove the default configuration file
RUN rm /etc/nginx/nginx.conf

# Copy the custom configuration file to the container
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Startup delay
CMD ["sh", "-c", "sleep 10 && nginx -g 'daemon off;'"]