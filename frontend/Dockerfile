# =============================================
# SCP World Frontend — Multi-stage Dockerfile
# Stage 1: Build Flutter web app
# Stage 2: Serve with Nginx
# =============================================

# Stage 1: Build
FROM ghcr.io/cirruslabs/flutter:stable AS builder
WORKDIR /app
COPY pubspec.* ./
RUN flutter pub get
COPY . .
RUN flutter build web --release --dart-define=GOOGLE_CLIENT_ID="1087559947666-uuelrdfelo0c76nm837e4v9epv5er3sa.apps.googleusercontent.com"

# Stage 2: Serve
FROM nginx:alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/build/web /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
