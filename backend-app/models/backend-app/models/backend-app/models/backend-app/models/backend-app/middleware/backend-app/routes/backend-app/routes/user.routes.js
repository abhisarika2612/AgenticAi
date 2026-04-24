// HANDLES USER PROFILE AND DATA
const express = require('express');
const router = express.Router();
const { authenticateToken } = require('../middleware/auth.middleware');
const UserModel = require('../models/User.model');
const DocumentModel = require('../models/Document.model');
const HistoryModel = require('../models/History.model');
const TopicProgressModel = require('../models/TopicProgress.model');

// Get all user data
router.get('/data', authenticateToken, (req, res) => {
  try {
    const user = UserModel.findById(req.userId);
    const documents = DocumentModel.getUserDocuments(req.userId);
    const history = HistoryModel.getUserHistory(req.userId);
    const progress = TopicProgressModel.getProgress(req.userId);
    
    res.json({
      success: true,
      data: {
        searchHistory: history,
        uploadedNotes: documents.notes,
        uploadedPapers: documents.papers,
        topicProgress: progress,
        streak: user.streak,
        userProfile: user.profile
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Error loading user data' });
  }
});

// Update profile
router.put('/profile', authenticateToken, (req, res) => {
  try {
    const { name, birthDate, grade, avatar } = req.body;
    const user = UserModel.findById(req.userId);
    
    user.profile = { name, birthDate, grade, avatar };
    UserModel.update(req.userId, user);
    
    res.json({ success: true, message: 'Profile updated', profile: user.profile });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Error updating profile' });
  }
});

// Increase streak
router.post('/streak', authenticateToken, (req, res) => {
  try {
    const user = UserModel.findById(req.userId);
    user.streak += 1;
    UserModel.update(req.userId, user);
    
    res.json({ success: true, streak: user.streak });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Error updating streak' });
  }
});

// Clear all history
router.delete('/history', authenticateToken, (req, res) => {
  HistoryModel.clearHistory(req.userId);
  res.json({ success: true, message: 'History cleared' });
});

// Delete single history entry
router.delete('/history/:id', authenticateToken, (req, res) => {
  HistoryModel.deleteEntry(req.userId, req.params.id);
  res.json({ success: true, message: 'Entry deleted' });
});

module.exports = router;