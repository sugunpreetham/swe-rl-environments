FROM node:20-slim

WORKDIR /app

COPY package.json tsconfig.json ./
RUN npm install -g typescript ts-node

COPY . ./
RUN npm run build || true

CMD ["npm", "test"]
