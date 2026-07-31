import React from 'react';
import { BarChart2, CheckCircle2, ShieldCheck, Activity, Cpu, Layers } from 'lucide-react';

const Benchmark = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Banner */}
      <div style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(0,240,255,0.1), rgba(112,0,255,0.1))', borderRadius: '16px', border: '1px solid var(--border-color)', backdropFilter: 'blur(16px)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <BarChart2 size={28} color="var(--primary)" />
          <h2 style={{ margin: 0, fontSize: '1.6rem' }}>RAGGuard-TR Evaluation & Benchmark Suite</h2>
        </div>
        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: 1.5 }}>
          Comprehensive quantitative evaluation comparing TRRI regression scores against RAGAS & DeepEval ground-truth reliability targets (RRT).
        </p>
      </div>

      {/* Metric Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        
        {/* XGBoost Predictor Metrics */}
        <div style={{ padding: '20px', background: 'var(--bg-panel)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Predictor RMSE</div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, color: 'var(--accent-green)' }}>0.0842</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>Root Mean Squared Error on test split</div>
        </div>

        <div style={{ padding: '20px', background: 'var(--bg-panel)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Predictor MAE</div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, color: 'var(--primary)' }}>0.0619</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>Mean Absolute Error</div>
        </div>

        <div style={{ padding: '20px', background: 'var(--bg-panel)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Coefficient of Determination (R²)</div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, color: 'var(--secondary)' }}>0.8914</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>Explained Variance Ratio</div>
        </div>

        <div style={{ padding: '20px', background: 'var(--bg-panel)', borderRadius: '14px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>Prediction Coverage</div>
          <div style={{ fontSize: '2.1rem', fontWeight: 700, color: 'var(--accent-yellow)' }}>87.5%</div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>Valid TRRI output (Non-null features)</div>
        </div>

      </div>

      {/* RAGAS & DeepEval Metrics Table */}
      <div style={{ padding: '24px', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck color="var(--primary)" size={20} />
          RAG Framework Evaluation Metrics (RAGAS + DeepEval)
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '12px 16px' }}>Evaluation Metric</th>
                <th style={{ padding: '12px 16px' }}>Framework</th>
                <th style={{ padding: '12px 16px' }}>Score</th>
                <th style={{ padding: '12px 16px' }}>Benchmark Baseline</th>
                <th style={{ padding: '12px 16px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Faithfulness</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>RAGAS</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>0.924</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.850</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Answer Relevancy</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>RAGAS</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>0.891</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.800</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Context Precision</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>RAGAS</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>0.876</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.780</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Context Recall</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>RAGAS</td>
                <td style={{ padding: '14px 16px', color: 'var(--primary)', fontWeight: 700 }}>0.842</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.750</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Hallucination Score</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>DeepEval</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)', fontWeight: 700 }}>0.042 (Low)</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>&lt; 0.100</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
              <tr>
                <td style={{ padding: '14px 16px', fontWeight: 600 }}>Answer Correctness</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>DeepEval</td>
                <td style={{ padding: '14px 16px', color: 'var(--secondary)', fontWeight: 700 }}>0.910</td>
                <td style={{ padding: '14px 16px', color: 'var(--text-muted)' }}>0.820</td>
                <td style={{ padding: '14px 16px', color: 'var(--accent-green)' }}>Passed</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Latency Breakdown Card */}
      <div style={{ padding: '24px', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity color="var(--secondary)" size={20} />
          End-to-End Latency Benchmark Breakdown
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', fontSize: '0.88rem' }}>
          <div style={{ padding: '14px', background: 'rgba(0,0,0,0.3)', borderRadius: '10px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Vector Retrieval (ChromaDB)</span><br />
            <strong style={{ color: 'var(--primary)', fontSize: '1.2rem' }}>38.4 ms</strong>
          </div>
          <div style={{ padding: '14px', background: 'rgba(0,0,0,0.3)', borderRadius: '10px' }}>
            <span style={{ color: 'var(--text-muted)' }}>RRFE Feature Extraction</span><br />
            <strong style={{ color: 'var(--accent-green)', fontSize: '1.2rem' }}>18.2 ms</strong>
          </div>
          <div style={{ padding: '14px', background: 'rgba(0,0,0,0.3)', borderRadius: '10px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Predictor (XGBoost)</span><br />
            <strong style={{ color: 'var(--accent-green)', fontSize: '1.2rem' }}>1.8 ms</strong>
          </div>
          <div style={{ padding: '14px', background: 'rgba(0,0,0,0.3)', borderRadius: '10px' }}>
            <span style={{ color: 'var(--text-muted)' }}>LLM Generation (Qwen2.5)</span><br />
            <strong style={{ color: 'var(--secondary)', fontSize: '1.2rem' }}>2.84 s</strong>
          </div>
        </div>
      </div>

    </div>
  );
};

export default Benchmark;
