// HANDLES ASKING QUESTIONS AND GETTING ANSWERS
const express = require('express');
const router = express.Router();
const { authenticateToken } = require('../middleware/auth.middleware');
const DocumentModel = require('../models/Document.model');
const HistoryModel = require('../models/History.model');
const { getAIAnswer } = require('../services/ai.service');

// Ask a question
router.post('/ask', authenticateToken, (req, res) => {
  try {
    const { question } = req.body;
    const userId = req.userId;
    
    if (!question || question.trim() === '') {
      return res.status(400).json({ 
        success: false, 
        message: 'Please enter a question' 
      });
    }
    
    // Get user's documents
    const documents = DocumentModel.getUserDocuments(userId);
    const allDocs = [...documents.notes, ...documents.papers];
    
    // Generate answer
    const result = getAIAnswer(question, allDocs);
    
    // Save to history
    HistoryModel.addEntry(userId, question, result.text, result.confidence);
    
    res.json({
      success: true,
      answer: result.text,
      source: result.source,
      confidence: result.confidence
    });
    
  } catch (error) {
    console.error('Error answering question:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error processing your question' 
    });
  }
});

// Generate quiz question
router.post('/generate-quiz', authenticateToken, (req, res) => {
  const documents = DocumentModel.getUserDocuments(req.userId);
  const allDocs = [...documents.notes, ...documents.papers];
  
  if (allDocs.length === 0) {
    return res.status(400).json({
      success: false,
      message: 'Please upload study materials first!'
    });
  }
  
  const randomDoc = allDocs[Math.floor(Math.random() * allDocs.length)];
  const topics = randomDoc.topics.join(', ');
  
  res.json({
    success: true,
    question: `Based on "${randomDoc.name}", explain a key concept about ${topics}.`,
    document: randomDoc.name
  });
});

module.exports = router;