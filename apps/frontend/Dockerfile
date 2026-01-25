FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
# Don't copy package-lock.json - it has host platform-specific optional deps
RUN npm install

COPY . /app

EXPOSE 3003
CMD ["npx", "nx", "serve", "@questurian/abw-client", "--host", "0.0.0.0", "--port", "3003"]
