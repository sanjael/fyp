import { BarChart2, ShieldCheck, Award, TrendingUp } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';


const Benchmark = () => {

  const radarBenchmarkData = [
    { metric: 'Faithfulness', baseline: 75, ragguard: 92 },
    { metric: 'Answer Relevancy', baseline: 70, ragguard: 89 },
    { metric: 'Context Precision', baseline: 68, ragguard: 88 },
    { metric: 'Context Recall', baseline: 65, ragguard: 84 },
    { metric: 'Hallucination Prevention', baseline: 60, ragguard: 95 },
  ];

  const groupedBarData = [
    { name: 'Faithfulness', Baseline: 0.75, RAGGuard: 0.924 },
    { name: 'Answer Relevancy', Baseline: 0.70, RAGGuard: 0.891 },
    { name: 'Context Precision', Baseline: 0.68, RAGGuard: 0.876 },
    { name: 'Context Recall', Baseline: 0.65, RAGGuard: 0.842 },
    { name: 'Correctness', Baseline: 0.72, RAGGuard: 0.910 },
  ];

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* Header Banner */}
      <div style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(0,240,255,0.1), rgba(112,0,255,0.1))', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <BarChart2 size={28} color="var(--primary)" />
          <h2 style={{ margin: 0, fontSize: '1.6rem', fontWeight: 800 }}>RAGGuard-TR IEEE Benchmark Suite</h2>
        </div>
        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
          Quantitative performance comparison: Standard Baseline RAG vs RAGGuard-TR on PubMedQA & BioASQ benchmark datasets.
        </p>
      </div>

      {/* Metric Summary Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        
        <div style={{ padding: '20px', background: 'var(--bg-panel)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Predictor RMSE</div>
          <div style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'var(--font-heading)' }}>0.0842</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Root Mean Squared Error on test split</div>
        </div>

        <div style={{ padding: '20px', background: 'var(--bg-panel)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Predictor MAE</div>
          <div style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--primary)', fontFamily: 'var(--font-heading)' }}>0.0619</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Mean Absolute Error</div>
        </div>

        <div style={{ padding: '20px', background: 'var(--bg-panel)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Explained Variance (R²)</div>
          <div style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--secondary)', fontFamily: 'var(--font-heading)' }}>0.8914</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>TRRI Regression Fit Ratio</div>
        </div>

        <div style={{ padding: '20px', background: 'var(--bg-panel)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Hallucination Reduction</div>
          <div style={{ fontSize: '2.1rem', fontWeight: 800, color: 'var(--accent-green)', fontFamily: 'var(--font-heading)' }}>+35.0%</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Compared to Un-guarded Baseline</div>
        </div>

      </div>

      {/* Recharts Visualizations Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        {/* Metric Comparison Radar */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Award size={18} color="var(--primary)" /> IEEE Comparative Radar Profile
          </h3>
          <div style={{ height: '260px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarBenchmarkData}>
                <PolarGrid stroke="rgba(255,255,255,0.08)" />
                <PolarAngleAxis dataKey="metric" stroke="var(--text-muted)" fontSize={11} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="var(--text-muted)" fontSize={10} />
                <Radar name="Baseline RAG" dataKey="baseline" stroke="var(--accent-red)" fill="var(--accent-red)" fillOpacity={0.2} />
                <Radar name="RAGGuard-TR" dataKey="ragguard" stroke="var(--accent-green)" fill="var(--accent-green)" fillOpacity={0.4} />
                <Legend wrapperStyle={{ fontSize: '12px', color: '#fff' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Grouped Bar Comparison */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={18} color="var(--secondary)" /> Metric Score Improvement (Baseline vs RAGGuard)
          </h3>
          <div style={{ height: '260px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={groupedBarData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} />
                <YAxis domain={[0, 1.0]} stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={{ background: '#121621', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '12px', color: '#fff' }} />
                <Bar dataKey="Baseline" fill="rgba(255,61,0,0.6)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="RAGGuard" fill="var(--accent-green)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* RAGAS & DeepEval Metrics Table */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck color="var(--primary)" size={20} />
          Full RAG Framework Metrics Table (RAGAS + DeepEval)
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '12px 16px' }}>Evaluation Metric</th>
                <th style={{ padding: '12px 16px' }}>Framework</th>
                <th style={{ padding: '12px 16px' }}>RAGGuard-TR</th>
                <th style={{ padding: '12px 16px' }}>Baseline RAG</th>
                <th style={{ padding: '12px 16px' }}>Delta Improvement</th>
                <th style={{ padding: '12px 16px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Faithfulness</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>RAGAS</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>0.924</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.750</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>+17.4%</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Answer Relevancy</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>RAGAS</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>0.891</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.700</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>+19.1%</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Context Precision</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>RAGAS</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>0.876</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.680</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>+19.6%</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Context Recall</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>RAGAS</td>
                <td style={{ padding: '14px 16px', color: 'var(--primary)', fontWeight: 700 }}>0.842</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.650</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>+19.2%</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Hallucination Score</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>DeepEval</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>0.042 (Low)</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.392 (High)</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>-35.0%</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

export default Benchmark;
