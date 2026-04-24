// HANDLES LOGIN AND REGISTRATION
const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const UserModel = require('../models/User.model');

// Login endpoint
router.post('/login', async (req, res) => {
  try {
    const { loginType, value } = req.body;
    
    // Validate input
    if (!loginType || !value) {
      return res.status(400).json({ 
        success: false, 
        message: 'Please provide login credentials' 
      });
    }
    
    // Check if user exists
    let user = UserModel.findByLoginId(value);
    
    // If not, create new user
    if (!user) {
      user = UserModel.create(value, loginType);
      console.log(`📝 New user created: ${value}`);
    } else {
      console.log(`👋 Returning user: ${value}`);
    }
    
    // Create JWT token
    const token = jwt.sign(
      { userId: user.id }, 
      process.env.JWT_SECRET || 'secret',
      { expiresIn: '7d' }
    );
    
    // Send response
    res.json({
      success: true,
      token: token,
      user: {
        id: user.id,
        loginId: user.loginId,
        loginType: user.loginType,
        profile: user.profile,
        streak: user.streak
      }
    });
    
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Server error during login' 
    });
  }
});

module.exports = router;