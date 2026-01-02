import React, { useState, useEffect } from 'react';

export default function ParameterEditor({ onRunFit, onPreview, externalLambdas, isFitting, onStopFit, onDataLoaded, currentPath }) {
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
  
  const [lambdaLabels, setLambdaLabels] = useState([]);

  // Sync external lambdas (Array from Preview, Dict from Fit Result)
  useEffect(() => {
      if (!externalLambdas) return;
      
      if (Array.isArray(externalLambdas) && externalLambdas.length > 0) {
           setFormData(prev => ({ ...prev, lambdas: externalLambdas }));
      } else if (typeof externalLambdas === 'object' && lambdaLabels.length > 0) {
           // Dictionary: {'Pt:d': 0.34}
           setFormData(prev => {
              const currentVals = prev.lambdas;
              const newLambdas = lambdaLabels.map((label, i) => {
                  if (externalLambdas[label] !== undefined) {
                      return externalLambdas[label];
                  }
                  return currentVals[i] || 0.0;
              });
              return { ...prev, lambdas: newLambdas };
           });
      }
  }, [externalLambdas, lambdaLabels]);

  // Auto-preview when lambdas change (Debounced 300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
        // Only run if we have labels (data loaded)
        if (lambdaLabels.length > 0) {
             handlePreview({ preventDefault: () => {} });
        }
    }, 300); 
    return () => clearTimeout(timer);
  }, [formData.lambdas]);

  const handleLoadData = () => {
    fetch('/api/load-data', { 
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    })
    .then(res => res.json())
    .then(data => {
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
                 
                 const newFormData = {...formData, lambdas: smartDefaults};
                 
                 // Reset lambdas to smart defaults
                 setFormData(prev => ({...prev, lambdas: smartDefaults}));

                 // Propagate to parent to ensure VisualizationDashboard has correct lambdas
                 if (onPreview) {
                     onPreview(newFormData);
                 }
            }
        }
        
        if (data.status === 'loaded' && onDataLoaded) {
             onDataLoaded();
        }
    })
    .catch(console.error);
  };

  // Reload data when currentPath changes (prop from parent)
  useEffect(() => {
      if (currentPath) {
          handleLoadData();
      }
  }, [currentPath]);

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
        <div style={{flex: 1}}>
            <h3 style={{fontSize: '1rem', marginTop: 0, marginBottom: '10px', color: 'var(--text-secondary)'}}>Fitting Weights</h3>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px'}}>
            <label>
                <span style={{fontSize: '0.85rem', display: 'block', marginBottom: '4px'}}>E_Fermi (eV)</span>
                    <input type="number" step="0.01" name="Efermi" value={formData.Efermi} onChange={handleChange} />
            </label>
            <label>
                    <span style={{fontSize: '0.85rem', display: 'block', marginBottom: '4px'}}>Weight σ (eV)</span>
                    <input type="number" step="0.1" name="weight_sigma" value={formData.weight_sigma} onChange={handleChange} />
            </label>
            </div>

            <div style={{marginTop: '20px'}}>
                 <h3 style={{fontSize: '1rem', marginTop: 0, marginBottom: '10px', color: 'var(--text-secondary)'}}>Lambdas</h3>
                
                <div style={{display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '15px'}}>
                {formData.lambdas.map((val, idx) => {
                    const label = lambdaLabels[idx] || `λ${idx}`;
                    // Hide 's' orbitals (SOC is effectively zero)
                    const isS = label.toLowerCase().endsWith(':s') || label.toLowerCase() === 's';
                    if (isS) return null;

                    return (
                        <div key={idx} style={{background: 'var(--bg-item)', padding: '8px 12px', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                             <label style={{fontSize: '0.9rem', fontWeight: '500', color: 'var(--text-main)', marginRight: '10px', minWidth: '60px'}}>
                                 {label}
                             </label>
                             
                             <div style={{display: 'flex', alignItems: 'center', gap: '8px', flex: 1}}>
                                <input
                                    type="number"
                                    min="0.0"
                                    step="0.001" 
                                    value={val}
                                    onChange={(e) => handleLambdaChange(idx, e.target.value)}
                                    style={{flex: 1, padding: '6px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--input-bg-subtle)', color: 'var(--text-main)'}}
                                />

                             </div>
                        </div>
                    );
                })}
                </div>

            </div>
        </div>

        <div style={{display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '30px'}}>
             <div style={{display: 'flex', gap: '10px'}}>
                 <button type="button" onClick={handlePreview} style={{flex: 1, background: 'var(--button-bg)', color: 'var(--button-text)', border: '1px solid var(--border-color)', padding: '10px', borderRadius: '6px', cursor: 'pointer'}}>Preview</button>
                 {isFitting ? (
                     <button type="button" onClick={onStopFit} style={{flex: 1, background: '#ff6b6b', color: 'white', fontWeight: 'bold', border: 'none', padding: '10px', borderRadius: '6px', cursor: 'pointer'}}>Stop</button>
                 ) : (
                     <button type="button" onClick={handleSubmit} style={{flex: 1, background: 'linear-gradient(45deg, #646cff, #42d392)', color: 'white', fontWeight: 'bold', border: 'none', padding: '10px', borderRadius: '6px', cursor: 'pointer'}}>Fitting</button>
                 )}
             </div>
             <button type="button" onClick={handleSaveHR} style={{width: '100%', background: 'var(--button-bg)', color: 'var(--button-text)', border: '1px solid var(--border-color)', padding: '10px', borderRadius: '6px', cursor: 'pointer'}}>Export HR</button>
        </div>
    </form>
  );
}
