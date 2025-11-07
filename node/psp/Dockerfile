FROM node:18-slim
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production
COPY sim.js .
EXPOSE 9000
CMD ["node","sim.js"]
