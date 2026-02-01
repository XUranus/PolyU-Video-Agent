// src/App.tsx
import React, { useState, useRef } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';    

import { Layout, Menu, Button, Progress } from 'antd';
import { 
  HomeOutlined, 
  VideoCameraOutlined, 
  SearchOutlined, 
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';

import type { MenuProps } from 'antd';

import UploadVideo from './components/UploadVideo';
import LectureVideoAnalysis from './components/LectureVideoAnalysis';
import PlayGround from './components/PlayGround';

const { Header, Sider, Content } = Layout;

const menuItems: MenuProps['items'] = [
  {
    key: '1',
    icon: <HomeOutlined />,
    label: 'Home',
  },
  {
    key: '2',
    icon: <VideoCameraOutlined />,
    label: 'Video Analysis',
  },
  {
    key: '3',
    icon: <SearchOutlined />,
    label: 'Search',
  },
  {
    key: '4',
    icon: <SettingOutlined />,
    label: 'Settings',
  },
];

const Dashboard: React.FC = () => {
  const [collapsed, setCollapsed] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);


  const [isUploading, setIsUploading] = useState(false);
  const [uploadedVideo, setUploadedVideo] = useState<string | null>(null);
 
  


  return (
    <Layout className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <Header className="bg-white shadow-md flex items-center justify-between px-4 py-2">
        <div className="flex items-center">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            className="text-gray-700 hover:text-blue-600"
          />
          <h1 className="ml-4 text-xl font-bold text-gray-800">PolyU Video Agent</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          {isUploading && (
            <div className="w-40">
              <Progress percent={uploadProgress} size="small" />
            </div>
          )}
          <div className="relative">
            <span className="absolute -top-2 -right-2 flex h-4 w-4">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-4 w-4 bg-red-500"></span>
            </span>
            <Button>Notifications</Button>
          </div>
          <Button>Profile</Button>
        </div>
      </Header>

      <Layout>
        {/* Left Sidebar */}
        <Sider 
          width={200} 
          collapsed={collapsed}
          collapsible
          trigger={null}
          className="bg-white shadow-md"
        >
          <Menu
            mode="inline"
            defaultSelectedKeys={['1']}
            items={menuItems}
            className="border-r-0"
          />
        </Sider>

        {/* Main Content */}
        <Content className="p-6">
          <BrowserRouter>
            <Routes>
              <Route 
                path="/"
                element={<UploadVideo setUploadProgress={setUploadProgress}/>} />
              <Route 
                path="/lecture/:videoId"
                element={<LectureVideoAnalysis/>} />
              <Route 
                path="/play"
                element={<PlayGround videoId="113514"/>} />
              {/* You can add more routes here */}
            </Routes>
          </BrowserRouter>
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;