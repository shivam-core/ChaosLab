import React, { useEffect, useState } from 'react';
import { initializeWorkspace, uploadDataset, listDatasets, createScenario, startRun, getRun } from './api';
import { UploadCloud, Play, FileText, CheckCircle, Clock } from 'lucide-react';


function App() {
  const [loading, setLoading] = useState(true);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  
  // Dashboard state
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [scenarioConfig, setScenarioConfig] = useState({
    supplier_reliability: 0.95,
    lead_time_days: 7,
    demand_volatility: 0.1,
    starting_inventory: 1000
  });
  
  const [running, setRunning] = useState(false);
  const [, setActiveRunId] = useState<string | null>(null);
  const [runData, setRunData] = useState<any>(null);

  useEffect(() => {
    init();
  }, []);

  const init = async () => {
    try {
      if (!localStorage.getItem('workspace_token')) {
        await initializeWorkspace();
      }
      await refreshDatasets();
    } catch (e) {
      console.error(e);
      // Reset token if invalid
      localStorage.removeItem('workspace_token');
      await initializeWorkspace();
      await refreshDatasets();
    }
    setLoading(false);
  };

  const refreshDatasets = async () => {
    const ds = await listDatasets();
    setDatasets(ds);
    if (ds.length > 0 && !activeDatasetId) {
      setActiveDatasetId(ds[0].id);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    try {
      await uploadDataset(e.target.files[0]);
      // Poll for processing completion
      let retries = 10;
      while (retries > 0) {
        await new Promise(r => setTimeout(r, 2000));
        const ds = await listDatasets();
        if (ds.length > 0) {
          setDatasets(ds);
          setActiveDatasetId(ds[0].id);
          break;
        }
        retries--;
      }
    } catch (e) {
      console.error(e);
      alert("Failed to upload");
    }
    setUploading(false);
  };

  const handleRunSimulation = async () => {
    if (!activeDatasetId) return;
    setRunning(true);
    try {
      const scenario = await createScenario(activeDatasetId, "New Scenario", scenarioConfig);
      const run = await startRun(scenario.id);
      setActiveRunId(run.id);
      
      // Poll for run completion
      const poll = setInterval(async () => {
        const runStatus = await getRun(run.id);
        setRunData(runStatus);
        if (runStatus.status === 'succeeded' || runStatus.status === 'failed') {
          clearInterval(poll);
          setRunning(false);
        }
      }, 2000);
      
    } catch(e) {
      console.error(e);
      setRunning(false);
    }
  };

  if (loading) {
    return <div className="flex h-screen items-center justify-center text-textMuted font-sans">Initializing ChaosLab...</div>;
  }

  return (
    <div className="min-h-screen bg-background text-textMain font-sans flex flex-col">
      <header className="bg-surface shadow-sm py-4 px-8 flex justify-between items-center border-b border-secondary">
        <div>
          <h1 className="text-2xl font-serif font-bold text-primary">ChaosLab Retail</h1>
          <p className="text-sm text-textMuted">Supply Chain Stress Testing</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs bg-secondary px-3 py-1 rounded-full text-textMuted font-medium">
            Workspace Active
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto p-8 flex flex-col gap-8">
        
        {datasets.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-secondary rounded-xl bg-surface p-12">
            <UploadCloud className="w-16 h-16 text-primary mb-6" />
            <h2 className="text-xl font-bold mb-2">Upload Historical Data</h2>
            <p className="text-textMuted mb-8 text-center max-w-md">
              Upload your historical sales and transaction data (CSV or XLSX) to begin testing resilience against supply chain disruptions.
            </p>
            <label className={`cursor-pointer bg-primary text-white px-6 py-3 rounded font-medium hover:bg-opacity-90 transition-all ${uploading ? 'opacity-50' : ''}`}>
              {uploading ? 'Processing...' : 'Select File'}
              <input type="file" className="hidden" accept=".csv,.xlsx" onChange={handleFileUpload} disabled={uploading} />
            </label>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Sidebar Configuration */}
            <div className="lg:col-span-1 flex flex-col gap-6">
              <div className="bg-surface rounded-xl p-6 shadow-sm border border-secondary">
                <h3 className="font-bold text-lg mb-4 font-serif">Scenario Parameters</h3>
                
                <div className="flex flex-col gap-4">
                  <div>
                    <label className="text-sm font-medium text-textMuted mb-1 block">Supplier Reliability (0 - 1)</label>
                    <input 
                      type="range" min="0" max="1" step="0.01"
                      className="w-full accent-primary"
                      value={scenarioConfig.supplier_reliability}
                      onChange={(e) => setScenarioConfig({...scenarioConfig, supplier_reliability: parseFloat(e.target.value)})}
                    />
                    <div className="text-right text-xs mt-1">{scenarioConfig.supplier_reliability.toFixed(2)}</div>
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-textMuted mb-1 block">Lead Time (Days)</label>
                    <input 
                      type="number" min="1" max="30"
                      className="w-full bg-background border border-secondary rounded px-3 py-2"
                      value={scenarioConfig.lead_time_days}
                      onChange={(e) => setScenarioConfig({...scenarioConfig, lead_time_days: parseInt(e.target.value)})}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-textMuted mb-1 block">Demand Volatility (0 - 1)</label>
                    <input 
                      type="range" min="0" max="1" step="0.01"
                      className="w-full accent-primary"
                      value={scenarioConfig.demand_volatility}
                      onChange={(e) => setScenarioConfig({...scenarioConfig, demand_volatility: parseFloat(e.target.value)})}
                    />
                    <div className="text-right text-xs mt-1">{scenarioConfig.demand_volatility.toFixed(2)}</div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-textMuted mb-1 block">Starting Inventory</label>
                    <input 
                      type="number" min="0" step="100"
                      className="w-full bg-background border border-secondary rounded px-3 py-2"
                      value={scenarioConfig.starting_inventory}
                      onChange={(e) => setScenarioConfig({...scenarioConfig, starting_inventory: parseInt(e.target.value)})}
                    />
                  </div>

                  <button 
                    className={`mt-4 w-full flex items-center justify-center gap-2 bg-primary text-white py-3 rounded font-medium hover:bg-opacity-90 ${running ? 'opacity-50' : ''}`}
                    onClick={handleRunSimulation}
                    disabled={running}
                  >
                    {running ? <Clock className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                    {running ? 'Running Simulation...' : 'Run Simulation'}
                  </button>

                </div>
              </div>
            </div>

            {/* Results Area */}
            <div className="lg:col-span-2 flex flex-col gap-6">
              {!runData ? (
                <div className="flex-1 bg-surface rounded-xl border border-secondary flex flex-col items-center justify-center p-12 text-center text-textMuted">
                  <CheckCircle className="w-12 h-12 text-success mb-4 opacity-50" />
                  <p>Dataset ready. Configure scenario parameters and run the simulation to see results.</p>
                </div>
              ) : (
                <>
                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-surface rounded-xl p-4 border border-secondary">
                      <div className="text-xs text-textMuted mb-1">Fill Rate</div>
                      <div className="text-2xl font-bold text-primary">
                        {runData.summary?.fill_rate ? (runData.summary.fill_rate * 100).toFixed(1) : '0'}%
                      </div>
                    </div>
                    <div className="bg-surface rounded-xl p-4 border border-secondary">
                      <div className="text-xs text-textMuted mb-1">Stockout Days</div>
                      <div className="text-2xl font-bold text-error">
                        {runData.summary?.stockout_days || 0}
                      </div>
                    </div>
                    <div className="bg-surface rounded-xl p-4 border border-secondary">
                      <div className="text-xs text-textMuted mb-1">Revenue</div>
                      <div className="text-2xl font-bold">
                        ${runData.summary?.total_revenue?.toLocaleString() || 0}
                      </div>
                    </div>
                    <div className="bg-surface rounded-xl p-4 border border-secondary">
                      <div className="text-xs text-textMuted mb-1">Net Profit</div>
                      <div className="text-2xl font-bold text-success">
                        ${runData.summary?.net_profit?.toLocaleString() || 0}
                      </div>
                    </div>
                  </div>

                  {/* Empty state for charts until we return detailed time-series from backend */}
                  <div className="bg-surface rounded-xl p-6 border border-secondary min-h-[300px] flex items-center justify-center">
                    <div className="text-center">
                      <FileText className="w-12 h-12 text-primary mx-auto mb-4 opacity-75" />
                      <h4 className="font-bold mb-2">Simulation Succeeded</h4>
                      <p className="text-sm text-textMuted mb-4">The detailed timeline and charts would be rendered here.</p>
                      <button className="text-primary font-medium text-sm hover:underline flex items-center gap-2 mx-auto">
                        <FileText className="w-4 h-4" /> Download PDF Report
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>

          </div>
        )}
      </main>
    </div>
  );
}

export default App;
