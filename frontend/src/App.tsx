import React, { useEffect, useState } from 'react';
import { initializeWorkspace, uploadDataset, listDatasets, createScenario, startRun, getRun, downloadReport } from './api';
import { UploadCloud, Play, FileText, Activity, AlertTriangle, Package, DollarSign, Target, ServerCrash, CheckCircle } from 'lucide-react';
import { XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

function App() {
  const [loading, setLoading] = useState(true);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [scenarioConfig, setScenarioConfig] = useState({
    supplier_reliability: 0.95,
    lead_time_days: 7,
    demand_volatility: 0.1,
    starting_inventory: 1000,
    price_elasticity: 0.5,
    marketing_spend: 5000,
  });
  
  const [running, setRunning] = useState(false);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [runData, setRunData] = useState<any>(null);
  
  // Animation state
  const [currentDay, setCurrentDay] = useState(0);
  const [chartData, setChartData] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [liveMetrics, setLiveMetrics] = useState({ revenue: 0, backlog: 0, fillRate: 100, stockouts: 0 });

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
      localStorage.removeItem('workspace_token');
      await initializeWorkspace();
      await refreshDatasets();
    }
    setLoading(false);
  };

  const refreshDatasets = async () => {
    const ds = await listDatasets();
    setDatasets(ds);
    if (ds.length > 0 && !activeDatasetId) setActiveDatasetId(ds[0].id);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    try {
      await uploadDataset(e.target.files[0]);
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
    setRunData(null);
    setCurrentDay(0);
    setChartData([]);
    setEvents([]);
    
    try {
      const scenario = await createScenario(activeDatasetId, "New Scenario", scenarioConfig);
      const run = await startRun(scenario.id);
      setActiveRunId(run.id);
      
      const poll = setInterval(async () => {
        const runStatus = await getRun(run.id);
        if (runStatus.status === 'succeeded' || runStatus.status === 'failed') {
          clearInterval(poll);
          setRunning(false);
          setRunData(runStatus);
          
          if (runStatus.status === 'succeeded' && runStatus.results?.snapshots) {
            animateSimulation(runStatus.results.snapshots);
          }
        }
      }, 2000);
      
    } catch(e) {
      console.error(e);
      setRunning(false);
    }
  };

  const animateSimulation = (snapshots: any[]) => {
    let day = 0;
    const interval = setInterval(() => {
      if (day >= snapshots.length) {
        clearInterval(interval);
        return;
      }
      
      const snap = snapshots[day];
      const totalInv = Object.values(snap.inventory).reduce((a: any, b: any) => a + b, 0) as number;
      
      setChartData(prev => [...prev, {
        day: snap.day,
        inventory: totalInv,
        backlog: snap.backlog_units,
        shipped: snap.shipped_units_today
      }]);
      
      if (snap.stock_blocked_products.length > 0) {
        setEvents(prev => [{
          day: snap.day, 
          type: 'error', 
          message: `Stockout on ${snap.stock_blocked_products.length} products`
        }, ...prev].slice(0, 10));
      } else if (snap.shipped_units_today > 0) {
        setEvents(prev => [{
          day: snap.day, 
          type: 'success', 
          message: `Shipped ${snap.shipped_units_today} units successfully`
        }, ...prev].slice(0, 10));
      }

      setLiveMetrics(prev => ({
        revenue: prev.revenue + (snap.shipped_units_today * 50),
        backlog: snap.backlog_units,
        fillRate: snap.backlog_units === 0 ? 100 : Math.max(0, 100 - (snap.backlog_units / 100)),
        stockouts: prev.stockouts + (snap.stock_blocked_products.length > 0 ? 1 : 0)
      }));

      setCurrentDay(snap.day);
      day++;
    }, 150); // 150ms per day
  };

  if (loading) return <div className="flex h-screen items-center justify-center text-textMuted">Initializing ChaosLab...</div>;

  return (
    <div className="flex h-screen bg-background text-textMain font-sans overflow-hidden">
      
      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-secondary flex flex-col">
        <div className="p-6 border-b border-secondary">
          <h1 className="text-xl font-serif font-bold text-textMain">ChaosLab Retail</h1>
          <p className="text-xs text-textMuted mt-1 tracking-wide uppercase font-semibold">Simulation Engine v2.0</p>
        </div>
        
        <div className="p-6 flex-1 overflow-y-auto">
          <h2 className="text-xs font-bold text-textMuted uppercase tracking-wider mb-4">Input Data</h2>
          
          {!datasets.length ? (
            <label className={`flex flex-col items-center justify-center p-6 border-2 border-dashed border-secondary rounded-lg cursor-pointer hover:bg-secondary transition-colors ${uploading ? 'opacity-50' : ''}`}>
              <UploadCloud className="w-8 h-8 text-textMuted mb-2" />
              <span className="text-sm font-medium text-textMain">{uploading ? 'Uploading...' : 'Upload CSV / XLSX'}</span>
              <input type="file" className="hidden" accept=".csv,.xlsx" onChange={handleFileUpload} disabled={uploading} />
            </label>
          ) : (
            <div className="space-y-4">
              <div className="bg-[#EFF6FF] text-[#1E40AF] p-3 rounded-lg border border-[#BFDBFE] flex items-center gap-3">
                <FileText className="w-5 h-5 flex-shrink-0" />
                <div className="text-sm font-medium truncate" title={datasets[0].name}>{datasets[0].name}</div>
              </div>
              <label className={`text-xs font-medium text-primary hover:underline cursor-pointer flex items-center gap-1 ${uploading ? 'opacity-50' : ''}`}>
                <UploadCloud className="w-3 h-3" /> {uploading ? 'Replacing...' : 'Replace Dataset'}
                <input type="file" className="hidden" accept=".csv,.xlsx" onChange={handleFileUpload} disabled={uploading} />
              </label>
            </div>
          )}

          <div className="mt-8">
            <h2 className="text-xs font-bold text-textMuted uppercase tracking-wider mb-4">Scenario Parameters</h2>
            <div className="space-y-5">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <label className="font-medium text-textMain">Supplier Reliability</label>
                  <span className="text-textMuted">{(scenarioConfig.supplier_reliability * 100).toFixed(0)}%</span>
                </div>
                <input type="range" min="0" max="1" step="0.01" className="w-full accent-primary"
                  value={scenarioConfig.supplier_reliability}
                  onChange={e => setScenarioConfig({...scenarioConfig, supplier_reliability: parseFloat(e.target.value)})} />
              </div>
              
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <label className="font-medium text-textMain">Demand Volatility</label>
                  <span className="text-textMuted">{(scenarioConfig.demand_volatility * 100).toFixed(0)}%</span>
                </div>
                <input type="range" min="0" max="1" step="0.01" className="w-full accent-primary"
                  value={scenarioConfig.demand_volatility}
                  onChange={e => setScenarioConfig({...scenarioConfig, demand_volatility: parseFloat(e.target.value)})} />
              </div>

              <div>
                <label className="font-medium text-xs text-textMain mb-1 block">Lead Time (Days)</label>
                <input type="number" min="1" max="30" className="w-full text-sm bg-surface border border-secondary rounded px-3 py-2 outline-none focus:border-[#2563EB]"
                  value={scenarioConfig.lead_time_days}
                  onChange={e => setScenarioConfig({...scenarioConfig, lead_time_days: parseInt(e.target.value)})} />
              </div>

              <div>
                <label className="font-medium text-xs text-textMain mb-1 block">Starting Inventory</label>
                <input type="number" min="0" step="100" className="w-full text-sm bg-surface border border-secondary rounded px-3 py-2 outline-none focus:border-[#2563EB]"
                  value={scenarioConfig.starting_inventory}
                  onChange={e => setScenarioConfig({...scenarioConfig, starting_inventory: parseInt(e.target.value)})} />
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-secondary">
          <button 
            className={`w-full flex items-center justify-center gap-2 bg-primary text-white py-3 rounded-lg font-medium text-sm hover:bg-opacity-90 transition-colors shadow-sm ${(!activeDatasetId || running) ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={handleRunSimulation}
            disabled={!activeDatasetId || running}
          >
            {running ? <Activity className="w-4 h-4 animate-pulse" /> : <Play className="w-4 h-4" />}
            {running ? 'Simulating...' : 'Run Simulation'}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-background">
        {/* Header */}
        <header className="bg-surface border-b border-secondary px-8 py-5 flex justify-between items-center sticky top-0 z-10">
          <div>
            <h2 className="text-2xl font-serif text-textMain">Retail Supply Chain Dashboard</h2>
            <p className="text-sm text-textMuted mt-1">Live simulation telemetry and post-run PDF reports</p>
          </div>
          {runData?.status === 'succeeded' && (
            <button 
              className="flex items-center gap-2 bg-surface border border-secondary text-textMain px-4 py-2 rounded-lg font-medium text-sm hover:bg-surface shadow-sm transition-colors"
              onClick={() => activeRunId && downloadReport(activeRunId)}
            >
              <FileText className="w-4 h-4 text-primary" /> Export PDF Report
            </button>
          )}
        </header>

        <div className="p-8 max-w-7xl mx-auto space-y-6">
          {(!runData && !running) ? (
            <div className="flex flex-col items-center justify-center py-20 text-textMuted">
              <Target className="w-16 h-16 mb-4 text-[#D1D5DB]" />
              <h3 className="text-xl font-medium text-textMain">Ready to simulate</h3>
              <p className="max-w-md text-center mt-2">Adjust your scenario parameters on the left and click "Run Simulation" to see live supply chain telemetry.</p>
            </div>
          ) : (
            <>
              {/* Metrics Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard icon={<DollarSign/>} title="Estimated Revenue" value={`$${liveMetrics.revenue.toLocaleString()}`} color="text-[#059669]" bg="bg-[#ECFDF5]" />
                <MetricCard icon={<Package/>} title="Active Backlog" value={liveMetrics.backlog.toLocaleString()} color="text-[#D97706]" bg="bg-[#FFFBEB]" />
                <MetricCard icon={<Activity/>} title="Avg Fill Rate" value={`${liveMetrics.fillRate.toFixed(1)}%`} color="text-primary" bg="bg-[#EFF6FF]" />
                <MetricCard icon={<ServerCrash/>} title="Stockout Days" value={liveMetrics.stockouts.toString()} color="text-[#DC2626]" bg="bg-[#FEF2F2]" />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Chart */}
                <div className="lg:col-span-2 bg-surface rounded-xl shadow-sm border border-secondary overflow-hidden">
                  <div className="px-6 py-4 border-b border-secondary flex justify-between items-center bg-surface">
                    <h3 className="font-semibold text-textMain">Inventory vs Backlog</h3>
                    <div className="text-xs font-bold text-textMuted bg-surface px-2 py-1 rounded border border-secondary">
                      Day {currentDay}
                    </div>
                  </div>
                  <div className="p-6 h-[400px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorInv" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#C15C3D" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#C15C3D" stopOpacity={0}/>
                          </linearGradient>
                          <linearGradient id="colorBacklog" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#B23A48" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#B23A48" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <XAxis dataKey="day" stroke="#9CA3AF" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#9CA3AF" fontSize={12} tickLine={false} axisLine={false} />
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                        <RechartsTooltip 
                          contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        />
                        <Area type="monotone" dataKey="inventory" name="Total Inventory" stroke="#C15C3D" strokeWidth={2} fillOpacity={1} fill="url(#colorInv)" isAnimationActive={false} />
                        <Area type="monotone" dataKey="backlog" name="Backlog Units" stroke="#B23A48" strokeWidth={2} fillOpacity={1} fill="url(#colorBacklog)" isAnimationActive={false} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Event Timeline */}
                <div className="bg-surface rounded-xl shadow-sm border border-secondary overflow-hidden flex flex-col h-[465px]">
                  <div className="px-6 py-4 border-b border-secondary bg-surface">
                    <h3 className="font-semibold text-textMain">Event Timeline</h3>
                  </div>
                  <div className="flex-1 p-0 overflow-y-auto">
                    {events.length === 0 ? (
                      <div className="h-full flex items-center justify-center text-sm text-textMuted">Waiting for events...</div>
                    ) : (
                      <ul className="divide-y divide-[#F3F4F6]">
                        {events.map((ev, idx) => (
                          <li key={idx} className="p-4 flex gap-4 hover:bg-surface transition-colors">
                            <div className="mt-1">
                              {ev.type === 'error' ? 
                                <AlertTriangle className="w-5 h-5 text-[#DC2626]" /> : 
                                <CheckCircle className="w-5 h-5 text-[#059669]" />
                              }
                            </div>
                            <div>
                              <div className="text-xs font-bold text-textMuted uppercase tracking-wider mb-0.5">Day {ev.day}</div>
                              <div className="text-sm text-textMain">{ev.message}</div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function MetricCard({ icon, title, value, color, bg }: { icon: React.ReactNode, title: string, value: string, color: string, bg: string }) {
  return (
    <div className="bg-surface p-5 rounded-xl border border-secondary shadow-sm flex items-center gap-4">
      <div className={`p-3 rounded-lg ${bg} ${color} [&>svg]:w-6 [&>svg]:h-6`}>
        {icon}
      </div>
      <div>
        <div className="text-xs font-medium text-textMuted uppercase tracking-wider">{title}</div>
        <div className="text-2xl font-bold text-textMain mt-0.5">{value}</div>
      </div>
    </div>
  );
}

export default App;
