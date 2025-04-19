import React, { useState, useEffect } from 'react';

const InterviewPage = () => {
  const [status, setStatus] = useState({
    emotion: "N/A",
    face_dir: "N/A",
    eye_dir: "N/A",
    match_status: "N/A",
    face_count: "N/A",
  });

  const [malpractice, setMalpractice] = useState({
    verdict: "Loading...",
    warning_count: 0,
  });

  // Fetch status from /status
  const fetchStatus = async () => {
    try {
      const response = await fetch("http://localhost:8001/status");
      const data = await response.json();
      setStatus(prev => ({ ...prev, ...data }));
    } catch (error) {
      console.error("Error fetching status:", error);
    }
  };

  // Fetch malpractice info from /malpractice
  const fetchMalpractice = async () => {
    try {
      const response = await fetch("http://localhost:8001/malpractice");
      const data = await response.json();

      if (data.warning_count > 5) {
        window.location.href = "/disqualified.html";
      }

      setMalpractice(prev => ({ ...prev, ...data }));
    } catch (error) {
      console.error("Error fetching malpractice:", error);
    }
  };

  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchStatus();
      fetchMalpractice();
    }, 2000);

    return () => clearInterval(intervalId);
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.chatContainer}>
        <InterviewChat />
      </div>

      <div style={styles.faceRecognitionContainer}>
        <div style={styles.faceRecognitionBox}>
          <div style={styles.faceStatus}>
            <div><strong>Emotion:</strong> {status.emotion}</div>
            <div><strong>Face Direction:</strong> {status.face_dir}</div>
            <div><strong>Eye Direction:</strong> {status.eye_dir}</div>
            <div><strong>Face Count:</strong> {status.face_count}</div>
            <div><strong>Match Status:</strong> {status.match_status}</div>
            <div><strong>Verdict:</strong> {malpractice.verdict}</div>
            <div><strong>Warning Count:</strong> {malpractice.warning_count}</div>
          </div>
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

const InterviewChat = () => {
  return (
    <div style={styles.chatBox}>
      <h3>AI Interviewer</h3>
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
    textAlign: 'left',
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
    fontSize: '14px',
    fontWeight: '500',
    marginBottom: '10px',
    color: '#374151',
    textAlign: 'left',
    width: '100%',
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
