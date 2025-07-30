# Stage 1: Install dependencies and build the Next.js application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json (if exists)
COPY package.json yarn.lock* package-lock.json* ./

# Install dependencies
RUN npm install --frozen-lockfile

# Copy the rest of the application code
COPY . .

# Build the Next.js application
RUN npm run build

# Stage 2: Run the Next.js application
FROM node:18-alpine AS runner

WORKDIR /app

# Set environment variables for production
ENV NODE_ENV=production

# Copy the standalone output
COPY --from=builder /app/.next/standalone ./ 

# Expose the port Next.js runs on
EXPOSE 3000

# Start the Next.js application
CMD ["node", "server.js"]