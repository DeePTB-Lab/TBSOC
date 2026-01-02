import React, { useState } from 'react'
import ParameterEditor from './components/ParameterEditor'
import VisualizationDashboard from './components/VisualizationDashboard'
import './App.css'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{padding: '20px', color: '#ff6b6b'}}>
          <h1>Something went wrong.</h1>
          <pre>{this.state.error && this.state.error.toString()}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  const [status, setStatus] = useState("Idle");
  const [activeLambdas, setActiveLambdas] = useState([]); 
  const [activeFermi, setActiveFermi] = useState(0.0);
  const [activeSigma, setActiveSigma] = useState(2.0);
  const [runTrigger, setRunTrigger] = useState(0);
  const [dataVersion, setDataVersion] = useState(0); // Trigger for data reload
  
  // Theme State
  const [currentTheme, setCurrentTheme] = useState(localStorage.getItem('theme') || 'Light');
  const [themeConfig, setThemeConfig] = useState(null);
  
  // Working Directory State (Lifted from ParameterEditor)
  const [currentPath, setCurrentPath] = useState('');
  const [appVersion, setAppVersion] = useState('');

  // Initial Data Load
  React.useEffect(() => {
    // Load Version
    fetch('/api/version')
        .then(res => res.json())
        .then(data => setAppVersion(`v${data.version}`))
        .catch(console.error);

    // Load Theme
    fetch(`/themes/${currentTheme.toLowerCase()}.json`)
      .then(res => res.json())
      .then(config => {
        setThemeConfig(config);
        if (config.css) {
            Object.entries(config.css).forEach(([key, value]) => {
                document.documentElement.style.setProperty(key, value);
            });
        }
        localStorage.setItem('theme', currentTheme);
      })
      .catch(err => console.error("Failed to load theme:", err));

    // Load Current Directory
    fetch('/api/current-directory')
        .then(res => res.json())
        .then(data => setCurrentPath(data.path))
        .catch(console.error);
  }, [currentTheme]);

  const handleOpenFolder = async () => {
      try {
          const res = await fetch('/api/choose-directory', { method: 'POST' });
          const data = await res.json();
          if (data.path) {
              setCurrentPath(data.path);
          }
      } catch (err) {
          console.error("Failed to open folder:", err);
      }
  };

  const handleDataLoaded = () => {
       console.log("Data loaded, updating version");
       setDataVersion(v => v + 1);
  };

  const runFit = async (data) => {
    setStatus("Submitting...");
    setActiveFermi(parseFloat(data.Efermi) || 0.0);
    setActiveSigma(parseFloat(data.weight_sigma) || 2.0);
    try {
        const res = await fetch('/api/fit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        if (res.ok) {
            setStatus("Fitting Started");
            pollStatus();
        } else {
            const err = await res.json();
            setStatus("Error: " + err.detail);
        }
    } catch (e) {
        setStatus("Network Error: " + e.message);
    }
  };

  const pollStatus = () => {
      const interval = setInterval(async () => {
          try {
              const res = await fetch('/api/status');
              const data = await res.json();
              
              if (data.status === 'completed') {
                  clearInterval(interval);
                  setStatus("Fitting Completed");
                  if (data.result && data.result.optimized_lambdas) {
                      const newLambdas = data.result.optimized_lambdas;
                      setActiveLambdas(newLambdas);
                      setRunTrigger(prev => prev + 1);
                      // ParameterEditor updates via externalLambdas
                  }
              } else if (data.status === 'error') {
                  clearInterval(interval);
                  setStatus("Error: " + data.message);
              } else {
                  setStatus(`Fitting... ${Math.round(data.progress * 100)}%`);
              }
          } catch (e) {
              console.error(e);
          }
      }, 1000);
  };

  const handlePreview = (formData) => {
      // Called when user clicks "Preview Bands"
      console.log("Previewing with:", formData.lambdas);
      setActiveLambdas(formData.lambdas);
      setActiveFermi(parseFloat(formData.Efermi) || 0.0);
      setActiveSigma(parseFloat(formData.weight_sigma) || 2.0);
      setRunTrigger(prev => prev + 1); // Trigger refresh
      setStatus("Previewing...");
  };

  const handleStopFit = async () => {
      setStatus("Stopping...");
      try {
          await fetch('/api/fit/stop', { method: 'POST' });
          // Poll will eventually see "cancelled" or "error"
      } catch (e) {
          console.error("Failed to stop fitting:", e);
      }
  };

  return (
    <ErrorBoundary>
    <div className="container" style={{maxWidth: '100%', padding: '20px', height: '100vh', boxSizing: 'border-box', display: 'flex', flexDirection: 'column'}}>
      <header style={{
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        padding: '0 20px', 
        height: '60px', 
        borderBottom: '1px solid var(--border-color)', 
        background: 'var(--bg-card)', 
        marginBottom: '20px',
        flexShrink: 0
      }}>
        <div style={{display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0}}>
             <img src="/logo.png" alt="Logo" style={{height: '48px', width: 'auto'}} />
             {/* App Title */}
             <div style={{fontWeight: '700', fontSize: '1.1rem', color: 'var(--text-main)', letterSpacing: '-0.02em'}}>
                TBSOC
             </div>
             {/* Version Badge */}
             <span style={{fontSize: '0.75rem', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', padding: '1px 6px', borderRadius: '4px'}}>{appVersion || 'v...'}</span>
        </div>
        
        {/* Center: Working Directory */}
        <div style={{flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minWidth: 0, padding: '0 20px'}}>
             <div style={{
                 display: 'flex', 
                 alignItems: 'center', 
                 background: 'var(--bg-secondary)', 
                 padding: '4px 4px 4px 12px', 
                 borderRadius: '8px', 
                 border: '1px solid var(--border-color)',
                 maxWidth: '100%'
             }}>
                 <span style={{
                     fontSize: '0.85rem', 
                     fontFamily: 'monospace', 
                     color: 'var(--text-secondary)', 
                     marginRight: '12px',
                     whiteSpace: 'nowrap',
                     overflow: 'hidden',
                     textOverflow: 'ellipsis',
                     maxWidth: '400px',
                     direction: 'rtl',
                     textAlign: 'left'
                  }} title={currentPath}>
                     {currentPath || "No directory selected"}
                 </span>
                 <button 
                     onClick={handleOpenFolder} 
                     style={{
                         whiteSpace: 'nowrap',
                         padding: '4px 12px',
                         fontSize: '0.8rem',
                         background: 'var(--button-bg)',
                         color: 'var(--button-text)',
                         border: '1px solid var(--border-color)',
                         borderRadius: '6px',
                         cursor: 'pointer',
                         fontWeight: 500
                     }}
                  >
                     Open Folder
                 </button>
             </div>
        </div>

        <div style={{display: 'flex', alignItems: 'center', gap: '20px', flexShrink: 0}}>
            {/* Status Indicator */}
            <div style={{display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', background: 'var(--bg-secondary)', padding: '4px 10px', borderRadius: '20px'}}>
                <span style={{
                    display: 'block', 
                    width: '8px', 
                    height: '8px', 
                    borderRadius: '50%', 
                    background: status.includes('Error') ? '#ff6b6b' : (status === 'Idle' || status === 'Fitting Completed' ? '#42d392' : '#fbbf24')
                }}></span>
                <span style={{color: 'var(--text-main)', fontWeight: 500}}>{status}</span>
            </div>
            
            {/* Divider */}
            <div style={{height: '24px', width: '1px', background: 'var(--border-color)'}}></div>
            
            {/* Theme Toggle Button */}
            <button 
                onClick={() => setCurrentTheme(currentTheme === 'Light' ? 'Dark' : 'Light')}
                title={`Switch to ${currentTheme === 'Light' ? 'Dark' : 'Light'} Mode`}
                style={{
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '20px',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    color: 'var(--text-main)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '4px 12px',
                    transition: 'all 0.2s ease',
                    fontWeight: 500
                }}
            >
                {currentTheme === 'Light' ? (
                     <>
                        <span>Theme</span>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="#4b5563" stroke="none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>
                     </>
                ) : (
                    <>
                        <span>Theme</span>
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>
                    </>
                )}
            </button>
        </div>
      </header>
      
      <div style={{display: 'flex', gap: '20px', flex: 1, minHeight: 0}}>
          <div style={{flex: '0 0 200px', minWidth: '300px'}}>
            <ParameterEditor 
                onRunFit={runFit} 
                onPreview={handlePreview} 
                onDataLoaded={handleDataLoaded}
                externalLambdas={activeLambdas} 
                isFitting={status.startsWith("Fitting") || status === "Submitting..."}
                onStopFit={handleStopFit}
                currentPath={currentPath}
            />
          </div>
          <div style={{flex: 1, minWidth: 0, height: '100%'}}>
            <VisualizationDashboard 
                lambdas={activeLambdas} 
                runTrigger={runTrigger} 
                dataVersion={dataVersion}
                fermiLevel={activeFermi} 
                weightSigma={activeSigma}
                themeConfig={themeConfig}
            />
          </div>
      </div>
    </div>
    </ErrorBoundary>
  )
}

export default App
