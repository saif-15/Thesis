"use client"
import { useState } from 'react';
import axios from 'axios';

const ChatDFU = () => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState('');

  const createSession = () => {
    const newSessionId = `user-${Date.now()}`;
    setSessionId(newSessionId);
    return newSessionId;
  };

  const addMessage = (message, isUserMessage = false) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { text: message, isUserMessage },
    ]);
  };

  const handleSendMessage = async () => {
    if (!sessionId) {
      createSession();
    }

    const newMessage = inputMessage;
    addMessage(newMessage, true);
    setInputMessage('');

    try {
      const response = await axios.post('/api/invoke-agent', {
        session_id: sessionId,
        user_prompt: newMessage,
        img_key: image ? image : null,
      });

      const reply = response.data.completion;
      addMessage(reply);
    } catch (error) {
      addMessage('Error occurred. Please try again later.');
    }
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    setImage(file);

    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
    };
    reader.readAsDataURL(file);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/upload-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const imgKey = response.data.img_key;
      addMessage(`Image uploaded successfully: ${imgKey}`);
    } catch (error) {
      addMessage('Failed to upload image.');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.chatBox}>
        <div style={styles.messages}>
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                ...styles.message,
                textAlign: msg.isUserMessage ? 'right' : 'left',
                backgroundColor: msg.isUserMessage ? '#f1f1f1' : '#d9fdd3',
              }}
            >
              {msg.text}
            </div>
          ))}
        </div>

        <div style={styles.inputContainer}>
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            style={styles.input}
          />
          <button onClick={handleSendMessage} style={styles.sendButton}>
            Send
          </button>
        </div>

        <div style={styles.uploadContainer}>
          <input
            type="file"
            onChange={handleImageUpload}
            style={styles.uploadInput}
          />
          {imagePreview && (
            <div style={styles.imagePreview}>
              <img src={imagePreview} alt="preview" style={styles.imagePreviewImg} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '600px',
    margin: 'auto',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
  },
  chatBox: {
    border: '1px solid #ccc',
    padding: '20px',
    borderRadius: '8px',
    backgroundColor: '#f9f9f9',
  },
  messages: {
    height: '300px',
    overflowY: 'auto',
    marginBottom: '20px',
  },
  message: {
    padding: '10px',
    margin: '5px 0',
    borderRadius: '10px',
  },
  inputContainer: {
    display: 'flex',
    marginBottom: '20px',
  },
  input: {
    width: '80%',
    padding: '10px',
    marginRight: '10px',
    borderRadius: '5px',
    border: '1px solid #ccc',
  },
  sendButton: {
    padding: '10px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '5px',
  },
  uploadContainer: {
    display: 'flex',
    justifyContent: 'center',
  },
  uploadInput: {
    marginTop: '20px',
  },
  imagePreview: {
    marginTop: '10px',
    textAlign: 'center',
  },
  imagePreviewImg: {
    maxWidth: '100%',
    borderRadius: '8px',
  },
};

export default ChatDFU;