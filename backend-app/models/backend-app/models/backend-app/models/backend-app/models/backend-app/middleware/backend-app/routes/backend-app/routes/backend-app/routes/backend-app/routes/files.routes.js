// HANDLES FILE UPLOADS
const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const { authenticateToken } = require('../middleware/auth.middleware');
const DocumentModel = require('../models/Document.model');
const { extractTopicsFromFilename } = require('../services/fileProcessor.service');

// Configure file storage
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, './backend-app/uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueName = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueName + path.extname(file.originalname));
  }
});

const upload = multer({ 
  storage: storage,
  limits: { fileSize: 10 * 1024 * 1024 } // 10MB limit
});

// Upload notes
router.post('/notes', authenticateToken, upload.array('files', 10), (req, res) => {
  try {
    const uploadedFiles = [];
    
    req.files.forEach(file => {
      const topics = extractTopicsFromFilename(file.originalname);
      const doc = DocumentModel.addDocument(
        req.userId, 
        'notes', 
        { originalName: file.originalname, filename: file.filename },
        topics
      );
      uploadedFiles.push(doc);
    });
    
    res.json({
      success: true,
      message: `${uploadedFiles.length} file(s) uploaded`,
      files: uploadedFiles
    });
    
  } catch (error) {
    console.error('Upload error:', error);
    res.status(500).json({ success: false, message: 'Error uploading files' });
  }
});

// Upload past papers
router.post('/papers', authenticateToken, upload.array('files', 10), (req, res) => {
  try {
    const uploadedFiles = [];
    
    req.files.forEach(file => {
      const topics = extractTopicsFromFilename(file.originalname);
      const doc = DocumentModel.addDocument(
        req.userId, 
        'paper', 
        { originalName: file.originalname, filename: file.filename },
        topics
      );
      uploadedFiles.push(doc);
    });
    
    res.json({
      success: true,
      message: `${uploadedFiles.length} paper(s) uploaded`,
      files: uploadedFiles
    });
    
  } catch (error) {
    res.status(500).json({ success: false, message: 'Error uploading files' });
  }
});

// Delete file
router.delete('/:fileId', authenticateToken, (req, res) => {
  DocumentModel.deleteDocument(req.userId, req.params.fileId);
  res.json({ success: true, message: 'File deleted' });
});

module.exports = router;