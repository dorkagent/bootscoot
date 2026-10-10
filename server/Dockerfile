FROM node:20-slim
WORKDIR /app
COPY javascript/ ./javascript/
COPY server/ ./server/
ENV PORT=3000
EXPOSE 3000
CMD ["node", "server/server.js"]
