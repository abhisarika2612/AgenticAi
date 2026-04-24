// THIS IS THE MAIN SERVER FILE - STARTS EVERYTHING
require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

// Import all routes
const authRoutes = require('./backend-app/routes/auth.routes');
const userRoutes = require('./backend-app/routes/user.routes');
const doubtRoutes = require('./backend-app/routes/doubt.routes');
const fileRoutes = require('./backend-app/routes/files.routes');

const app = express();

// Security middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Rate limiting (prevents too many requests)
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100
});
app.use(limiter);

// Register all routes
app.use('/api/auth', authRoutes);
app.use('/api/user', userRoutes);
app.use('/api/doubt', doubtRoutes);
app.use('/api/files', fileRoutes);

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`✅ Server is running on http://localhost:${PORT}`);
  console.log(`📍 Waiting for frontend to connect...`);
});