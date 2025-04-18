import React, { useState, useEffect } from 'react';

// Component to show the AI Interviewer and Face Recognition UI
const InterviewPage = () => {
  const [status, setStatus] = useState({
    emotion: "N/A",
    face_dir: "N/A",
    eye_dir: "N/A",
    match: "N/A"
  });

  // Fetch the current status from the backend periodically
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch("http://localhost:8001/status");
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error("Error fetching status:", error);
      }
    };

    // Polling every 2 seconds to update the status
    const intervalId = setInterval(fetchStatus, 2000);

    return () => clearInterval(intervalId); // Cleanup interval on component unmount
  }, []);

  return (
    <div style={styles.container}>
      {/* AI Interview Chat */}
      <div style={styles.chatContainer}>
        <InterviewChat />
      </div>

      {/* Face Recognition Status */}
      <div style={styles.faceRecognitionContainer}>
        <div style={styles.faceRecognitionBox}>
          <div style={styles.faceStatus}>
            Emotion: {status.emotion} | Face Direction: {status.face_dir} | Match: {status.match}
          </div>

          {/* Display the webcam stream using an <img> for MJPEG compatibility */}
          <img
            style={styles.videoStream}
            src="http://localhost:8001/video_feed"
            alt="Live Face Feed"
          />
        </div>
      </div>
    </div>
  );
};

// AI Interview Chat component (just a placeholder for now)
const InterviewChat = () => {
  return (
    <div style={styles.chatBox}>
      <h3>AI Interviewer</h3>
      {/* Here, you would include your AI interviewer chat logic */}
      <p>Chat with the AI interviewer...</p>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    position: 'relative',
    padding: '20px',
    backgroundColor: '#f0f4f8',
  },
  chatContainer: {
    flex: 1,
    marginBottom: '20px',
    backgroundColor: '#ffffff',
    padding: '16px',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  },
  chatBox: {
    padding: '20px',
    background: '#ffffff',
    borderRadius: '8px',
    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
  },
  faceRecognitionContainer: {
    position: 'absolute',
    top: '16px',
    right: '16px',
    zIndex: 10,
    backgroundColor: '#ffffff',
    padding: '16px',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
  },
  faceRecognitionBox: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    padding: '16px',
    borderRadius: '8px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  },
  faceStatus: {
    fontSize: '16px',
    fontWeight: 'bold',
    marginBottom: '8px',
    color: '#4b5563',
  },
  videoStream: {
    borderRadius: '50%',
    border: '2px solid #f3f4f6',
    marginTop: '8px',
    width: '200px',
    height: '200px',
    objectFit: 'cover',
  },
};

export default InterviewPage;
