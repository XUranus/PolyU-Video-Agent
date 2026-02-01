
// src/App.tsx
import React, { useState, useRef, Dispatch, SetStateAction } from 'react';
import { Button, message } from 'antd';
import {
  VideoCameraOutlined, 
  UploadOutlined,
} from '@ant-design/icons';
import { RcFile, UploadProps } from 'antd/es/upload';

import { v4 as uuidv4 } from 'uuid'; // Optional: better UID than Date.now()



interface UploadVideoProps {
  setUploadProgress: Dispatch<SetStateAction<number>>
}

const UploadVideo: React.FC<UploadVideoProps> = ({ setUploadProgress }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const finishUpload = (file: RcFile) => {
    setIsUploading(false);
    //setUploadedVideo(URL.createObjectURL(file));
    setIsProcessing(true);
    
    // Simulate processing time
    setTimeout(() => {
      setIsProcessing(false);
      //addAgentMessage("Hello! I've analyzed your video. How can I help you today?");
    }, 3000);
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
    
  // Upload Page
  return (
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
          />
          <Button 
            type="primary" 
            //onClick={handleSendMessage}
            disabled={!inputValue.trim()}
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
  </div>);
}

export default UploadVideo;