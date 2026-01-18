FROM node:20-alpine

WORKDIR /app
COPY package.json ./
# Don't copy package-lock.json - it has host platform-specific optional deps
RUN npm install

COPY . .
WORKDIR /app

EXPOSE 5173
CMD ["npm", "run", "-s", "nx", "--", "serve", "frontend"]
