FROM node:22-alpine

WORKDIR /app

# Copiar package files
COPY package.json ./

# Instalar dependências
RUN npm install

# Copiar código fonte
COPY . .

# Porta
EXPOSE 3000

# Comando de desenvolvimento
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
