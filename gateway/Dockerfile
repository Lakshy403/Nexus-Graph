# ---- Nexus-Graph Gateway ----
FROM node:20-alpine

WORKDIR /app

COPY gateway/package*.json ./
RUN npm install --omit=dev

COPY gateway .
COPY shared/proto ./shared/proto

EXPOSE 3000

CMD ["node", "src/index.js"]
