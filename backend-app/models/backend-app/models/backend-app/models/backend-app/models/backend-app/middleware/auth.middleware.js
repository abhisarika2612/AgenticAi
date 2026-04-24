// VERIFIES USER TOKENS (LIKE A SECURITY GUARD)
const jwt = require('jsonwebtoken');

function authenticateToken(req, res, next) {
  // Get token from request headers
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ 
      success: false, 
      message: 'Access denied. No token provided.' 
    });
  }
  
  // Verify token
  jwt.verify(token, process.env.JWT_SECRET || 'secret', (err, decoded) => {
    if (err) {
      return res.status(403).json({ 
        success: false, 
        message: 'Invalid or expired token' 
      });
    }
    
    // Add user ID to request for use in routes
    req.userId = decoded.userId;
    next();
  });
}

module.exports = { authenticateToken };