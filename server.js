const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public')); // Serve static files from public directory

// MongoDB connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/cognisphere', {
    useNewUrlParser: true,
    useUnifiedTopology: true
})
.then(() => console.log('Connected to MongoDB'))
.catch(err => console.error('MongoDB connection error:', err));

// Feedback Schema
const feedbackSchema = new mongoose.Schema({
    overallRating: [{
        type: String,
        enum: ['excellent', 'good', 'average', 'poor', 'very-poor']
    }],
    easeOfUse: [{
        type: String,
        enum: ['excellent', 'good', 'average', 'poor', 'very-poor']
    }],
    facedIssues: {
        type: String,
        required: true,
        enum: ['yes', 'no']
    },
    issuesDescription: {
        type: String,
        default: ''
    },
    accuracy: [{
        type: String,
        enum: ['1', '2', '3', '4']
    }],
    generalFeedback: {
        type: String,
        required: true
    },
    timestamp: {
        type: Date,
        default: Date.now
    }
});

// Feedback Model
const Feedback = mongoose.model('Feedback', feedbackSchema);

// Feedback Routes
app.post('/api/feedback', async (req, res) => {
    try {
        console.log('Received feedback:', req.body); // Log the received data for debugging
        
        // Validate required fields
        if (!req.body.overallRating || !req.body.easeOfUse || !req.body.accuracy) {
            return res.status(400).json({ error: 'Please select at least one option for each rating section' });
        }

        const feedback = new Feedback(req.body);
        await feedback.save();
        
        console.log('Feedback saved successfully'); // Log success
        res.status(201).json({ message: 'Feedback submitted successfully' });
    } catch (error) {
        console.error('Error saving feedback:', error);
        res.status(500).json({ 
            error: 'Failed to save feedback',
            details: error.message 
        });
    }
});

// Get all feedback (for admin purposes)
app.get('/api/feedback', async (req, res) => {
    try {
        const feedback = await Feedback.find().sort({ timestamp: -1 });
        res.json(feedback);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch feedback' });
    }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
