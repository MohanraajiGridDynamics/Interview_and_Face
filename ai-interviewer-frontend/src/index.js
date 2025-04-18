import React from 'react';
import ReactDOM from 'react-dom/client'; // <-- Important: Import from 'react-dom/client' in React 18+.
import App from './App';
import './index.css';

// Create root using createRoot instead of render
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
