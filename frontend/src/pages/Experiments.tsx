import { Layers, Database } from 'lucide-react';


interface ExperimentRun {
  id: string;
  dataset: string;
  modelVersion: string;
  embeddingModel: string;
  llm: string;
  avgTRRI: string;
  rmse: string;
  latency: string;
  coverage: string;
  date: string;
  status: string;
}

const EXPERIMENTS: ExperimentRun[] = [
  {
    id: 'EXP-2026-004 (V1.0 Production)',
    dataset: 'Academic RAG Corpus (PDFs + arXiv)',
    modelVersion: 'v1.0.0-xgboost',
    embeddingModel: 'nomic-embed-text',
    llm: 'qwen2.5:latest',
    avgTRRI: '86.4%',
    rmse: '0.0842',
    latency: '58.4 ms',
    coverage: '87.5%',
    date: '2026-07-31',
    status: 'Completed',
  },
  {
    id: 'EXP-2026-003 (Hierarchical Resolver)',
    dataset: 'Academic PDFs (Raw Metadata)',
    modelVersion: 'v0.9.4-xgboost',
    embeddingModel: 'nomic-embed-text',
    llm: 'qwen2.5:latest',
    avgTRRI: '84.1%',
    rmse: '0.0890',
    latency: '62.1 ms',
    coverage: '85.0%',
    date: '2026-07-30',
    status: 'Completed',
  },
  {
    id: 'EXP-2026-002 (Base Baseline)',
    dataset: 'RAGAS Synthetic QA Set',
    modelVersion: 'v0.8.0-xgboost',
    embeddingModel: 'all-MiniLM-L6-v2',
    llm: 'llama3:8b',
    avgTRRI: '78.2%',
    rmse: '0.1120',
    latency: '142.5 ms',
    coverage: '60.0%',
    date: '2026-07-28',
    status: 'Completed',
  },
];

const Experiments = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Banner */}
      <div style={{ padding: '24px', background: 'linear-gradient(135deg, rgba(112,0,255,0.1), rgba(0,240,255,0.1))', borderRadius: '16px', border: '1px solid var(--border-color)', backdropFilter: 'blur(16px)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <Layers size={28} color="var(--secondary)" />
          <h2 style={{ margin: 0, fontSize: '1.6rem' }}>Research Experiments & Version Comparison</h2>
        </div>
        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: 1.5 }}>
          Comparative audit of RAGGuard-TR model iterations, dataset versions, embedding backends, and prediction coverage metrics.
        </p>
      </div>

      {/* Experiments Table */}
      <div style={{ padding: '24px', background: 'var(--bg-panel)', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Database color="var(--primary)" size={20} />
          Registered Experiment Runs
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.86rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '12px 14px' }}>Experiment ID</th>
                <th style={{ padding: '12px 14px' }}>Dataset</th>
                <th style={{ padding: '12px 14px' }}>Model</th>
                <th style={{ padding: '12px 14px' }}>Embedding</th>
                <th style={{ padding: '12px 14px' }}>LLM</th>
                <th style={{ padding: '12px 14px' }}>Avg TRRI</th>
                <th style={{ padding: '12px 14px' }}>RMSE</th>
                <th style={{ padding: '12px 14px' }}>Overhead Latency</th>
                <th style={{ padding: '12px 14px' }}>Coverage</th>
              </tr>
            </thead>
            <tbody>
              {EXPERIMENTS.map((exp) => (
                <tr key={exp.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '14px', fontWeight: 600, color: 'var(--primary)' }}>{exp.id}</td>
                  <td style={{ padding: '14px', color: 'var(--text-main)' }}>{exp.dataset}</td>
                  <td style={{ padding: '14px', color: 'var(--text-muted)' }}>{exp.modelVersion}</td>
                  <td style={{ padding: '14px', color: 'var(--text-muted)' }}>{exp.embeddingModel}</td>
                  <td style={{ padding: '14px', color: 'var(--text-muted)' }}>{exp.llm}</td>
                  <td style={{ padding: '14px', color: 'var(--accent-green)', fontWeight: 700 }}>{exp.avgTRRI}</td>
                  <td style={{ padding: '14px', color: 'var(--secondary)' }}>{exp.rmse}</td>
                  <td style={{ padding: '14px', color: 'var(--accent-green)' }}>{exp.latency}</td>
                  <td style={{ padding: '14px', color: 'var(--accent-yellow)', fontWeight: 600 }}>{exp.coverage}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};

export default Experiments;
