import React, { useState, useEffect } from 'react';

export default function ParameterEditor({ onRunFit, onPreview, externalLambdas, isFitting, onStopFit, onDataLoaded }) {
  const [formData, setFormData] = useState({
    posfile: 'POSCAR',
    winfile: 'wannier90.win',
    hrfile: 'wannier90_hr.dat',
    kpfile: 'KPOINTS',
    eigfile: 'EIGENVAL',
    Efermi: 0.0,
    weight_sigma: 2.0,
    lambdas: [0.0, 0.0], 
  });
  
  const [liveUpdate, setLiveUpdate] = useState(true);

  useEffect(() => {
      if (externalLambdas && externalLambdas.length > 0) {
          setFormData(prev => ({ ...prev, lambdas: externalLambdas }));
      }
  }, [externalLambdas]);
  
  const [files, setFiles] = useState([]);
  const [currentPath, setCurrentPath] = useState('');
  const [lambdaLabels, setLambdaLabels] = useState([]);

  // Live Tuning Effect: Auto-update preview when lambdas change
  useEffect(() => {
    const timer = setTimeout(() => {
        // Only auto-preview if we have valid data loaded AND live update is enabled
        if (lambdaLabels.length > 0 && liveUpdate) {
            // Check if we actually have data to preview
            // (Avoiding infinite loops or premature calls)
             handlePreview({ preventDefault: () => {} });
        }
    }, 150); // Debounce 150ms for smooth slider dragging
    return () => clearTimeout(timer);
  }, [formData.lambdas, liveUpdate]);

  const refreshFiles = () => {
      fetch('/api/files')
        .then(res => res.json())
        .then(data => {
            console.log("Files loaded:", data);
            setFiles(data);
        })
        .catch(err => console.error("Failed to load files:", err));
  };

  useEffect(() => {
    console.log("ParameterEditor Mounted");
    // Fetch current directory
    fetch('/api/current-directory')
        .then(res => res.json())
        .then(data => setCurrentPath(data.path))
        .catch(console.error);
  }, []);

  // Reload data when currentPath changes (initially established or changed by user)
  useEffect(() => {
      if (currentPath) {
          refreshFiles();
          handleLoadData();
      }
  }, [currentPath]);

  const handleLoadData = () => {
    fetch('/api/load-data', { 
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'loaded' && onDataLoaded) {
             onDataLoaded();
        }
        
        if (data.orb_labels && data.orb_labels.length > 0) {
            // Check if labels changed, indicating a new system or file load
            const labelsChanged = JSON.stringify(data.orb_labels) !== JSON.stringify(lambdaLabels);
            
            if (labelsChanged) {
                 setLambdaLabels(data.orb_labels);
                 // Generate smart defaults: 0.0 for s-orbital, 0.2 for others (p, d, f)
                 const smartDefaults = data.orb_labels.map(label => {
                     // Check for 's' orbital (e.g. "Ga:s" or just "s")
                     // Be robust: looks for ":s" at end or exact match "s"
                     const isS = label.trim().endsWith(':s') || label.trim() === 's';
                     return isS ? 0.0 : 0.2;
                 });
                 
                 // Reset lambdas to smart defaults
                 setFormData(prev => ({...prev, lambdas: smartDefaults}));
            }
        }
    })
    .catch(console.error);
  };

  const handleOpenFolder = async () => {
      try {
          const res = await fetch('/api/choose-directory', { method: 'POST' });
          const data = await res.json();
          if (data.path) {
              setCurrentPath(data.path);
              refreshFiles(); // Reload files from new directory
              handleLoadData(); // Reload initial parameters for the new directory
          }
      } catch (err) {
          console.error("Failed to open folder:", err);
      }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    // console.log("Change:", name, value);
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLambdaChange = (index, val) => {
    const newLambdas = [...formData.lambdas];
    newLambdas[index] = parseFloat(val);
    setFormData(prev => ({ ...prev, lambdas: newLambdas }));
  };

  const addLambda = () => {
    const newLambdaLabels = [...lambdaLabels, `λ${lambdaLabels.length}`];
    setLambdaLabels(newLambdaLabels);
    setFormData(prev => ({ ...prev, lambdas: [...prev.lambdas, 0.0] }));
  };

  const removeLambda = (index) => {
    const newLambdas = formData.lambdas.filter((_, i) => i !== index);
    setFormData(prev => ({ ...prev, lambdas: newLambdas }));
  };

  const handlePreview = (e) => {
      e.preventDefault();
      // First load data to cache
      fetch('/api/load-data', {
          method: 'POST', 
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(formData)
      })
      .then(res => {
          if(res.ok) {
              onPreview(formData);
          } else {
              alert("Failed to load data for preview");
          }
      })
      .catch(console.error);
  }

  const handleSaveHR = () => {
      fetch('/api/save-hr', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(formData)
      })
      .then(res => res.json())
      .then(data => {
          if (data.path) {
              alert(`Saved to: ${data.path}`);
          } else {
              // Usually error handled in catch or by check
              if (data.detail) alert("Failed: " + data.detail);
          }
      })
      .catch(err => alert("Error: " + err));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onRunFit(formData);
  };

  return (
    <form className="card" style={{height: '100%', overflowY: 'auto', display: 'flex', flexDirection: 'column', margin: 0}}>
        <h2 style={{marginTop: 0}}>Configuration</h2>

        {/* Project Folder Selection */}
        <div style={{marginBottom: '20px', padding: '10px', background: 'var(--bg-secondary)', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
            <div style={{overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis', marginRight: '10px', flex: 1}}>
                <span style={{fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block'}}>Working Directory</span>
                <span style={{fontFamily: 'monospace', fontSize: '0.9rem'}} title={currentPath}>{currentPath || "Loading..."}</span>
            </div>
            <button type="button" onClick={handleOpenFolder} style={{flexShrink: 0, padding: '6px 12px', fontSize: '0.85rem', background: 'var(--button-bg)', color: 'var(--button-text)', border: '1px solid var(--border-color)', borderRadius: '4px', cursor: 'pointer'}}>Open Folder</button>
        </div>
        
        <div style={{flex: 1}}>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px'}}>
                <div style={{gridColumn: '1 / -1'}}>
                <h3 style={{fontSize: '1rem', marginTop: '10px', marginBottom: '5px', color: 'var(--text-secondary)'}}>Input Files</h3>
                </div>
                
                <label style={{display: 'block'}}>
                    <span style={{fontSize: '0.85rem', display: 'block', marginBottom: '4px'}}>Wannier90 Win</span>
                    <input name="winfile" value={formData.winfile} onChange={handleChange} list="files-list"/>
                </label>
                <label style={{display: 'block'}}>
                    <span style={{fontSize: '0.85rem', display: 'block', marginBottom: '4px'}}>Wannier90 HR</span>
                    <input name="hrfile" value={formData.hrfile} onChange={handleChange} list="files-list"/>
                </label>

                <datalist id="files-list">
                    {files.map(f => <option key={f.path} value={f.name} />)}
                </datalist>
            </div>
            
            <div style={{marginTop: '20px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px'}}>
            <div style={{gridColumn: '1 / -1'}}>
                <h3 style={{fontSize: '1rem', marginTop: '0', marginBottom: '5px', color: 'var(--text-secondary)'}}>Parameters</h3>
                </div>
            <label>
                <span style={{fontSize: '0.85rem', display: 'block', marginBottom: '4px'}}>Fermi Energy (eV)</span>
                    <input type="number" step="0.01" name="Efermi" value={formData.Efermi} onChange={handleChange} />
            </label>
            <label>
                    <span style={{fontSize: '0.85rem', display: 'block', marginBottom: '4px'}}>Weight Sigma (eV)</span>
                    <input type="number" step="0.1" name="weight_sigma" value={formData.weight_sigma} onChange={handleChange} />
            </label>
            </div>

            <div style={{marginTop: '20px'}}>
                <h3 style={{fontSize: '1rem', marginTop: '0', marginBottom: '10px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                    <span>
                        Lambdas (Live Tuning)
                        <span style={{fontSize: '0.7em', color: 'var(--text-secondary)', marginLeft: '10px'}}>Drag sliders to update plot</span>
                    </span>
                    <label style={{display: 'flex', alignItems: 'center', cursor: 'pointer', fontSize: '0.8em', color: 'var(--text-main)'}}>
                        <input
                            type="checkbox"
                            checked={liveUpdate}
                            onChange={(e) => setLiveUpdate(e.target.checked)}
                            style={{marginRight: '5px', accentColor: '#42d392'}}
                        />
                        Live Update
                    </label>
                </h3>
                <div style={{display: 'flex', flexDirection: 'column', gap: '15px', marginBottom: '15px'}}>
                {formData.lambdas.map((val, idx) => {
                    const label = lambdaLabels[idx] || `λ${idx}`;
                    // Hide 's' orbitals (SOC is effectively zero)
                    const isS = label.toLowerCase().endsWith(':s') || label.toLowerCase() === 's';
                    if (isS) return null;

                    return (
                        <div key={idx} style={{background: 'var(--bg-item)', padding: '10px', borderRadius: '6px'}}>
                            <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '5px'}}>
                                <label style={{fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--text-main)'}}>
                                    {label}
                                </label>
                                <span style={{fontSize: '0.85rem', fontFamily: 'monospace', color: '#42d392'}}>
                                    {(typeof val === 'number') ? val.toFixed(3) : '0.000'}
                                </span>
                            </div>
                            
                            <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                                {/* Slider for Live Tuning: Range 0 to 2 */}
                                <input
                                    type="range"
                                    min="0.0"
                                    max="2.0"
                                    step="0.01"
                                    value={val}
                                    onChange={(e) => handleLambdaChange(idx, e.target.value)}
                                    style={{flex: 1, cursor: 'pointer', accentColor: '#42d392'}}
                                />
                                
                                {/* Number Input for Precision */}
                                <input
                                    type="number"
                                    min="0.0"
                                    step="0.01"
                                    value={val}
                                    onChange={(e) => handleLambdaChange(idx, e.target.value)}
                                    style={{width: '70px', padding: '4px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--input-bg-subtle)', color: 'var(--text-main)'}}
                                />
                                
                                <button type="button" onClick={() => removeLambda(idx)} style={{background: 'none', color: 'var(--text-muted)', fontSize: '1.2em', border: 'none', cursor: 'pointer'}} title="Remove">×</button>
                            </div>
                        </div>
                    );
                })}
                </div>
                <button type="button" onClick={addLambda} style={{width: '100%', marginTop: '5px', padding: '8px', background: 'var(--button-bg)', border: '1px dashed var(--border-color)', color: 'var(--text-muted)', borderRadius: '4px'}}>+ Add Optimization Parameter</button>
            </div>
        </div>

        <div style={{display: 'flex', gap: '10px', marginTop: '30px'}}>
             <button type="button" onClick={handlePreview} style={{flex: 1, background: 'var(--button-bg)', color: 'var(--button-text)', border: '1px solid var(--border-color)'}}>Preview Bands</button>
             <button type="button" onClick={handleSaveHR} style={{flex: 1, background: 'var(--button-bg)', color: 'var(--button-text)', border: '1px solid var(--border-color)'}}>Export HR</button>
             {isFitting ? (
                 <button type="button" onClick={onStopFit} style={{flex: 1, background: '#ff6b6b', fontWeight: 'bold'}}>Stop Fitting</button>
             ) : (
                 <button type="button" onClick={handleSubmit} style={{flex: 1, background: 'linear-gradient(45deg, #646cff, #42d392)', fontWeight: 'bold'}}>Start Fitting</button>
             )}
        </div>
    </form>
  );
}
