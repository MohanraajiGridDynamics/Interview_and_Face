import React, { useState, useEffect } from 'react';

const InterviewChat = () => {
  const [messages, setMessages] = useState([]);
  const [websocket, setWebsocket] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [isConnecting, setIsConnecting] = useState(true);
  const [transcript, setTranscript] = useState('');
  const [recognition, setRecognition] = useState(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/interview/');
    
    ws.onopen = () => {
      console.log('Connected to WebSocket');
      setIsConnecting(false);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prevMessages) => [...prevMessages, data]);
    };

    ws.onerror = (error) => {
      console.log('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed');
      stopListening();
    };

    setWebsocket(ws);

    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = 'en-US';
      
      recognitionInstance.onstart = () => {
        console.log('Speech recognition started');
        setIsListening(true);
        setTranscript('');
      };
      
      recognitionInstance.onresult = (event) => {
        const current = event.resultIndex;
        const transcriptText = event.results[current][0].transcript;
        setTranscript(transcriptText);
      };
      
      recognitionInstance.onend = () => {
        console.log('Speech recognition ended');
        setIsListening(false);
        
        // Send the transcript as a message if it's not empty
        if (transcript.trim() !== '') {
          sendMessage(transcript);
        }
      };
      
      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        setIsListening(false);
      };
      
      setRecognition(recognitionInstance);
    } else {
      console.log('Speech recognition not supported');
    }

    return () => {
      ws.close();
      if (recognition) {
        recognition.abort();
      }
    };
    // eslint-disable-next-line
  }, []);
  
  // Handle transcript changes
  useEffect(() => {
    console.log('Transcript updated:', transcript);
  }, [transcript]);

  const startListening = () => {
    if (recognition) {
      try {
        recognition.start();
        setIsListening(true);
      } catch (error) {
        console.error('Error starting speech recognition:', error);
      }
    }
  };

  const stopListening = () => {
    if (recognition) {
      recognition.stop();
      setIsListening(false);
    }
  };

  const sendMessage = (message) => {
    if (message && websocket) {
      websocket.send(JSON.stringify({ sender: 'Candidate', message }));
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'Candidate', message },
      ]);
    }
  };
// eslint-disable-next-line 
  const toggleMicrophone = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <h1 style={styles.title}>AI Interview Assistant</h1>
          <div style={styles.statusContainer}>
            <span style={{
              ...styles.statusDot,
              backgroundColor: isConnecting ? '#f59e0b' : isListening ? '#10b981' : '#3730a3'
            }}></span>
            <span style={styles.statusText}>
              {isConnecting ? 'Connecting...' : isListening ? 'Listening' : 'Connected'}
            </span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div style={styles.content}>
        {/* Messages area */}
        <div style={styles.messagesContainer}>
          {messages.length === 0 ? (
            <div style={styles.emptyState}>
              <svg style={styles.emptyStateIcon} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
              </svg>
              <p style={styles.emptyStateText}>Your interview will begin shortly. The AI interviewer will guide you through the process.</p>
            </div>
          ) : (
            <ul style={styles.messagesList}>
              {messages.map((msg, index) => (
                <li 
                  key={index} 
                  style={{
                    ...styles.messageItem,
                    backgroundColor: msg.sender === 'Candidate' ? '#e0e7ff' : '#f3f4f6',
                    marginLeft: msg.sender === 'Candidate' ? 'auto' : '0',
                    textAlign: msg.sender === 'Candidate' ? 'right' : 'left',
                  }}
                >
                  <div style={styles.messageSender}>{msg.sender}</div>
                  <div style={styles.messageContent}>{msg.message}</div>
                </li>
              ))}
              {/* Show current transcription if listening */}
              {isListening && transcript && (
                <li style={{
                  ...styles.messageItem,
                  backgroundColor: '#f0fdf4',
                  marginLeft: 'auto',
                  textAlign: 'right',
                  opacity: 0.7
                }}>
                  <div style={styles.messageSender}>You (speaking)</div>
                  <div style={styles.messageContent}>{transcript}...</div>
                </li>
              )}
            </ul>
          )}
        </div>

        
      </div>

      {/* Footer */}
      <footer style={styles.footer}>
        <div style={styles.footerContent}>
          <p>Press the microphone button to start speaking. Press it again to stop.</p>
          <p style={styles.footerSubtext}>This interview is being recorded for assessment purposes.</p>
        </div>
      </footer>
    </div>
  );
};

// CSS Styles
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: 'linear-gradient(to bottom right, #f0f4ff, #e0e7ff)',
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
  },
  header: {
    backgroundColor: '#ffffff',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    padding: '16px'
  },
  headerContent: {
    maxWidth: '900px',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#3730a3',
    margin: 0
  },
  statusContainer: {
    display: 'flex',
    alignItems: 'center'
  },
  statusDot: {
    display: 'inline-block',
    height: '12px',
    width: '12px',
    borderRadius: '50%',
    marginRight: '8px'
  },
  statusText: {
    fontSize: '14px',
    color: '#4b5563'
  },
  content: {
    flexGrow: 1,
    padding: '16px',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    maxWidth: '900px',
    margin: '0 auto',
    width: '100%'
  },
  messagesContainer: {
    flexGrow: 1,
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    padding: '24px',
    marginBottom: '16px',
    overflowY: 'auto'
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: '#9ca3af'
  },
  emptyStateIcon: {
    width: '64px',
    height: '64px',
    marginBottom: '16px'
  },
  emptyStateText: {
    textAlign: 'center'
  },
  messagesList: {
    listStyleType: 'none',
    padding: 0,
    margin: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: '16px'
  },
  messageItem: {
    padding: '16px',
    borderRadius: '8px',
    maxWidth: '75%',
    boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
  },
  messageSender: {
    fontWeight: 'bold',
    marginBottom: '4px',
    color: '#3730a3'
  },
  messageContent: {
    color: '#1f2937'
  },
  controlsContainer: {
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    padding: '24px'
  },
  controlsContent: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  },
  instructions: {
    color: '#4b5563'
  },
  listeningText: {
    color: '#10b981',
    fontWeight: 'bold',
    animation: 'pulse 2s infinite',
    margin: 0
  },
  micButton: {
    padding: '16px',
    borderRadius: '50%',
    border: 'none',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    color: '#ffffff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  waveContainer: {
    marginTop: '16px'
  },
  waveBackground: {
    height: '32px',
    backgroundColor: '#f3f4f6',
    borderRadius: '16px',
    overflow: 'hidden'
  },
  waveAnimation: {
    height: '100%',
    width: '10%',
    backgroundColor: '#4f46e5',
    borderRadius: '16px',
    animation: 'pulse 2s infinite'
  },
  footer: {
    backgroundColor: '#ffffff',
    padding: '16px',
    boxShadow: '0 -2px 4px rgba(0, 0, 0, 0.05)'
  },
  footerContent: {
    maxWidth: '900px',
    margin: '0 auto',
    textAlign: 'center',
    fontSize: '14px',
    color: '#6b7280'
  },
  footerSubtext: {
    marginTop: '4px'
  },
  '@keyframes pulse': {
    '0%': { opacity: 1 },
    '50%': { opacity: 0.5 },
    '100%': { opacity: 1 }
  }
};

export default InterviewChat;