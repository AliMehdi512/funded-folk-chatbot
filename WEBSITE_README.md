# 🌐 Funded Folk Chatbot Website

A beautiful, modern TypeScript/JavaScript website that integrates with your hybrid RAG chatbot API.

## 🚀 Quick Start

### 1. **Start the API Server** (if not already running)
```bash
python api_server.py
```
- API will be available at: `http://localhost:8000`

### 2. **Start the Website Server**
```bash
python serve_website.py
```
- Website will open automatically at: `http://localhost:3000`

### 3. **That's it!** 
Your chatbot website is now running! 🎉

---

## 📁 File Structure

```
├── index.html          # Main HTML page
├── styles.css          # Modern CSS styling
├── chatbot.js          # TypeScript-style JavaScript
├── serve_website.py    # Simple HTTP server
└── WEBSITE_README.md   # This file
```

---

## ✨ Features

### 🎨 **Modern UI/UX**
- **Responsive design** - Works on desktop, tablet, and mobile
- **Beautiful gradients** - Professional purple-blue theme
- **Smooth animations** - Typing indicators, fade-ins, hover effects
- **Real-time feedback** - Character count, status updates

### 🤖 **Chatbot Integration**
- **Real-time chat** - Instant messaging interface
- **API communication** - Connects to your RAG system
- **Session management** - Maintains conversation context
- **Error handling** - Graceful error messages

### 📊 **Smart Features**
- **Model information** - Shows which AI model was used
- **Response timing** - Displays processing time
- **Suggestion buttons** - Quick access to common questions
- **Health monitoring** - API status checking

---

## 🎯 How to Use

### **For Users:**
1. Type your question in the input field
2. Press Enter or click the send button
3. See the AI response with model info and timing
4. Use suggestion buttons for quick questions

### **For Developers:**
- **Debug mode**: Open browser console, access `window.chatbot`
- **API testing**: Use `window.chatbotUtils.testAPI()`
- **Health check**: Use `window.chatbotUtils.checkHealth()`

---

## 🔧 Customization

### **Change API URL**
Edit `chatbot.js` line 4:
```javascript
this.apiUrl = 'http://localhost:8000'; // Change to your API URL
```

### **Modify Styling**
Edit `styles.css` to change:
- Colors and gradients
- Fonts and spacing
- Animations and effects
- Mobile responsiveness

### **Add Features**
Extend `chatbot.js` to add:
- File uploads
- Voice messages
- Chat history
- User authentication

---

## 🌐 Production Deployment

### **Option 1: Static Hosting**
Upload files to:
- **Netlify**: Drag and drop the folder
- **Vercel**: Connect your GitHub repo
- **GitHub Pages**: Push to a repository

### **Option 2: Custom Server**
Replace `serve_website.py` with:
- **Nginx**: For high-traffic sites
- **Apache**: Traditional web server
- **Node.js**: Express.js server

### **Option 3: CDN**
Serve static files from:
- **Cloudflare**: Free CDN
- **AWS S3**: Scalable storage
- **Google Cloud Storage**: Enterprise solution

---

## 🔒 Security Considerations

### **For Production:**
1. **Update API URL** to your production server
2. **Add CORS restrictions** in your API server
3. **Implement rate limiting** to prevent abuse
4. **Add authentication** if needed
5. **Use HTTPS** for all communications

### **Environment Variables:**
```bash
# .env file
API_URL=https://your-api-domain.com
ENABLE_DEBUG=false
MAX_MESSAGE_LENGTH=500
```

---

## 🐛 Troubleshooting

### **Common Issues:**

**❌ "API not available"**
- Make sure `api_server.py` is running
- Check if port 8000 is available
- Verify API health at `http://localhost:8000/health`

**❌ "CORS error"**
- API server needs CORS headers
- Check browser console for details
- Update API server CORS configuration

**❌ "Website not loading"**
- Check if port 3000 is available
- Try a different port in `serve_website.py`
- Verify all files are in the same directory

### **Debug Commands:**
```javascript
// In browser console
window.chatbot.checkHealth()           // Check API status
window.chatbotUtils.testAPI()          // Test API connection
console.log(window.chatbot.sessionId)  // View session ID
```

---

## 📈 Performance

### **Optimizations:**
- **Minified CSS/JS** for production
- **Image optimization** for any images
- **CDN delivery** for faster loading
- **Caching headers** for static assets

### **Monitoring:**
- **Response times** displayed in chat
- **API health** checked on startup
- **Error logging** in browser console
- **User session** tracking

---

## 🎉 Success!

Your Funded Folk Chatbot website is now:
- ✅ **Fully functional** with your RAG API
- ✅ **Beautiful and modern** UI design
- ✅ **Mobile responsive** for all devices
- ✅ **Production ready** with proper error handling
- ✅ **Cost optimized** with hybrid model selection

**Next steps:**
1. Test all features thoroughly
2. Customize styling to match your brand
3. Deploy to production
4. Monitor usage and performance

---

**Need help?** Check the main project README or the web integration guide for more details! 