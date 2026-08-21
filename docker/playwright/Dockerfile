FROM mcr.microsoft.com/playwright:v1.62.1-noble

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./

ENTRYPOINT ["npm", "run", "test:e2e", "--"]
