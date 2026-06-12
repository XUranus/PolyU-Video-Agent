import React from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '4rem 0',
      textAlign: 'center',
      color: 'white',
    }}>
      <div style={{maxWidth: '800px', margin: '0 auto', padding: '0 1rem'}}>
        <h1 style={{fontSize: '3rem', fontWeight: 700, marginBottom: '1rem'}}>
          🎓 {siteConfig.title}
        </h1>
        <p style={{fontSize: '1.3rem', opacity: 0.9, marginBottom: '2rem'}}>
          {siteConfig.tagline}
        </p>
        <p style={{fontSize: '1rem', opacity: 0.8, lineHeight: 1.8, maxWidth: '600px', margin: '0 auto 2rem'}}>
          上传一段课堂视频，LectureMind 自动完成语音转录、幻灯片识别、
          知识点提取、思维导图生成，并提供基于 RAG 的智能问答 Agent。
        </p>
        <Link
          to="/getting-started"
          style={{
            display: 'inline-block',
            padding: '0.8rem 2rem',
            backgroundColor: 'white',
            color: '#667eea',
            borderRadius: '8px',
            fontWeight: 600,
            fontSize: '1.1rem',
            textDecoration: 'none',
            transition: 'transform 0.2s',
          }}
        >
          开始阅读 →
        </Link>
      </div>
    </header>
  );
}

function FeatureCard({icon, title, description, link}: {icon: string; title: string; description: string; link: string}) {
  return (
    <Link to={link} style={{textDecoration: 'none', color: 'inherit'}}>
      <div style={{
        padding: '1.5rem',
        borderRadius: '12px',
        border: '1px solid #e5e7eb',
        backgroundColor: 'white',
        transition: 'all 0.3s ease',
        cursor: 'pointer',
        height: '100%',
      }}>
        <div style={{fontSize: '2rem', marginBottom: '0.8rem'}}>{icon}</div>
        <h3 style={{fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.5rem'}}>{title}</h3>
        <p style={{fontSize: '0.9rem', color: '#6b7280', lineHeight: 1.6, margin: 0}}>{description}</p>
      </div>
    </Link>
  );
}

function Features() {
  const features = [
    {icon: '🏗️', title: '架构概览', description: '了解系统的整体设计、数据流和技术栈选型。', link: '/architecture'},
    {icon: '⚙️', title: '后端开发', description: 'Django REST API、异步任务管线、数据模型详解。', link: '/backend/backend-overview'},
    {icon: '🤖', title: 'AI 核心模块', description: 'RAG 引擎、ReAct Agent、向量存储、LLM 客户端。', link: '/ai/ai-overview'},
    {icon: '🖥️', title: '前端开发', description: 'React 组件架构、SSE 流式聊天、实时交互。', link: '/frontend/frontend-overview'},
    {icon: '🐳', title: '部署指南', description: 'Docker Compose 部署、环境变量配置、生产环境优化。', link: '/deployment/docker-deployment'},
    {icon: '🧪', title: '开发指南', description: '添加新任务、扩展 Agent 工具、测试策略。', link: '/development/adding-tasks'},
  ];

  return (
    <section style={{maxWidth: '1000px', margin: '0 auto', padding: '3rem 1rem'}}>
      <h2 style={{textAlign: 'center', fontSize: '1.8rem', marginBottom: '2rem', color: '#1f2937'}}>
        文档导航
      </h2>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1.2rem',
      }}>
        {features.map((f, i) => <FeatureCard key={i} {...f} />)}
      </div>
    </section>
  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <HomepageHeader />
      <main>
        <Features />
      </main>
    </Layout>
  );
}
