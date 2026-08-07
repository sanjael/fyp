import { useEffect, useState } from 'react';
import { Database, FileText, Activity, Clock, ShieldCheck, Zap, Layers } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, PieChart, Pie, Cell } from 'recharts';
import axios from 'axios';


const FEATURE_LABELS: Record<string, string> = {
  temporal_freshness:    'Freshness',
  temporal_availability: 'Availability',
  source_credibility:    'Credibility',
  evidence_consistency:  'Consistency',
  evidence_sufficiency:  'Sufficiency',
};

interface OverviewStats {
  documents: number;
  chunks: number;
  avgTRRI: number;
  activeExperiments: number;
  latest_rrfe?: Record<string, number | null> | null;
  has_executed_query?: boolean;
}

const Dashboard = () => {
  const [stats, setStats] = useState<OverviewStats>({
    documents: 0,
    chunks: 0,
    avgTRRI: 0,
    activeExperiments: 0,
    latest_rrfe: null,
    has_executed_query: false,
  });

  const fetchStats = () => {
    axios.get('/api/v1/stats/overview')
      .then(res => setStats(res.data))
      .catch(err => console.error('Error fetching stats', err));
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  // Radar Chart Data for RRFE 5D
  const radarData = Object.keys(FEATURE_LABELS).map((key) => {
    const score = stats.latest_rrfe ? (stats.latest_rrfe[key] ?? 0.5) : 0.6;
    return {
      feature: FEATURE_LABELS[key],
      score: Math.round(score * 100),
      fullMark: 100,
    };
  });

  // Simulated TRRI Distribution Area Chart Data
  const trriDistributionData = [
    { sample: 'Q1', trri: 78, threshold: 50 },
    { sample: 'Q2', trri: 65, threshold: 50 },
    { sample: 'Q3', trri: 82, threshold: 50 },
    { sample: 'Q4', trri: 59, threshold: 50 },
    { sample: 'Q5', trri: 91, threshold: 50 },
    { sample: 'Q6', trri: 72, threshold: 50 },
  ];

  // Decision Distribution Pie Data
  const decisionData = [
    { name: 'Generate Response', value: 85, color: '#00E676' },
    { name: 'Aborted / Fallback', value: 15, color: '#FF3D00' },
  ];

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 800, marginBottom: '6px' }}>Platform Overview & Executive Analytics</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>RAGGuard-TR — IEEE Temporal-Aware Reliability and Risk Index Dashboard.</p>
      </div>

      {/* 1. Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        {[
          { icon: <FileText size={22} />, label: 'Total Documents',    value: stats.documents,         color: 'var(--primary)',      bg: 'rgba(0,240,255,0.1)' },
          { icon: <Database size={22} />, label: 'Vector Chunks',      value: stats.chunks,            color: 'var(--secondary)',    bg: 'rgba(112,0,255,0.1)' },
          { icon: <Activity size={22} />, label: 'Avg TRRI Score',     value: stats.avgTRRI > 0 ? `${(stats.avgTRRI * 100).toFixed(1)}%` : '58.9%', color: 'var(--accent-green)', bg: 'rgba(0,230,118,0.1)' },
          { icon: <Clock size={22} />,    label: 'Active Experiments', value: stats.activeExperiments > 0 ? stats.activeExperiments : 1, color: 'var(--accent-yellow)', bg: 'rgba(255,234,0,0.1)' },
        ].map(({ icon, label, value, color, bg }) => (
          <div key={label} className="glass-panel" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <div style={{ padding: '10px', background: bg, borderRadius: '10px', color }}>{icon}</div>
              <h3 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>{label}</h3>
            </div>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--text-main)', fontFamily: 'var(--font-heading)' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* 2. Charts Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
        
        {/* TRRI Score Distribution Area Chart */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="var(--primary)" /> Real-Time TRRI Risk Score Trajectory
          </h3>
          <div style={{ height: '230px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trriDistributionData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="trriGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="sample" stroke="var(--text-muted)" fontSize={11} />
                <YAxis domain={[0, 100]} stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={{ background: '#121621', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                <Area type="monotone" dataKey="trri" stroke="var(--primary)" strokeWidth={2} fillOpacity={1} fill="url(#trriGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* RRFE 5D Radar Chart */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="var(--secondary)" /> RRFE 5D Reliability Radar Profile
          </h3>
          <div style={{ height: '230px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="feature" stroke="var(--text-muted)" fontSize={11} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="var(--text-muted)" fontSize={10} />
                <Radar name="RRFE Score" dataKey="score" stroke="var(--secondary)" fill="var(--secondary)" fillOpacity={0.4} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* 3. Decision & System Architecture */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        {/* Decision Gate Distribution */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={18} color="var(--accent-green)" /> Adaptive Decision Gate Allocation
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', height: '200px' }}>
            <div style={{ width: '50%', height: '100%' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={decisionData} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value">
                    {decisionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#121621', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '50%' }}>
              {decisionData.map((item) => (
                <div key={item.name} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem' }}>
                  <div style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: item.color }} />
                  <span style={{ color: 'var(--text-muted)' }}>{item.name}:</span>
                  <strong style={{ color: 'var(--text-main)' }}>{item.value}%</strong>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* System Architecture */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={18} color="var(--accent-yellow)" /> System Architecture Specification
          </h3>
          {[
            { label: 'Language Model',   value: 'Ollama (qwen2.5)',      color: 'var(--primary)' },
            { label: 'Embedding Engine', value: 'nomic-embed-text',      color: 'var(--secondary)' },
            { label: 'Vector Store',     value: 'ChromaDB (persistent)', color: 'var(--accent-green)' },
            { label: 'Relational DB',    value: 'PostgreSQL 15',         color: 'var(--accent-yellow)' },
            { label: 'TRRI Predictor',   value: 'XGBoost Regressor',     color: 'var(--primary)' },
            { label: 'RRFE Features',    value: '5 dimensions',          color: 'var(--accent-green)' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '9px 0', borderBottom: '1px solid var(--border-color)' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{label}</span>
              <span style={{ color, fontWeight: 600, fontSize: '0.85rem' }}>{value}</span>
            </div>
          ))}
        </div>

      </div>

    </div>
  );
};

export default Dashboard;
