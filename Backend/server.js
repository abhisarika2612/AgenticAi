require('dotenv').config();
const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
    res.json({ message: 'Backend is running!' });
});

app.post('/api/auth/login', (req, res) => {
    const { loginType, value } = req.body;
    res.json({ 
        success: true, 
        token: 'dummy_token',
        user: { id: '123', loginId: value }
    });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ Server running on http://0.0.0.0:${PORT}`);
    console.log(`📡 Access from other devices at: http://${getLocalIp()}:${PORT}`);
});

// Add this function at the top of server.js
function getLocalIp() {
    const { networkInterfaces } = require('os');
    const nets = networkInterfaces();
    for (const name of Object.keys(nets)) {
        for (const net of nets[name]) {
            if (net.family === 'IPv4' && !net.internal) {
                return net.address;
            }
        }
    }
    return 'localhost';
}
