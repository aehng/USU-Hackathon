# 1. Grab a lightweight Linux machine with Node.js pre-installed
FROM node:22-slim

WORKDIR /app

# 2. Copy the Node package files
COPY package*.json ./

# 3. Install the frontend libraries
RUN npm install

# 4. Copy the frontend code
COPY . .

# 5. Expose the port Vite uses
EXPOSE 5173

# 6. Start the frontend development server
CMD ["npm", "run", "dev", "--", "--host"]
