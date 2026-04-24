// HANDLES GENERATING AI ANSWERS
const Groq = require('groq-sdk');

// Initialize Groq client (reads API key from .env file)
const groq = new Groq({
    apiKey: process.env.GROQ_API_KEY
});

// REAL AI function using Groq API
async function getRealAIAnswer(question, documents) {
    try {
        // Combine all document texts
        const context = documents.map(doc => doc.extractedText || doc.name).join('\n\n');
        
        const completion = await groq.chat.completions.create({
            messages: [
                {
                    role: "system",
                    content: `You are a helpful tutor. Answer questions based ONLY on this study material. If the answer isn't in the material, say so politely:\n\n${context}`
                },
                {
                    role: "user",
                    content: question
                }
            ],
            model: "llama-3.1-8b-instant",
            temperature: 0.7,
        });
        
        return {
            text: completion.choices[0]?.message?.content || "Sorry, I couldn't generate an answer.",
            source: "🤖 AI based on your uploaded materials",
            confidence: 90
        };
    } catch (error) {
        console.error('Groq API error:', error);
        return null; // Fallback to mock answer
    }
}

// Original mock function (kept as fallback)
function getMockAnswer(question, documents) {
  // Check if user has uploaded any documents
  if (documents.length === 0) {
    return {
      text: "⚠️ Please upload your notes or past papers first! I can only answer based on YOUR materials.",
      source: "No documents uploaded",
      confidence: 0
    };
  }
  
  const doc = documents[0];
  const questionLower = question.toLowerCase();
  let answerText = "";
  
  // Simple keyword matching for demo
  if (questionLower.includes('hess') || questionLower.includes('enthalpy')) {
    answerText = "Hess's Law states that the total enthalpy change is independent of the pathway. ΔH°rxn = ΣΔH°f(products) - ΣΔH°f(reactants)";
  } 
  else if (questionLower.includes('calculus') || questionLower.includes('derivative')) {
    answerText = "The derivative measures instantaneous rate of change. d/dx[x^n] = n·x^(n-1)";
  } 
  else if (questionLower.includes('newton') || questionLower.includes('force')) {
    answerText = "Newton's Second Law: F = ma (Force = mass × acceleration)";
  } 
  else if (questionLower.includes('photosynthesis')) {
    answerText = "Photosynthesis converts light energy to chemical energy: 6CO₂ + 6H₂O → C₆H₁₂O₆ + 6O₂";
  }
  else {
    answerText = `Based on your document "${doc.name}", review the section about ${doc.topics.join(', ')} to find the answer to: "${question}"`;
  }
  
  return {
    text: answerText,
    source: `📌 Based on: ${doc.name}`,
    confidence: 85
  };
}

// Main function - tries real AI first, falls back to mock
async function getAIAnswer(question, documents) {
  // Check if user has uploaded any documents
  if (documents.length === 0) {
    return {
      text: "⚠️ Please upload your notes or past papers first! I can only answer based on YOUR materials.",
      source: "No documents uploaded",
      confidence: 0
    };
  }
  
  // Try real AI if Groq API key is available
  if (process.env.GROQ_API_KEY) {
    const realAnswer = await getRealAIAnswer(question, documents);
    if (realAnswer) {
      return realAnswer;
    }
  }
  
  // Fallback to mock answer
  return getMockAnswer(question, documents);
}

module.exports = { getAIAnswer };