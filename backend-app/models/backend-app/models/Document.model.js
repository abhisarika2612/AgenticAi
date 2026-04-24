// STORES INFORMATION ABOUT UPLOADED FILES

const userDocuments = new Map(); // Stores documents per user

class DocumentModel {
  static addDocument(userId, type, fileInfo, topics) {
    if (!userDocuments.has(userId)) {
      userDocuments.set(userId, { notes: [], papers: [] });
    }
    
    const doc = {
      id: Date.now().toString(),
      name: fileInfo.originalName,
      filename: fileInfo.filename,
      type: type,
      topics: topics,
      uploadedAt: new Date()
    };
    
    const userDocs = userDocuments.get(userId);
    if (type === 'notes') {
      userDocs.notes.push(doc);
    } else {
      userDocs.papers.push(doc);
    }
    
    userDocuments.set(userId, userDocs);
    return doc;
  }
  
  static getUserDocuments(userId) {
    return userDocuments.get(userId) || { notes: [], papers: [] };
  }
  
  static deleteDocument(userId, docId) {
    const userDocs = userDocuments.get(userId);
    if (!userDocs) return false;
    
    userDocs.notes = userDocs.notes.filter(d => d.id !== docId);
    userDocs.papers = userDocs.papers.filter(d => d.id !== docId);
    userDocuments.set(userId, userDocs);
    return true;
  }
}

module.exports = DocumentModel;