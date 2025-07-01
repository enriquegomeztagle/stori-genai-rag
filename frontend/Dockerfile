FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

RUN apk add --no-cache curl

COPY generate-config.sh ./generate-config.sh
RUN chmod +x ./generate-config.sh

RUN npm install -g serve
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

CMD ["/bin/sh", "-c", "./generate-config.sh && serve -s dist -l 3000"] 
