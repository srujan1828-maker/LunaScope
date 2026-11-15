import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './RedesignedApp';
import './styles/utilities.css';
import './styles/index.css';
import './styles/lunascope.css';
import './styles/surface.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
