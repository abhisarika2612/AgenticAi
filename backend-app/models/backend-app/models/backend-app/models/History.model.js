// TRACKS ALL QUESTIONS AND ANSWERS FOR EACH USER

const userHistory = new Map(); // Stores history per user

class HistoryModel {
  static addEntry(userId, question, answer, confidence) {
    if (!userHistory.has(userId)) {
      userHistory.set(userId, []);
    }
    
    const entry = {
      id: Date.now().toString(),
      question: question.substring(0, 200),
      answer: answer.substring(0, 500),
      confidence: confidence,
      time: new Date().toLocaleString(),
      timestamp: new Date()
    };
    
    const history = userHistory.get(userId);
    history.unshift(entry);
    
    // Keep only last 30 entries
    if (history.length > 30) history.pop();
    
    userHistory.set(userId, history);
    return entry;
  }
  
  static getUserHistory(userId) {
    return userHistory.get(userId) || [];
  }
  
  static deleteEntry(userId, entryId) {
    const history = userHistory.get(userId);
    if (!history) return false;
    
    const filtered = history.filter(e => e.id !== entryId);
    userHistory.set(userId, filtered);
    return true;
  }
  
  static clearHistory(userId) {
    userHistory.set(userId, []);
  }
}

module.exports = HistoryModel;