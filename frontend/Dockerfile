FROM node:21-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy app source
COPY . .

# Expose port
EXPOSE 3000

# Set environment
ENV HOSTNAME=0.0.0.0

# Dev mode
CMD ["npm", "run", "dev"]
