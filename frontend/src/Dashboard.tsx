// src/App.tsx
import React, { useState, useRef } from 'react';
import { Layout, Menu, Button, Progress, Spin, Upload, message } from 'antd';
import { 
  HomeOutlined, 
  VideoCameraOutlined, 
  SearchOutlined, 
  SettingOutlined,
  UploadOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  LoadingOutlined
} from '@ant-design/icons';
import { RcFile, UploadProps } from 'antd/es/upload';

import { v4 as uuidv4 } from 'uuid'; // Optional: better UID than Date.now()

const { Header, Sider, Content } = Layout;


import type { MenuProps } from 'antd';

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
  const [collapsed, setCollapsed] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadedVideo, setUploadedVideo] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<{id: number; text: string; sender: 'user' | 'agent'}[]>([]);
  const [inputValue, setInputValue] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);


  // Or if you don't want to add uuid, use Date.now()
  const createRcFile = (file: File): RcFile => {
    let rcFile = file as RcFile;
    rcFile.uid = uuidv4 ? uuidv4() : `file-${Date.now()}`;
    //rcFile.lastModifiedDate = file.lastModified ? new Date(file.lastModified) : new Date();
    return rcFile;
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const file = e.target.files[0];
      if (file.type.startsWith('video/')) {
        const rcFile = createRcFile(file);
        startUpload(rcFile);
      } else {
        message.error('Please upload a video file');
      }
    }
  };


  const startUpload = (file: RcFile) => {
    setIsUploading(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            finishUpload(file);
          }, 500);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const finishUpload = (file: RcFile) => {
    setIsUploading(false);
    setUploadedVideo(URL.createObjectURL(file));
    setIsProcessing(true);
    
    // Simulate processing time
    setTimeout(() => {
      setIsProcessing(false);
      addAgentMessage("Hello! I've analyzed your video. How can I help you today?");
    }, 3000);
  };

  const addAgentMessage = (text: string) => {
    setChatMessages(prev => [
      ...prev,
      { id: Date.now(), text, sender: 'agent' }
    ]);
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
    // Add user message
    setChatMessages(prev => [
      ...prev,
      { id: Date.now(), text: inputValue, sender: 'user' }
    ]);
    
    // Clear input
    setInputValue('');
    
    // Simulate agent response after delay
    setTimeout(() => {
      addAgentMessage(`I received your query: "${inputValue}". Here's what I found...`);
    }, 1000);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files?.[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('video/')) {
        const rcFile = createRcFile(file);
        startUpload(rcFile);
      } else {
        message.error('Please upload a video file');
      }
    }
  };

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
          width={240} 
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
          {!uploadedVideo ? (
            // Upload Page
            <div className="flex flex-col items-center justify-center h-full">
              <div 
                className="w-full max-w-3xl border-2 border-dashed border-blue-400 rounded-2xl p-10 text-center bg-white shadow-lg transition-all hover:shadow-xl"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                <div className="flex flex-col items-center justify-center">
                  <div className="bg-blue-100 p-4 rounded-full mb-6">
                    <VideoCameraOutlined className="text-blue-600 text-3xl" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-800 mb-2">Upload Your Video</h2>
                  <p className="text-gray-600 mb-6">Drag & drop your video here or click the button below</p>
                  
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileChange} 
                    accept="video/*" 
                    className="hidden" 
                  />
                  
                  <Button 
                    type="primary" 
                    size="large" 
                    icon={<UploadOutlined />} 
                    onClick={handleUploadClick}
                    className="mb-6"
                  >
                    Select Video File
                  </Button>
                  
                  <p className="text-gray-500 text-sm">Supported formats: MP4, MOV, AVI, MKV</p>
                </div>
              </div>
              
              <div className="mt-8 w-full max-w-3xl">
                <div className="bg-white rounded-xl shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">Ask Questions About Your Video</h3>
                  <div className="flex">
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder="Type your question here..."
                      className="flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={!uploadedVideo}
                    />
                    <Button 
                      type="primary" 
                      onClick={handleSendMessage}
                      disabled={!uploadedVideo || !inputValue.trim()}
                      className="rounded-r-lg"
                    >
                      Send
                    </Button>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                  <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-5 rounded-xl shadow">
                    <h4 className="font-medium text-gray-800 mb-2">Event Query</h4>
                    <p className="text-gray-600 text-sm">"When did Person X appear in the surveillance footage?"</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-5 rounded-xl shadow">
                    <h4 className="font-medium text-gray-800 mb-2">Thematic Segmentation</h4>
                    <p className="text-gray-600 text-sm">Segment educational videos into thematic units and summarize key concepts</p>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-teal-50 p-5 rounded-xl shadow">
                    <h4 className="font-medium text-gray-800 mb-2">Knowledge Point Location</h4>
                    <p className="text-gray-600 text-sm">Locate precise video segments corresponding to user-specified knowledge points</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Video Analysis Page
            <div className="flex flex-col h-full">
              <div className="flex flex-col md:flex-row gap-6 h-full">
                {/* Video Section */}
                <div className="md:w-1/2 bg-black rounded-xl overflow-hidden shadow-xl">
                  {isProcessing ? (
                    <div className="flex items-center justify-center h-full">
                      <Spin 
                        size="large" 
                        tip="Processing your video..." 
                        indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />}
                      />
                    </div>
                  ) : (
                    <video 
                      src={uploadedVideo} 
                      controls 
                      className="w-full h-full object-contain"
                    />
                  )}
                </div>
                
                {/* Chat Section */}
                <div className="md:w-1/2 flex flex-col bg-white rounded-xl shadow-xl overflow-hidden">
                  <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
                    <div className="space-y-4">
                      {chatMessages.map((msg) => (
                        <div 
                          key={msg.id} 
                          className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div 
                            className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                              msg.sender === 'user' 
                                ? 'bg-blue-500 text-white rounded-tr-none' 
                                : 'bg-gray-200 text-gray-800 rounded-tl-none'
                            }`}
                          >
                            {msg.text}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Input Area */}
                  <div className="p-4 border-t border-gray-200 bg-white">
                    <div className="flex">
                      <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="Ask about the video..."
                        className="flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                      />
                      <Button 
                        type="primary" 
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim()}
                        className="rounded-r-lg"
                      >
                        Send
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Features Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-5 rounded-xl shadow">
                  <h4 className="font-medium text-gray-800 mb-2">Video Type Recognition</h4>
                  <p className="text-gray-600 text-sm">Automatically identifies video types (surveillance, lectures, etc.)</p>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-5 rounded-xl shadow">
                  <h4 className="font-medium text-gray-800 mb-2">Contextual Analysis</h4>
                  <p className="text-gray-600 text-sm">Understands context within the video for accurate responses</p>
                </div>
                <div className="bg-gradient-to-br from-green-50 to-teal-50 p-5 rounded-xl shadow">
                  <h4 className="font-medium text-gray-800 mb-2">Multimodal Processing</h4>
                  <p className="text-gray-600 text-sm">Handles video, audio, and text data simultaneously</p>
                </div>
              </div>
            </div>
          )}
        </Content>
      </Layout>
    </Layout>
  );
};

export default Dashboard;